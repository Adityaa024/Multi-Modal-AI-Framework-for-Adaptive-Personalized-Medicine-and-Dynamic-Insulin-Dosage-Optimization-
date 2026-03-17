from dataclasses import dataclass

import numpy as np
import pandas as pd


DOSE_REGRESSION_FEATURE_NAMES = [
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
    "glucose_hba1c_interaction",
    "dose_response_ratio",
    "weight_adjusted_dose",
    "insulin_resistance",
]


@dataclass
class GlucoseFeatures:
    """
    Lightweight container for derived glucose features.

    This dataclass makes the feature interface explicit and keeps the ML
    model independent of the raw API schema types.
    """

    current_glucose_mgdl: float
    delta_glucose_mgdl: float | None
    is_preprandial: bool
    is_bedtime: bool


def build_glucose_features(
    current_glucose_mgdl: float,
    previous_glucose_mgdl: float | None,
    is_preprandial: bool,
    is_bedtime: bool,
) -> GlucoseFeatures:
    """
    Derive simple, interpretable features from raw glucose inputs.

    This helper is intentionally minimal but provides a single, testable
    entry point for extending feature engineering (e.g. trend windows,
    circadian features, or multi-modal signals).
    """

    delta = None
    if previous_glucose_mgdl is not None:
        delta = current_glucose_mgdl - previous_glucose_mgdl

    return GlucoseFeatures(
        current_glucose_mgdl=current_glucose_mgdl,
        delta_glucose_mgdl=delta,
        is_preprandial=is_preprandial,
        is_bedtime=is_bedtime,
    )


@dataclass
class StructuredFeatures:
    """Core structured (demographic / anthropometric) features."""

    age: float
    weight_kg: float
    height_cm: float
    bmi: float


@dataclass
class LabFeatures:
    """Laboratory biomarkers relevant to glycemic control and renal status."""

    fasting_glucose_mgdl: float
    hba1c: float
    creatinine_mgdl: float


@dataclass
class BehavioralFeatures:
    """Lifestyle-related behavioral indicators."""

    activity_level: float
    diet_adherence_score: float


@dataclass
class EarlyFusionConfig:
    """
    Configuration for early-fusion feature normalization.

    `mean` and `std` are 1D arrays with length equal to the concatenated
    feature vector. They can be estimated from data during training and
    reused at inference time for consistent preprocessing.
    """

    mean: np.ndarray
    std: np.ndarray


@dataclass
class EarlyFusionFeatures:
    """
    Container for early-fused feature representations.

    - `raw_vector` holds the unnormalized concatenation of structured,
      lab, and behavioral features.
    - `normalized_vector` applies z-score normalization using either
      provided or default reference statistics.
    """

    raw_vector: np.ndarray
    normalized_vector: np.ndarray


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    """Compute BMI from weight and height."""

    height_m = max(height_cm / 100.0, 1e-6)
    return float(weight_kg / (height_m**2))


def build_dose_regression_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build the engineered feature frame used by the dosage regressor."""

    features = df.copy()

    if "bmi" not in features.columns:
        features["bmi"] = features.apply(
            lambda row: compute_bmi(float(row["weight_kg"]), float(row["height_cm"])),
            axis=1,
        )

    weight = features["weight_kg"].clip(lower=1e-6)
    glucose_after = features["glucose_after_dose_mgdl"].clip(lower=1.0)

    features["glucose_hba1c_interaction"] = (
        features["fasting_glucose_mgdl"] * features["hba1c"]
    )
    features["dose_response_ratio"] = (
        features["previous_insulin_dose_units"] / glucose_after
    )
    features["weight_adjusted_dose"] = (
        features["previous_insulin_dose_units"] / weight
    )
    features["insulin_resistance"] = (
        features["bmi"] * features["fasting_glucose_mgdl"] / 100.0
    )

    return features[DOSE_REGRESSION_FEATURE_NAMES].copy()


def build_dose_regression_vector(
    *,
    age: float,
    weight_kg: float,
    height_cm: float,
    bmi: float | None,
    fasting_glucose_mgdl: float,
    hba1c: float,
    creatinine_mgdl: float,
    previous_insulin_dose_units: float,
    glucose_after_dose_mgdl: float,
    activity_level: float,
    diet_adherence_score: float,
) -> np.ndarray:
    """Build an engineered feature vector in the training feature order."""

    resolved_bmi = float(bmi) if bmi is not None else compute_bmi(weight_kg, height_cm)
    safe_weight = max(weight_kg, 1e-6)
    safe_glucose_after = max(glucose_after_dose_mgdl, 1.0)

    return np.array(
        [
            age,
            weight_kg,
            height_cm,
            resolved_bmi,
            fasting_glucose_mgdl,
            hba1c,
            creatinine_mgdl,
            previous_insulin_dose_units,
            glucose_after_dose_mgdl,
            activity_level,
            diet_adherence_score,
            fasting_glucose_mgdl * hba1c,
            previous_insulin_dose_units / safe_glucose_after,
            previous_insulin_dose_units / safe_weight,
            resolved_bmi * fasting_glucose_mgdl / 100.0,
        ],
        dtype=float,
    )


def build_early_fusion_features(
    structured: StructuredFeatures,
    labs: LabFeatures,
    behavioral: BehavioralFeatures,
    config: EarlyFusionConfig | None = None,
) -> EarlyFusionFeatures:
    """
    Concatenate structured, lab, and behavioral features into a single vector
    and apply normalization.

    By default, the function uses reference means and standard deviations
    aligned with the synthetic cohort generator. In a production setting,
    callers should provide an `EarlyFusionConfig` fitted on the training
    dataset to ensure consistent preprocessing.
    """

    raw = np.array(
        [
            structured.age,
            structured.weight_kg,
            structured.height_cm,
            structured.bmi,
            labs.fasting_glucose_mgdl,
            labs.hba1c,
            labs.creatinine_mgdl,
            behavioral.activity_level,
            behavioral.diet_adherence_score,
        ],
        dtype=float,
    )

    if config is None:
        # Approximate reference statistics based on the synthetic data
        # generation process. These values serve as a reasonable default
        # for research use, but they should be replaced by empirically
        # estimated statistics when training on real datasets.
        ref_mean = np.array(
            [
                60.0,  # age
                90.0,  # weight_kg (approx. from BMI 31 and height 170 cm)
                170.0,  # height_cm
                31.0,  # bmi
                155.0,  # fasting_glucose_mgdl
                8.0,  # hba1c
                1.1,  # creatinine_mgdl
                1.5,  # activity_level
                80.0,  # diet_adherence_score
            ],
            dtype=float,
        )
        ref_std = np.array(
            [
                10.0,  # age
                15.0,  # weight_kg
                10.0,  # height_cm
                4.0,  # bmi
                35.0,  # fasting_glucose_mgdl
                1.0,  # hba1c
                0.3,  # creatinine_mgdl
                1.0,  # activity_level
                10.0,  # diet_adherence_score
            ],
            dtype=float,
        )
    else:
        ref_mean = config.mean
        ref_std = config.std

    # Guard against zero standard deviations to avoid division by zero.
    safe_std = np.where(ref_std == 0.0, 1.0, ref_std)
    normalized = (raw - ref_mean) / safe_std

    return EarlyFusionFeatures(raw_vector=raw, normalized_vector=normalized)
