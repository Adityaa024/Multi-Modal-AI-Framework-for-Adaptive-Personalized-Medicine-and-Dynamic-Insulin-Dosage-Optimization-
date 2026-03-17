"""
Synthetic Type 2 Diabetes cohort generator.

This script creates 10,000 synthetic T2D patient records with clinically
plausible distributions and a simple, transparent insulin dosing heuristic.
The resulting dataset is saved as a CSV file for downstream research use.

The data and dosing logic are *not* suitable for clinical decision support.
They are intended for simulation, prototyping, and algorithm development.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class CohortConfig:
    """Configuration for the synthetic cohort and output."""

    n_patients: int = 10_000
    random_seed: int = 42
    target_glucose_mgdl: float = 110.0
    output_path: Path = Path("data") / "synthetic_t2d_patients.csv"


def _ensure_output_dir(path: Path) -> None:
    """
    Ensure that the parent directory of the output path exists.

    This keeps the script self-contained and robust when run from a fresh
    clone of the repository.
    """

    path.parent.mkdir(parents=True, exist_ok=True)


def sample_patient_attributes(cfg: CohortConfig) -> dict[str, np.ndarray]:
    """
    Sample core clinical and behavioral attributes for the synthetic cohort.

    Distributions are intentionally approximate but chosen to reflect:
    - Typical age range for T2D patients.
    - Higher BMI values than the general population.
    - Correlation between poor glycemic control and renal function.
    - Activity level and diet adherence as modifiable lifestyle factors.
    """

    rng = np.random.default_rng(cfg.random_seed)

    # Age distribution: middle-aged to elderly adults, skewed to older.
    age = rng.normal(loc=60, scale=10, size=cfg.n_patients).clip(30, 90)

    # Height (cm): approximate adult distribution, independent of T2D.
    height_cm = rng.normal(loc=170, scale=10, size=cfg.n_patients).clip(145, 200)

    # BMI: overweight/obese range common in T2D.
    bmi = rng.normal(loc=31, scale=4, size=cfg.n_patients).clip(22, 45)

    # Weight derived from BMI and height for internal consistency.
    height_m = height_cm / 100.0
    weight_kg = bmi * (height_m**2)

    # Fasting glucose (mg/dL): broad spectrum from near-normal to poorly controlled.
    fasting_glucose = rng.normal(loc=155, scale=35, size=cfg.n_patients).clip(80, 320)

    # HbA1c (%): moderately to poorly controlled range.
    hba1c = rng.normal(loc=8.0, scale=1.0, size=cfg.n_patients).clip(5.5, 12.5)

    # Creatinine (mg/dL): mildly elevated values are more common in T2D.
    creatinine = rng.normal(loc=1.1, scale=0.3, size=cfg.n_patients).clip(0.6, 2.5)

    # Activity level: ordinal 0–3 (sedentary to high), correlated with lower BMI.
    activity_base = rng.integers(0, 4, size=cfg.n_patients)
    activity_adjustment = (25 - (bmi - 25)).clip(-5, 5) / 10.0
    activity_level = np.clip(activity_base + activity_adjustment, 0, 3).round().astype(
        int
    )

    # Diet adherence: 0–100 score, higher when HbA1c is closer to target.
    hba1c_target = 7.0
    adherence_noise = rng.normal(loc=0, scale=10, size=cfg.n_patients)
    diet_adherence = (
        80 - 15 * (hba1c - hba1c_target) + adherence_noise
    ).clip(0, 100)

    return {
        "age": age,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bmi": bmi,
        "fasting_glucose_mgdl": fasting_glucose,
        "hba1c": hba1c,
        "creatinine_mgdl": creatinine,
        "activity_level": activity_level,
        "diet_adherence_score": diet_adherence,
    }


def derive_severity_labels(
    fasting_glucose_mgdl: np.ndarray,
    hba1c: np.ndarray,
) -> np.ndarray:
    """Derive Mild / Moderate / Severe labels using transparent thresholds."""

    mild_mask = (hba1c < 7.5) & (fasting_glucose_mgdl < 140)
    severe_mask = (hba1c >= 9.5) | (fasting_glucose_mgdl >= 200)

    labels = np.where(mild_mask, "Mild", "Moderate")
    labels = np.where(severe_mask, "Severe", labels)
    return labels


def simulate_insulin_dose_and_response(
    attrs: dict[str, np.ndarray],
    cfg: CohortConfig,
) -> dict[str, np.ndarray]:
    """
    Simulate previous dose, post-dose glucose, and corrected dose labels.

    The target label generation is intentionally aligned with physiological
    insulin ranges instead of the older low-dose heuristic. Dose labels are
    anchored by severity-scaled weight-based baselines, then adjusted for
    HbA1c, fasting glucose, post-dose glucose response, and activity.
    """

    rng = np.random.default_rng(cfg.random_seed + 1)

    weight_kg = attrs["weight_kg"]
    fasting_glucose = attrs["fasting_glucose_mgdl"]
    hba1c = attrs["hba1c"]
    activity_level = attrs["activity_level"]

    severity = derive_severity_labels(fasting_glucose, hba1c)
    severity_base = np.select(
        [severity == "Mild", severity == "Moderate", severity == "Severe"],
        [0.2, 0.3, 0.4],
        default=0.3,
    )

    base_dose_units = severity_base * weight_kg
    hba1c_multiplier = 1.0 + np.maximum(0.0, hba1c - 7.0) * 0.10
    fasting_multiplier = 1.0 + np.where(fasting_glucose > 180.0, 0.05, 0.0)
    activity_multiplier = 1.0 - np.where(activity_level >= 3, 0.10, 0.0)

    preliminary_optimal_dose = (
        base_dose_units * hba1c_multiplier * fasting_multiplier * activity_multiplier
    )

    previous_ratio = rng.normal(loc=0.92, scale=0.12, size=preliminary_optimal_dose.size)
    previous_insulin_dose = preliminary_optimal_dose * previous_ratio
    previous_insulin_dose += rng.normal(loc=0.0, scale=1.5, size=preliminary_optimal_dose.size)
    previous_insulin_dose = np.clip(previous_insulin_dose, 0.2 * weight_kg, 0.6 * weight_kg)

    glucose_deviation = np.maximum(0.0, fasting_glucose - cfg.target_glucose_mgdl)
    response_fraction = np.clip(
        previous_insulin_dose / np.maximum(preliminary_optimal_dose, 1e-6),
        0.3,
        1.4,
    )
    expected_improvement = glucose_deviation * 0.7 * response_fraction
    glucose_after = fasting_glucose - expected_improvement
    glucose_after += rng.normal(loc=0.0, scale=12.0, size=glucose_after.size)
    glucose_after = np.clip(glucose_after, 70.0, 320.0)

    response_multiplier = 1.0 + np.where(glucose_after > 180.0, 0.10, 0.0)
    optimal_dose_units = preliminary_optimal_dose * response_multiplier
    optimal_dose_units += rng.normal(loc=0.0, scale=2.0, size=optimal_dose_units.size)
    optimal_dose_units = np.clip(optimal_dose_units, 0.2 * weight_kg, 0.6 * weight_kg)

    return {
        "severity_label": severity,
        "previous_insulin_dose_units": previous_insulin_dose,
        "simulated_optimal_insulin_dose_units": optimal_dose_units,
        "glucose_after_dose_mgdl": glucose_after,
    }


def build_dataset(cfg: CohortConfig) -> pd.DataFrame:
    """End-to-end generation of the synthetic T2D dataset."""

    attrs = sample_patient_attributes(cfg)
    dosing = simulate_insulin_dose_and_response(attrs, cfg)

    data = {**attrs, **dosing}
    df = pd.DataFrame(data)
    return df


def main() -> None:
    """Generate the synthetic cohort and write it to disk as CSV."""

    cfg = CohortConfig()
    _ensure_output_dir(cfg.output_path)

    df = build_dataset(cfg)
    df.to_csv(cfg.output_path, index=False)

    print(f"Generated {len(df)} synthetic T2D records at: {cfg.output_path}")


if __name__ == "__main__":
    main()

