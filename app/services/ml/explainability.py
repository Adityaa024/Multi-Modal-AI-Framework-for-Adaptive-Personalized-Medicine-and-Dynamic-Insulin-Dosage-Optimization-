"""Explainability utilities for the engineered XGBoost dosage model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import shap


DOSAGE_MODEL_PATH = Path("data") / "dosage_model.pkl"


@dataclass
class DosageExplanation:
    """Container for dosage model SHAP-based explanations."""

    top_features: list[str]
    explanation: str


def _load_dosage_model(model_path: Path = DOSAGE_MODEL_PATH):
    """
    Load the trained dosage model from disk.

    Supports either a bare estimator or a bundled payload containing
    the estimator plus metadata such as feature names and metrics.
    """

    import pickle

    if not model_path.exists():
        raise FileNotFoundError(
            f"Dosage model not found at {model_path}. "
            "Train it first with `scripts/train_dosage_model.py`."
        )

    with model_path.open("rb") as f:
        payload = pickle.load(f)

    if isinstance(payload, dict) and "model" in payload:
        return payload["model"]
    return payload


def _build_example_frame(
    feature_values: Sequence[float],
    feature_names: Sequence[str],
) -> pd.DataFrame:
    """
    Helper to assemble a single-row DataFrame for SHAP.

    Using a DataFrame preserves feature names, which SHAP uses to
    align attributions correctly.
    """

    if len(feature_values) != len(feature_names):
        raise ValueError("feature_values and feature_names must have the same length.")

    return pd.DataFrame([feature_values], columns=list(feature_names))


def _fasting_glucose_phrase(value: float) -> str:
    if value < 80:
        return "low fasting glucose"
    if value <= 130:
        return "near-target fasting glucose"
    if value <= 180:
        return "elevated fasting glucose"
    return "high fasting glucose"


def _hba1c_phrase(value: float) -> str:
    if value < 7:
        return "near target HbA1c"
    if value <= 9:
        return "suboptimally controlled HbA1c"
    return "poorly controlled HbA1c"


def _describe_feature(name: str, value: float, contribution: float) -> str:
    """
    Build a short phrase describing how a feature influenced the dose.

    The text is intentionally coarse but clinically motivated.
    """

    direction = "increased" if contribution > 0 else "reduced"

    if name.lower() in {"hba1c"}:
        return f"{_hba1c_phrase(value)} {direction} the recommended dose"
    if "fasting_glucose" in name.lower():
        return f"{_fasting_glucose_phrase(value)} {direction} the recommended dose"
    if "bmi" in name.lower():
        return f"higher BMI {direction} the recommended dose"
    if "weight_kg" in name.lower():
        return f"higher body weight {direction} the recommended dose"
    if "creatinine" in name.lower():
        return f"renal function (creatinine) {direction} the recommended dose"
    if "activity_level" in name.lower():
        return f"activity level {direction} the recommended dose"
    if "diet_adherence" in name.lower():
        return f"diet adherence {direction} the recommended dose"
    if "previous_insulin_dose" in name.lower():
        return f"previous insulin dose {direction} the recommended dose"
    if "glucose_after_dose" in name.lower():
        return f"post-dose glucose pattern {direction} the recommended dose"

    return f"{name} {direction} the recommended dose"


def explain_dosage_prediction(
    feature_values: Iterable[float],
    feature_names: Sequence[str],
    model_path: Path = DOSAGE_MODEL_PATH,
) -> DosageExplanation:
    """
    Compute a SHAP-based explanation for a single dosage prediction.

    Parameters
    ----------
    feature_values:
        Iterable of feature values in the same order used during training
        (see `scripts/train_dosage_model.py`).
    feature_names:
        Ordered list of feature names corresponding to `feature_values`.
    model_path:
        Optional path to a pickled dosage model; defaults to the canonical
        location under `data/`.

    Returns
    -------
    DosageExplanation
        - `top_features`: names of the three most influential features by
          absolute SHAP value.
        - `explanation`: short natural-language description highlighting the
          combined effect of these features.
    """

    model = _load_dosage_model(model_path)
    X = _build_example_frame(list(feature_values), feature_names)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)[0]

    # Identify top 3 features by absolute contribution magnitude.
    abs_vals = np.abs(shap_values)
    top_indices = np.argsort(abs_vals)[-3:][::-1]

    top_feature_names = [feature_names[i] for i in top_indices]
    top_feature_values = [float(X.iloc[0, i]) for i in top_indices]
    top_contribs = [float(shap_values[i]) for i in top_indices]

    # Estimate relative change vs. baseline for textual description.
    prediction = float(model.predict(X)[0])
    expected_value = explainer.expected_value
    if isinstance(expected_value, np.ndarray):
        baseline = float(np.ravel(expected_value)[0])
    else:
        baseline = float(expected_value)
    if baseline != 0:
        delta_percent = (prediction - baseline) / abs(baseline)
    else:
        delta_percent = 0.0

    direction_word = "increased" if delta_percent >= 0 else "reduced"
    percent_str = f"{abs(delta_percent) * 100:.1f}%"

    # Build concise human-readable explanation from top features.
    feature_phrases = [
        _describe_feature(n, v, c)
        for n, v, c in zip(top_feature_names, top_feature_values, top_contribs)
    ]
    # Join first two with "and", keep third as additional context if present.
    if len(feature_phrases) >= 2:
        core_phrase = " and ".join(feature_phrases[:2])
    else:
        core_phrase = feature_phrases[0]

    explanation = f"{core_phrase} and, together, {direction_word} the recommended dose by {percent_str}."

    return DosageExplanation(
        top_features=top_feature_names,
        explanation=explanation,
    )

