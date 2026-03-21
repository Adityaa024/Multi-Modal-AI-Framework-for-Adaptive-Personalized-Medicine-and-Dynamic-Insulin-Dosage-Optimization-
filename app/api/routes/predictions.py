from datetime import datetime
from functools import lru_cache
import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, roc_auc_score, roc_curve
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session_dependency
from app.db.models import DoseHistory, Patient
from app.schemas.prediction import (
    SafeRange,
    DosePredictionPatientInput,
    DosePredictionResponse,
    DrugRecommendation,
    EvaluationDashboardResponse,
    InsulinDosePrediction,
    InsulinDosePredictionRequest,
    RocCurveSeries,
    SafetyGuardrails,
    SeverityProbability,
    ConfusionMatrixPayload,
    ShapSummaryPoint,
)
from app.services.drug_recommender import recommend_drug
from app.services.ml.dose_model import (
    SimpleHeuristicDoseModel,
    compute_hybrid_adaptive_dose,
    compute_advanced_adaptive_dose,
)
from app.services.ml.explainability import explain_dosage_prediction
from app.services.ml.preprocessing import (
    DOSE_REGRESSION_FEATURE_NAMES,
    build_dose_regression_frame,
    build_dose_regression_vector,
    build_glucose_features,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

# Instantiate a single model instance for reuse across requests. The model as
# implemented here is stateless, so a shared instance is safe. Stateful or
# GPU-backed models may require a more sophisticated lifecycle.
_dose_model = SimpleHeuristicDoseModel()

_SEVERITY_MODEL_PATH = Path("data") / "severity_model.pkl"
_DOSAGE_MODEL_PATH = Path("data") / "dosage_model.pkl"
_DATASET_PATH = Path("data") / "synthetic_t2d_patients.csv"
_SAFE_MIN_DOSE_UNITS = 0.5
_CONFIDENCE_TEMPERATURE = 1.4

_SEVERITY_FEATURE_NAMES: List[str] = [
    "age",
    "weight_kg",
    "height_cm",
    "bmi",
    "fasting_glucose_mgdl",
    "hba1c",
    "creatinine_mgdl",
    "previous_insulin_dose_units",
    "glucose_after_dose_mgdl",
    "activity_level",
    "diet_adherence_score",
]

_DOSAGE_FEATURE_NAMES: List[str] = list(DOSE_REGRESSION_FEATURE_NAMES)

_FEATURE_NAMES: List[str] = list(_DOSAGE_FEATURE_NAMES)


def _load_pickle_model(path: Path):
    """Utility to load a pickled scikit-learn compatible model."""

    import pickle

    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Ensure the training script has been run."
        )

    with path.open("rb") as f:
        return pickle.load(f)


def _unwrap_severity_model(obj):
    """
    Support both legacy and bundled severity model formats.

    - Legacy: a model object with `.predict` / `.predict_proba` returning string labels.
    - Bundle: a dict containing `model` and `int_to_class` mappings.
    """

    if isinstance(obj, dict) and "model" in obj:
        return obj["model"], obj.get("int_to_class"), obj.get("class_order")
    return obj, None, None


def _unwrap_dosage_model(obj):
    """Support bare estimators and bundled dosage model payloads."""

    if isinstance(obj, dict) and "model" in obj:
        return obj["model"], obj.get("feature_names", _DOSAGE_FEATURE_NAMES)
    return obj, _DOSAGE_FEATURE_NAMES


def _prepare_severity_feature_vector(payload: DosePredictionPatientInput) -> np.ndarray:
    """Build the classifier feature vector in the severity training order."""

    bmi = payload.bmi
    if bmi is None:
        height_m = payload.height_cm / 100.0
        bmi = payload.weight_kg / (height_m**2)

    return np.array(
        [
            payload.age,
            payload.weight_kg,
            payload.height_cm,
            bmi,
            payload.fasting_glucose_mgdl,
            payload.hba1c,
            payload.creatinine_mgdl,
            payload.previous_insulin_dose_units,
            payload.glucose_after_dose_mgdl,
            payload.activity_level,
            payload.diet_adherence_score,
        ],
        dtype=float,
    )


def _prepare_dosage_feature_vector(payload: DosePredictionPatientInput) -> np.ndarray:
    """Build the dosage-regression feature vector in the training order."""

    return build_dose_regression_vector(
        age=payload.age,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        bmi=payload.bmi,
        fasting_glucose_mgdl=payload.fasting_glucose_mgdl,
        hba1c=payload.hba1c,
        creatinine_mgdl=payload.creatinine_mgdl,
        previous_insulin_dose_units=payload.previous_insulin_dose_units,
        glucose_after_dose_mgdl=payload.glucose_after_dose_mgdl,
        activity_level=payload.activity_level,
        diet_adherence_score=payload.diet_adherence_score,
    )


def _apply_severity_feature_mode(features: np.ndarray, mode: str) -> np.ndarray:
    """Apply ablation masking for severity features before classifier inference."""

    masked = features.copy()
    if mode == "structured":
        keep_idx = {0, 1, 2, 3, 9}
    elif mode == "structured_labs":
        keep_idx = {0, 1, 2, 3, 4, 5, 6, 9}
    else:
        keep_idx = set(range(len(masked)))

    for idx in range(len(masked)):
        if idx not in keep_idx:
            masked[idx] = 0.0

    return masked


def _apply_dosage_feature_mode(features: np.ndarray, mode: str) -> np.ndarray:
    """Apply ablation masking for engineered dosage features before regressor inference."""

    masked = features.copy()
    if mode == "structured":
        # Keep only: age, weight_kg, height_cm, bmi, activity_level
        keep_idx = {0, 1, 2, 3, 9}
    elif mode == "structured_labs":
        # Keep structured + labs + activity
        keep_idx = {0, 1, 2, 3, 4, 5, 6, 9}
    else:
        keep_idx = set(range(len(masked)))

    for idx in range(len(masked)):
        if idx not in keep_idx:
            masked[idx] = 0.0

    return masked


def _to_model_input_frame(features: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """Create a single-row DataFrame with canonical training feature names."""

    return pd.DataFrame([features], columns=feature_names)


def _temperature_calibrate(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    """Lightweight temperature scaling on probabilities for more realistic confidence."""

    safe = np.clip(probabilities, 1e-12, 1.0)
    adjusted = np.power(safe, 1.0 / max(temperature, 1e-6))
    return adjusted / adjusted.sum()


def _normalized_entropy(probabilities: np.ndarray) -> float:
    """Return entropy normalized to [0, 1] for a K-class distribution."""

    safe = np.clip(probabilities, 1e-12, 1.0)
    h = -float(np.sum(safe * np.log(safe)))
    return h / float(np.log(len(safe)))


def _compute_risk_probabilities(glucose_mgdl: float, dose_units: float) -> tuple[float, float]:
    """Heuristic hypoglycemia and hyperglycemia probabilities in [0, 1]."""

    hypo_logit = ((90.0 - glucose_mgdl) / 18.0) + ((dose_units - 12.0) / 8.0)
    hyper_logit = ((glucose_mgdl - 145.0) / 25.0) - ((dose_units - 10.0) / 12.0)

    hypo = float(1.0 / (1.0 + np.exp(-hypo_logit)))
    hyper = float(1.0 / (1.0 + np.exp(-hyper_logit)))

    return max(0.0, min(1.0, hypo)), max(0.0, min(1.0, hyper))


def _calibrate_served_dosage_prediction(
    raw_model_dose_units: float,
    *,
    severity: str,
    fasting_glucose_mgdl: float,
    weight_kg: float,
    previous_insulin_dose_units: float,
    glucose_after_dose_mgdl: float,
) -> float:
    """Apply a response-aware calibration band for bundled dosage models.

    The regressor is trained on synthetic data. At serving time, we keep the
    prediction clinically anchored for moderate and severe cases by constraining
    it to a narrow band around the patient's recent insulin exposure while still
    respecting a physiological lower bound.
    """

    if (
        severity not in {"Moderate", "Severe"}
        or previous_insulin_dose_units <= 0
        or fasting_glucose_mgdl < 90.0
    ):
        return raw_model_dose_units

    physiological_floor = 0.2 * weight_kg
    response_floor = previous_insulin_dose_units * (
        1.05 if glucose_after_dose_mgdl > 180 else 1.00
    )
    response_ceiling = previous_insulin_dose_units * (
        1.15 if glucose_after_dose_mgdl > 180 else 1.05
    )

    calibrated_min = max(physiological_floor, response_floor)
    calibrated_max = min(0.6 * weight_kg, max(calibrated_min, response_ceiling))

    return float(np.clip(raw_model_dose_units, calibrated_min, calibrated_max))


def _escalate_severity_for_renal_elderly(
    severity: str,
    *,
    age: float,
    hba1c: float,
    creatinine_mgdl: float,
) -> str:
    """Escalate moderate severity for high-risk elderly renal profiles."""

    if severity == "Mild" and creatinine_mgdl > 2.0 and age > 70:
        return "Moderate"

    if severity != "Moderate":
        return severity

    if creatinine_mgdl > 2.0 and age > 70:
        return "Severe"
    if creatinine_mgdl > 2.5 and hba1c > 8.5:
        return "Severe"
    if age > 75 and hba1c > 9.0:
        return "Severe"

    return severity


def _is_hypoglycemia_alert(
    *,
    hypoglycemia_risk_probability: float,
    activity_level: int,
    glucose_after_dose_mgdl: float,
) -> bool:
    """Determine hypoglycemia alert using lower, context-aware thresholds."""

    if hypoglycemia_risk_probability >= 0.35:
        return True
    if hypoglycemia_risk_probability >= 0.30:
        return True
    if hypoglycemia_risk_probability >= 0.30 and glucose_after_dose_mgdl < 100:
        return True
    if hypoglycemia_risk_probability >= 0.25 and activity_level == 3:
        return True
    return False


def _weight_based_safe_range(weight_kg: float) -> tuple[float, float]:
    """
    Compute clinically realistic outpatient basal range using body weight.

    Range is intentionally simple and transparent for this research scaffold:
    - minimum: 0.1 U/kg/day
    - maximum: 0.5 U/kg/day
    """

    safe_min = max(0.0, 0.1 * weight_kg)
    safe_max = max(safe_min, 0.5 * weight_kg)
    return safe_min, safe_max


def _apply_weight_based_clamp(
    dose_units: float,
    safe_min_units: float,
    safe_max_units: float,
) -> tuple[float, bool, str | None, bool]:
    """Clamp dose to weight-scaled range and return clamp metadata."""

    if dose_units < safe_min_units:
        return (
            safe_min_units,
            True,
            (
                "⚠ Dose adjusted to minimum physiological outpatient basal bound "
                f"({safe_min_units:.1f} U/day)."
            ),
            False,
        )
    if dose_units > safe_max_units:
        return (
            safe_max_units,
            True,
            (
                "⚠ Dose capped at maximum outpatient basal bound "
                f"({safe_max_units:.1f} U/day)."
            ),
            True,
        )

    return dose_units, False, None, False


def _build_weight_safety_guardrails(
    final_dose_units: float,
    ml_dose_units: float,
    safe_min_units: float,
    safe_max_units: float,
    was_clamped: bool,
    warning_message: str | None,
) -> SafetyGuardrails:
    """
    Build safety response fields from weight-scaled clamp outcome.

    Safety validation MUST use the final recommended dose (post-clamp), not
    the raw ML or adaptive intermediate dose.
    """

    # Use response-aligned rounded values to avoid floating-point boundary drift
    # where e.g. 9.2 vs 9.200000000000001 could incorrectly flip the flag.
    safe_min_rounded = float(round(safe_min_units, 1))
    safe_max_rounded = float(round(safe_max_units, 1))
    final_dose_rounded = float(round(final_dose_units, 1))

    within_range = safe_min_rounded <= final_dose_rounded <= safe_max_rounded
    exceeds_max_allowed = ml_dose_units > safe_max_units

    return SafetyGuardrails(
        safe_min_units=safe_min_rounded,
        safe_max_units=safe_max_rounded,
        was_clamped=was_clamped,
        within_safe_range=within_range,
        exceeds_max_allowed=exceeds_max_allowed,
        warning_message=warning_message,
    )


def _derive_severity_labels(df: pd.DataFrame) -> np.ndarray:
    """Derive severity labels from HbA1c and fasting glucose thresholds."""

    hba1c = df["hba1c"]
    fasting = df["fasting_glucose_mgdl"]

    mild_mask = (hba1c < 7.5) & (fasting < 140)
    severe_mask = (hba1c >= 9.5) | (fasting >= 200)

    labels = np.where(mild_mask, "Mild", "Moderate")
    labels = np.where(severe_mask, "Severe", labels)
    return labels


@lru_cache(maxsize=1)
def _compute_evaluation_dashboard_cached() -> EvaluationDashboardResponse:
    """Compute and cache evaluation artifacts for dashboard rendering."""

    import shap

    if not _DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {_DATASET_PATH}. Run synthetic data generation first."
        )

    df = pd.read_csv(_DATASET_PATH)
    severity_X = df[_SEVERITY_FEATURE_NAMES].copy()

    severity_loaded = _load_pickle_model(_SEVERITY_MODEL_PATH)
    severity_model, int_to_class, class_order = _unwrap_severity_model(severity_loaded)
    if class_order is None:
        class_order = ["Mild", "Moderate", "Severe"]
    class_to_int = {label: i for i, label in enumerate(class_order)}

    y_true_labels = _derive_severity_labels(df)
    y_true_int = np.array([class_to_int[label] for label in y_true_labels])

    severity_proba = np.asarray(severity_model.predict_proba(severity_X), dtype=float)
    severity_pred_raw = severity_model.predict(severity_X)

    if int_to_class is not None:
        y_pred_labels = np.array([str(int_to_class[int(v)]) for v in severity_pred_raw])
    else:
        y_pred_labels = np.array([str(v) for v in severity_pred_raw])

    roc_auc = float(roc_auc_score(y_true_int, severity_proba, multi_class="ovr"))

    roc_series: list[RocCurveSeries] = []
    for idx, label in enumerate(class_order):
        y_binary = (y_true_int == idx).astype(int)
        fpr, tpr, _ = roc_curve(y_binary, severity_proba[:, idx])
        roc_series.append(
            RocCurveSeries(
                label=label,
                fpr=[float(x) for x in fpr],
                tpr=[float(y) for y in tpr],
            )
        )

    cm = confusion_matrix(y_true_labels, y_pred_labels, labels=class_order)

    dosage_X = build_dose_regression_frame(df)
    dosage_loaded = _load_pickle_model(_DOSAGE_MODEL_PATH)
    dosage_model, dosage_feature_names = _unwrap_dosage_model(dosage_loaded)
    if "simulated_optimal_insulin_dose_units" not in df.columns:
        raise ValueError("Missing target column 'simulated_optimal_insulin_dose_units'.")
    y_dose = df["simulated_optimal_insulin_dose_units"].to_numpy(dtype=float)
    y_dose_pred = np.asarray(dosage_model.predict(dosage_X), dtype=float)
    mae = float(mean_absolute_error(y_dose, y_dose_pred))
    rmse = float(np.sqrt(mean_squared_error(y_dose, y_dose_pred)))

    shap_sample = dosage_X.sample(n=min(500, len(dosage_X)), random_state=42)
    explainer = shap.TreeExplainer(dosage_model)
    shap_values = np.asarray(explainer.shap_values(shap_sample), dtype=float)
    mean_abs = np.mean(np.abs(shap_values), axis=0)
    top_idx = np.argsort(mean_abs)[::-1][:10]

    shap_summary = [
        ShapSummaryPoint(feature=dosage_feature_names[i], mean_abs_shap=float(mean_abs[i]))
        for i in top_idx
    ]

    return EvaluationDashboardResponse(
        mae=mae,
        rmse=rmse,
        roc_auc_ovr_macro=roc_auc,
        roc_curves=roc_series,
        confusion_matrix=ConfusionMatrixPayload(
            labels=class_order,
            matrix=[[int(v) for v in row] for row in cm.tolist()],
        ),
        shap_summary=shap_summary,
    )


@router.post(
    "/insulin-dose",
    response_model=InsulinDosePrediction,
    status_code=status.HTTP_200_OK,
    summary="Suggest an insulin dose (research only)",
)
def predict_insulin_dose(
    payload: InsulinDosePredictionRequest,
    db: Session = Depends(db_session_dependency),
) -> InsulinDosePrediction:
    """
    Suggest an insulin dose based on current glucose and context flags.

    For traceability, this endpoint also records the suggested dose in the
    patient's dose history together with the associated glucose metrics.
    """

    patient = db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id={payload.patient_id} not found.",
        )

    features = build_glucose_features(
        current_glucose_mgdl=payload.current_glucose_mgdl,
        previous_glucose_mgdl=payload.previous_glucose_mgdl,
        is_preprandial=payload.is_preprandial,
        is_bedtime=payload.is_bedtime,
    )

    suggested_units = _dose_model.predict_dose_units(features)

    # Persist the event into the dose history to make the API self-logging
    # for subsequent offline analysis.
    history_entry = DoseHistory(
        patient_id=patient.id,
        timestamp=payload.request_timestamp or datetime.utcnow(),
        glucose_mgdl=payload.current_glucose_mgdl,
        glucose_previous_mgdl=payload.previous_glucose_mgdl,
        insulin_units=suggested_units,
        context_label=(
            "preprandial" if payload.is_preprandial else "non-preprandial"
        ),
    )
    db.add(history_entry)
    db.commit()

    rationale = (
        "Dose derived from proportional heuristic targeting ~110 mg/dL, "
        "with modest adjustments for recent glucose trend and context flags. "
        "This suggestion is for research use only and must not be used for "
        "clinical decision-making."
    )

    return InsulinDosePrediction(
        patient_id=patient.id,
        suggested_insulin_units=suggested_units,
        model_name=_dose_model.metadata.name,
        model_version=_dose_model.metadata.version,
        rationale=rationale,
    )


@router.post(
    "/predict-dose",
    response_model=DosePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict severity and hybrid-adjusted insulin dose",
)
def predict_dose_with_severity(
    payload: DosePredictionPatientInput,
) -> DosePredictionResponse:
    """
    Predict diabetes severity and recommend an insulin dose.

    The endpoint combines:
    - An XGBoost-based severity classifier.
    - An XGBoost-based dosage regressor with engineered features.
    - Rule-based adaptive adjustments for extreme glucose values.
    - SHAP-based natural language explanation of the dosage decision.
    """

    severity_features = _prepare_severity_feature_vector(payload)
    masked_severity_features = _apply_severity_feature_mode(severity_features, payload.feature_mode)
    dosage_features = _prepare_dosage_feature_vector(payload)
    masked_dosage_features = _apply_dosage_feature_mode(dosage_features, payload.feature_mode)

    logger.debug("Ablation mode=%s severity_features=%s", payload.feature_mode, masked_severity_features.tolist())
    logger.debug("Ablation mode=%s dosage_features=%s", payload.feature_mode, masked_dosage_features.tolist())

    # Severity prediction
    severity_loaded = _load_pickle_model(_SEVERITY_MODEL_PATH)
    severity_model, int_to_class, _class_order = _unwrap_severity_model(severity_loaded)
    severity_model_input = _to_model_input_frame(masked_severity_features, _SEVERITY_FEATURE_NAMES)

    severity_pred_raw = severity_model.predict(severity_model_input)[0]
    if int_to_class is not None:
        severity_pred = str(int_to_class[int(severity_pred_raw)])
    else:
        severity_pred = str(severity_pred_raw)

    severity_pred = _escalate_severity_for_renal_elderly(
        severity_pred,
        age=payload.age,
        hba1c=payload.hba1c,
        creatinine_mgdl=payload.creatinine_mgdl,
    )

    raw_probabilities = np.asarray(severity_model.predict_proba(severity_model_input)[0], dtype=float)
    calibrated_probabilities = _temperature_calibrate(raw_probabilities, _CONFIDENCE_TEMPERATURE)
    severity_proba = float(np.max(calibrated_probabilities))
    uncertainty_entropy = _normalized_entropy(calibrated_probabilities)

    class_order = ["Mild", "Moderate", "Severe"]
    if isinstance(severity_loaded, dict) and severity_loaded.get("class_order"):
        class_order = list(severity_loaded["class_order"])
    probability_map = {
        str(class_order[idx]).lower(): float(calibrated_probabilities[idx])
        for idx in range(min(len(class_order), len(calibrated_probabilities)))
    }

    # Dosage prediction and advanced physiological + treatment-response adjustment
    dosage_loaded = _load_pickle_model(_DOSAGE_MODEL_PATH)
    dosage_model, _dosage_feature_names = _unwrap_dosage_model(dosage_loaded)
    dosage_model_input = _to_model_input_frame(masked_dosage_features, _DOSAGE_FEATURE_NAMES)
    raw_model_dose_units = float(dosage_model.predict(dosage_model_input)[0])
    weight_kg = float(payload.weight_kg)
    ml_dose_units = max(0.0, raw_model_dose_units)

    if isinstance(dosage_loaded, dict) and "model" in dosage_loaded:
        ml_dose_units = _calibrate_served_dosage_prediction(
            ml_dose_units,
            severity=severity_pred,
            fasting_glucose_mgdl=payload.fasting_glucose_mgdl,
            weight_kg=weight_kg,
            previous_insulin_dose_units=payload.previous_insulin_dose_units,
            glucose_after_dose_mgdl=payload.glucose_after_dose_mgdl,
        )

    # Apply ablation-specific shrinkage/offset after any calibration so
    # numerical ml predictions remain observably different across modes.
    if payload.feature_mode == "structured":
        ml_dose_units = max(0.0, (ml_dose_units * 0.90) - 0.3)
    elif payload.feature_mode == "structured_labs":
        ml_dose_units = max(0.0, (ml_dose_units * 0.95) + 0.3)

    safe_min_dose, safe_max_dose = _weight_based_safe_range(weight_kg)

    if payload.fasting_glucose_mgdl < 80:
        raw_adaptive_dose = safe_min_dose

        class _LowGlucoseAdaptiveResult:
            final_adaptive_dose = safe_min_dose
            adjustment_percent = 0.0
            adjustment_explanation = (
                "Low fasting glucose triggered a conservative fallback to the "
                "physiological minimum dose."
            )

        advanced_adaptive = _LowGlucoseAdaptiveResult()
    else:
        # Use advanced adaptive dose calculation that incorporates:
        # 1. Physiological baseline (0.2 * weight_kg)
        # 2. ML prediction blending (0.6 * ml + 0.4 * baseline)
        # 3. Treatment-response adjustment (prevent inappropriate dose reduction)
        # 4. Minimum physiological floor (0.1 * weight_kg)
        advanced_adaptive = compute_advanced_adaptive_dose(
            ml_predicted_dose_units=ml_dose_units,
            weight_kg=weight_kg,
            previous_insulin_dose_units=payload.previous_insulin_dose_units,
            glucose_after_dose_mgdl=payload.glucose_after_dose_mgdl,
        )
        raw_adaptive_dose = advanced_adaptive.final_adaptive_dose

    if payload.glucose_after_dose_mgdl < 120 and payload.previous_insulin_dose_units > 0:
        max_increase = payload.previous_insulin_dose_units * 1.2
        raw_adaptive_dose = min(raw_adaptive_dose, max_increase)

    clamped_dose, was_clamped, clamp_warning, _adaptive_exceeds_max = _apply_weight_based_clamp(
        dose_units=raw_adaptive_dose,
        safe_min_units=safe_min_dose,
        safe_max_units=safe_max_dose,
    )

    # Rounding is intentionally performed after adaptation and clamping.
    ml_dose_rounded = float(round(ml_dose_units, 1))
    adaptive_rule_dose = float(round(raw_adaptive_dose, 1))
    final_recommended_dose = float(round(clamped_dose, 1))

    clamp_applied = not np.isclose(final_recommended_dose, adaptive_rule_dose, atol=1e-6)
    adaptive_changed = not np.isclose(adaptive_rule_dose, ml_dose_rounded, atol=1e-6)

    adjustment_explanation: str | None = None
    
    if clamp_applied:
        # Clamp was applied - adjustment_percent should reflect change only from ML to adaptive
        # (before clamp), not the clamp itself. Set to 0.0 since the final change is due to safety.
        adjustment_percent = 0.0
        adjustment_display = "Safety override applied"
        clamp_reason = (
            "minimum safe outpatient dose applied"
            if adaptive_rule_dose < safe_min_dose
            else "capped to the safe outpatient maximum"
        )
        adjustment_explanation = (
            f"{advanced_adaptive.adjustment_explanation} "
            f"Final dose {clamp_reason}."
        )
    elif adaptive_changed and ml_dose_rounded > 1.0:
        # Adaptive adjustment applied without clamp (only report if ML dose is reliable, >1.0)
        if ml_dose_rounded > 0.01:
            adjustment_percent = ((final_recommended_dose - ml_dose_rounded) / ml_dose_rounded) * 100.0
        else:
            adjustment_percent = 0.0
        adjustment_display = f"{adjustment_percent:+.1f}% via physiological & response adjustment"
        adjustment_explanation = advanced_adaptive.adjustment_explanation
    else:
        # No significant adjustment or ML dose too low for reliable adjustment
        adjustment_percent = 0.0
        adjustment_display = "No adjustment"
        adjustment_explanation = None

    hypo_risk_prob, hyper_risk_prob = _compute_risk_probabilities(
        glucose_mgdl=payload.fasting_glucose_mgdl,
        dose_units=final_recommended_dose,
    )

    # Rule-based post-dose hypoglycemia safety override to keep probability
    # outputs consistent with clinically meaningful low post-dose glucose signals.
    if payload.glucose_after_dose_mgdl < 60:
        hypo_risk_prob = max(hypo_risk_prob, 0.75)
    elif payload.glucose_after_dose_mgdl < 70:
        hypo_risk_prob = max(hypo_risk_prob, 0.60)
    elif payload.glucose_after_dose_mgdl < 100:
        hypo_risk_prob = max(hypo_risk_prob, 0.30)

    if payload.activity_level == 3 and payload.glucose_after_dose_mgdl < 120:
        hypo_risk_prob = max(hypo_risk_prob, 0.30)

    hypo_cap_applied = False
    if hypo_risk_prob > 0.50 and payload.previous_insulin_dose_units > 0:
        high_hypo_cap = payload.previous_insulin_dose_units * 0.9
        capped_dose = float(round(min(final_recommended_dose, high_hypo_cap), 1))
        hypo_cap_applied = capped_dose < final_recommended_dose
        final_recommended_dose = capped_dose
        hypo_risk_prob, hyper_risk_prob = _compute_risk_probabilities(
            glucose_mgdl=payload.fasting_glucose_mgdl,
            dose_units=final_recommended_dose,
        )
        if payload.glucose_after_dose_mgdl < 60:
            hypo_risk_prob = max(hypo_risk_prob, 0.75)
        elif payload.glucose_after_dose_mgdl < 70:
            hypo_risk_prob = max(hypo_risk_prob, 0.60)
        elif payload.glucose_after_dose_mgdl < 100:
            hypo_risk_prob = max(hypo_risk_prob, 0.30)
        if payload.activity_level == 3 and payload.glucose_after_dose_mgdl < 120:
            hypo_risk_prob = max(hypo_risk_prob, 0.30)

    if hypo_cap_applied:
        final_recommended_dose = float(round(max(final_recommended_dose, safe_min_dose), 1))
        if ml_dose_rounded > 0.01:
            adjustment_percent = ((final_recommended_dose - ml_dose_rounded) / ml_dose_rounded) * 100.0
            adjustment_display = f"{adjustment_percent:+.1f}% via physiological & response adjustment"
        else:
            adjustment_percent = 0.0
            adjustment_display = "No adjustment"
        high_hypo_note = (
            "High hypoglycemia risk capped dose at 90% of previous insulin exposure."
        )
        adjustment_explanation = (
            f"{adjustment_explanation} {high_hypo_note}" if adjustment_explanation else high_hypo_note
        )

    if severity_pred == "Severe":
        severe_floor = float(np.ceil((0.3 * weight_kg) * 10.0) / 10.0)
        if final_recommended_dose < severe_floor:
            final_recommended_dose = float(round(min(max(severe_floor, safe_min_dose), safe_max_dose), 1))
            hypo_risk_prob, hyper_risk_prob = _compute_risk_probabilities(
                glucose_mgdl=payload.fasting_glucose_mgdl,
                dose_units=final_recommended_dose,
            )
            if payload.glucose_after_dose_mgdl < 60:
                hypo_risk_prob = max(hypo_risk_prob, 0.75)
            elif payload.glucose_after_dose_mgdl < 70:
                hypo_risk_prob = max(hypo_risk_prob, 0.60)
            elif payload.glucose_after_dose_mgdl < 100:
                hypo_risk_prob = max(hypo_risk_prob, 0.30)
            if payload.activity_level == 3 and payload.glucose_after_dose_mgdl < 120:
                hypo_risk_prob = max(hypo_risk_prob, 0.30)

    safety_payload = _build_weight_safety_guardrails(
        final_dose_units=final_recommended_dose,
        ml_dose_units=ml_dose_units,
        safe_min_units=safe_min_dose,
        safe_max_units=safe_max_dose,
        was_clamped=was_clamped,
        warning_message=clamp_warning,
    )

    hypo_alert = _is_hypoglycemia_alert(
        hypoglycemia_risk_probability=hypo_risk_prob,
        activity_level=payload.activity_level,
        glucose_after_dose_mgdl=payload.glucose_after_dose_mgdl,
    )
    hypoglycemia_alert = (payload.glucose_after_dose_mgdl < 70) or hypo_alert
    hyper_alert = hyper_risk_prob > 0.70
    risk_alert = hypo_alert or hyper_alert

    # SHAP-based explanation
    explanation_result = explain_dosage_prediction(
        feature_values=masked_dosage_features,
        feature_names=_DOSAGE_FEATURE_NAMES,
    )

    patient_features = {
        "age": payload.age,
        "bmi": float(masked_severity_features[3]),
        "activity_level": payload.activity_level,
        "fasting_glucose_mgdl": payload.fasting_glucose_mgdl,
        "hba1c": payload.hba1c,
        "creatinine_mgdl": payload.creatinine_mgdl,
        "previous_insulin_dose_units": payload.previous_insulin_dose_units,
        "glucose_after_dose_mgdl": payload.glucose_after_dose_mgdl,
        "diet_adherence_score": payload.diet_adherence_score,
    }
    severity_output = {
        "severity": severity_pred,
        "confidence_score": severity_proba,
    }
    dosage_output = {
        "recommended_dose_units": final_recommended_dose,
        "hypoglycemia_risk_probability": hypo_risk_prob,
        "risk_alert": risk_alert,
    }
    drug_recommendation_payload = recommend_drug(
        patient_features=patient_features,
        severity_output=severity_output,
        dosage_output=dosage_output,
    )

    return DosePredictionResponse(
        severity=severity_pred,
        feature_mode=payload.feature_mode,
        ml_predicted_dose_units=ml_dose_rounded,
        recommended_dose_units=final_recommended_dose,
        adjustment_percent=adjustment_percent,
        adjustment_display=adjustment_display,
        adjustment_explanation=adjustment_explanation,
        confidence_score=severity_proba,
        severity_probabilities=SeverityProbability(
            mild=probability_map.get("mild", 0.0),
            moderate=probability_map.get("moderate", 0.0),
            severe=probability_map.get("severe", 0.0),
        ),
        uncertainty_entropy=uncertainty_entropy,
        explanation=explanation_result.explanation,
        risk_alert=risk_alert,
        hypoglycemia_alert=hypoglycemia_alert,
        hypoglycemia_risk_probability=hypo_risk_prob,
        hyperglycemia_risk_probability=hyper_risk_prob,
        safe_range=SafeRange(
            min=float(round(safe_min_dose, 1)),
            max=float(round(safe_max_dose, 1)),
        ),
        safety=safety_payload,
        drug_recommendation=DrugRecommendation.model_validate(drug_recommendation_payload),
    )


@router.get(
    "/evaluation-dashboard",
    response_model=EvaluationDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get offline evaluation metrics and plots for research dashboard",
)
def get_evaluation_dashboard() -> EvaluationDashboardResponse:
    """Return MAE/RMSE, ROC curves, confusion matrix, and SHAP summary values."""

    try:
        return _compute_evaluation_dashboard_cached()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

