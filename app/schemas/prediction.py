from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class InsulinDosePredictionRequest(BaseModel):
    """
    Input payload for requesting an insulin dose suggestion.

    The schema deliberately keeps a small, interpretable set of features.
    More complex, multi-modal inputs (e.g. CGM time series, activity, meals)
    can be added later in a backward-compatible way.
    """

    patient_id: int = Field(..., ge=1)

    # Current and recent glucose context
    current_glucose_mgdl: float = Field(..., gt=0)
    previous_glucose_mgdl: float | None = Field(
        default=None,
        description=(
            "Optional prior glucose value (mg/dL) close in time to the current "
            "reading, used for estimating short-term trend."
        ),
    )

    # Simple contextual flags
    is_preprandial: bool = Field(
        default=True,
        description="Whether the suggested dose is intended for a pre-meal context.",
    )
    is_bedtime: bool = Field(
        default=False,
        description="Whether the suggested dose is intended near bedtime.",
    )

    request_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp assigned by the caller; defaults to server time.",
    )


class InsulinDosePrediction(BaseModel):
    """
    Model output: a transparent, research-only insulin dose suggestion.
    """

    patient_id: int
    suggested_insulin_units: float = Field(
        ...,
        gt=0,
        description=(
            "Suggested subcutaneous insulin dose (in units). "
            "This is for research use only and must NOT be used "
            "for clinical decision-making."
        ),
    )
    model_name: str
    model_version: str
    rationale: str = Field(
        ...,
        description=(
            "Human-readable explanation of the main drivers behind the "
            "suggested dose, to support model interpretability in research."
        ),
    )

    model_config = ConfigDict(protected_namespaces=())


class DosePredictionPatientInput(BaseModel):
    """
    Patient-level feature vector used for ML-based severity and dosage prediction.

    These fields mirror the synthetic dataset used for model training so that
    the API remains aligned with the offline research workflow.
    """

    age: float = Field(..., ge=18, le=100)
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    bmi: float | None = Field(
        default=None,
        description=(
            "Body mass index. If omitted, it will be computed from weight and "
            "height assuming BMI = weight_kg / (height_m^2)."
        ),
    )
    fasting_glucose_mgdl: float = Field(..., gt=0)
    hba1c: float = Field(..., gt=0)
    creatinine_mgdl: float = Field(..., gt=0)
    previous_insulin_dose_units: float = Field(..., ge=0)
    glucose_after_dose_mgdl: float = Field(..., gt=0)
    activity_level: int = Field(
        ...,
        ge=0,
        le=3,
        description="Ordinal activity level (0=sedentary, 3=high).",
    )
    diet_adherence_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Self-reported or model-derived diet adherence score (0–100).",
    )
    feature_mode: Literal["structured", "structured_labs", "full"] = Field(
        default="full",
        validation_alias=AliasChoices("feature_mode", "ablation_mode"),
        description=(
            "Ablation mode controlling which modality groups are used for inference: "
            "structured only, structured+l labs, or full multi-modal."
        ),
    )


class SeverityProbability(BaseModel):
    """Per-class probabilities for calibrated confidence visualization."""

    mild: float = Field(..., ge=0, le=1)
    moderate: float = Field(..., ge=0, le=1)
    severe: float = Field(..., ge=0, le=1)


class SafetyGuardrails(BaseModel):
    """Safety checks and warnings for recommended dose values."""

    safe_min_units: float = Field(..., ge=0)
    safe_max_units: float = Field(..., ge=0)
    was_clamped: bool
    within_safe_range: bool
    exceeds_max_allowed: bool
    warning_message: str | None = None


class SafeRange(BaseModel):
    """Weight-scaled safe outpatient basal insulin range in units/day."""

    min: float = Field(..., ge=0)
    max: float = Field(..., ge=0)


class DrugRecommendation(BaseModel):
    """Adjunct pharmacotherapy recommendation with safety context."""

    primary_therapy: str
    adjunct_drug: str
    contraindications: list[str]
    confidence: float = Field(..., ge=0, le=1)
    explanation: str


class DosePredictionResponse(BaseModel):
    """
    Combined severity and insulin dose recommendation output.
    """

    severity: str = Field(
        ...,
        description="Predicted diabetes severity class (e.g. Mild, Moderate, Severe).",
    )
    feature_mode: Literal["structured", "structured_labs", "full"]
    ml_predicted_dose_units: float = Field(
        ...,
        ge=0,
        description="Raw insulin dose from the dosage regression model before adaptation.",
    )
    recommended_dose_units: float = Field(
        ...,
        ge=0,
        description="Final recommended insulin dose after hybrid adjustment.",
    )
    adjustment_percent: float = Field(
        ...,
        description="Relative percent change applied by hybrid adaptive adjustment.",
    )
    adjustment_display: str = Field(
        ...,
        description=(
            "Display-oriented adjustment text. Uses a percentage when valid, "
            "or a safety/low-baseline message when percentage is not clinically meaningful."
        ),
    )
    adjustment_explanation: str | None = Field(
        default=None,
        description="Optional clinical explanation when adjustment percentage is suppressed.",
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description=(
            "Model confidence in the severity prediction, expressed as the "
            "maximum class probability."
        ),
    )
    severity_probabilities: SeverityProbability
    uncertainty_entropy: float = Field(
        ...,
        ge=0,
        description="Shannon entropy of class probabilities (higher means more uncertain).",
    )
    explanation: str = Field(
        ...,
        description=(
            "Human-readable explanation summarizing the main drivers behind "
            "the recommended dose."
        ),
    )
    risk_alert: bool = Field(
        ...,
        description=(
            "Boolean flag indicating elevated hypoglycemia risk based on the "
            "hybrid adjustment logic."
        ),
    )
    hypoglycemia_alert: bool = Field(
        ...,
        description=(
            "Hypoglycemia-specific alert flag. True only when post-dose glucose "
            "is <70 mg/dL or hypoglycemia probability exceeds 0.70."
        ),
    )
    hypoglycemia_risk_probability: float = Field(..., ge=0, le=1)
    hyperglycemia_risk_probability: float = Field(..., ge=0, le=1)
    safe_range: SafeRange
    safety: SafetyGuardrails
    drug_recommendation: DrugRecommendation


class RocCurveSeries(BaseModel):
    """One-vs-rest ROC points for a specific class."""

    label: str
    fpr: list[float]
    tpr: list[float]


class ConfusionMatrixPayload(BaseModel):
    """Matrix and labels for confusion matrix visualization."""

    labels: list[str]
    matrix: list[list[int]]


class ShapSummaryPoint(BaseModel):
    """Mean absolute SHAP contribution per feature."""

    feature: str
    mean_abs_shap: float = Field(..., ge=0)


class EvaluationDashboardResponse(BaseModel):
    """Aggregate offline evaluation artifacts for the dashboard tab."""

    mae: float = Field(..., ge=0)
    rmse: float = Field(..., ge=0)
    roc_auc_ovr_macro: float = Field(..., ge=0, le=1)
    roc_curves: list[RocCurveSeries]
    confusion_matrix: ConfusionMatrixPayload
    shap_summary: list[ShapSummaryPoint]

