from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


SEVERITY_MILD = "Mild"
SEVERITY_MODERATE = "Moderate"
SEVERITY_SEVERE = "Severe"

DRUG_METFORMIN = "Metformin"
DRUG_SGLT2 = "SGLT2 Inhibitors"
DRUG_DPP4 = "DPP-4 Inhibitors"
DRUG_GLP1 = "GLP-1 Receptor Agonists"
DRUG_INSULIN_ONLY = "Insulin only"
DRUG_LIFESTYLE = "Lifestyle modification"

PRIMARY_BASAL_CONTINUATION = "Basal Insulin continuation"
PRIMARY_INSULIN_BASED = "Insulin-based therapy"
PRIMARY_LIFESTYLE_FOCUS = "Lifestyle-focused glycemic optimization"

CONTRA_AVOID_METFORMIN = "Avoid Metformin: elevated creatinine"
CONTRA_AVOID_GLP1 = "Avoid GLP-1 Receptor Agonists: underweight BMI"
CONTRA_AVOID_AGGRESSIVE_INSULIN = (
    "Avoid aggressive insulin escalation: hypoglycemia risk signal"
)
CONTRA_AVOID_SGLT2_RENAL = (
    "Avoid SGLT2 Inhibitors: renal impairment (creatinine > 1.8 mg/dL)"
)
CONTRA_AVOID_SGLT2_AKI_ELDERLY = (
    "Avoid SGLT2 Inhibitors: high risk of AKI in elderly renal impairment"
)
DRUG_DPP4_RENAL = "DPP-4 Inhibitors (dose-adjusted)"


@dataclass(frozen=True)
class DrugRecommendationResult:
    """Structured recommendation payload returned by the drug recommender."""

    primary_therapy: str
    adjunct_drug: str
    contraindications: list[str]
    confidence: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_therapy": self.primary_therapy,
            "adjunct_drug": self.adjunct_drug,
            "contraindications": self.contraindications,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


def _value(source: Mapping[str, Any], name: str, default: float | str | bool = 0.0) -> Any:
    """Safely fetch a named field from a mapping-like source."""

    return source.get(name, default)


def _build_explanation(
    hba1c: float,
    bmi: float,
    creatinine: float,
    glucose_after_dose: float,
    severity: str,
    adjunct: str,
    contraindications: list[str],
) -> str:
    """Create a concise human-readable rationale for recommendation output."""

    severity_l = severity.lower()

    parts: list[str] = []

    if hba1c > 9.0:
        parts.append(f"Elevated HbA1c ({hba1c:.1f}%) indicates need for therapy intensification")
    elif hba1c >= 7.5:
        parts.append(f"HbA1c ({hba1c:.1f}%) suggests additional glycemic control support")
    else:
        parts.append(f"HbA1c ({hba1c:.1f}%) is closer to target range")

    parts.append(f"{severity_l.capitalize()} severity profile supports {adjunct}")

    if bmi > 30.0 and DRUG_GLP1 in adjunct:
        parts.append(f"higher BMI ({bmi:.1f}) favors GLP-1 based weight-sensitive strategy")

    if creatinine > 1.5:
        parts.append(f"creatinine ({creatinine:.2f} mg/dL) limits renally sensitive options")
    else:
        parts.append(f"creatinine ({creatinine:.2f} mg/dL) is within safer range for selected therapy")

    if glucose_after_dose < 70:
        parts.append("Recent post-dose hypoglycemia signal detected")

    if contraindications:
        parts.append("contraindications were applied as safety overrides")

    return ". ".join(parts) + "."


def recommend_drug(
    patient_features: Mapping[str, Any],
    severity_output: Mapping[str, Any],
    dosage_output: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Recommend adjunct therapy using a rule-based safety-first baseline.

    Parameters
    ----------
    patient_features:
        Multi-modal patient attributes used for decision rules.
    severity_output:
        Severity prediction payload (expects `severity` and optional `confidence_score`).
    dosage_output:
        Dosage/risk payload (expects dose recommendation and risk flags/probabilities).

    Returns
    -------
    dict[str, Any]
        Keys: primary_therapy, adjunct_drug, contraindications, confidence, explanation.
    """

    age = float(_value(patient_features, "age", 0.0))
    bmi = float(_value(patient_features, "bmi", 0.0))
    activity_level = float(_value(patient_features, "activity_level", 0.0))
    fasting_glucose = float(_value(patient_features, "fasting_glucose_mgdl", 0.0))
    hba1c = float(_value(patient_features, "hba1c", 0.0))
    creatinine = float(_value(patient_features, "creatinine_mgdl", 0.0))
    _previous_insulin_dose = float(_value(patient_features, "previous_insulin_dose_units", 0.0))
    glucose_after_dose = float(_value(patient_features, "glucose_after_dose_mgdl", 0.0))
    diet_adherence = float(_value(patient_features, "diet_adherence_score", 0.0))

    severity = str(_value(severity_output, "severity", SEVERITY_MODERATE))
    severity_conf = float(_value(severity_output, "confidence_score", 0.5))
    recommended_dose = float(_value(dosage_output, "recommended_dose_units", 0.0))
    hypoglycemia_risk_prob = float(_value(dosage_output, "hypoglycemia_risk_probability", 0.0))
    risk_alert = bool(_value(dosage_output, "risk_alert", False))

    primary_therapy = PRIMARY_BASAL_CONTINUATION
    adjunct_drug = DRUG_METFORMIN

    if severity == SEVERITY_MILD:
        primary_therapy = PRIMARY_LIFESTYLE_FOCUS
        adjunct_drug = f"{DRUG_LIFESTYLE} + {DRUG_METFORMIN}"
    elif severity == SEVERITY_SEVERE:
        primary_therapy = PRIMARY_INSULIN_BASED
        adjunct_drug = f"{DRUG_INSULIN_ONLY} + {DRUG_METFORMIN}"
    else:
        adjunct_drug = f"{DRUG_METFORMIN} or {DRUG_SGLT2}"

    if hba1c > 9.0:
        primary_therapy = PRIMARY_INSULIN_BASED
        adjunct_drug = f"{DRUG_INSULIN_ONLY} + {DRUG_METFORMIN}"

    if bmi > 30.0 and severity != SEVERITY_MILD:
        adjunct_drug = DRUG_GLP1

    contraindications: list[str] = []

    if creatinine > 1.5:
        contraindications.append(CONTRA_AVOID_METFORMIN)
        if DRUG_METFORMIN in adjunct_drug:
            adjunct_drug = DRUG_SGLT2 if severity != SEVERITY_SEVERE else DRUG_DPP4

    if bmi < 18.5:
        contraindications.append(CONTRA_AVOID_GLP1)
        if adjunct_drug == DRUG_GLP1:
            adjunct_drug = DRUG_DPP4

    if creatinine > 1.8:
        contraindications.append(CONTRA_AVOID_SGLT2_RENAL)
        if DRUG_SGLT2 in adjunct_drug:
            adjunct_drug = DRUG_DPP4_RENAL if creatinine > 2.0 else DRUG_DPP4

    if creatinine > 2.0 and age > 65:
        contraindications.append(CONTRA_AVOID_SGLT2_AKI_ELDERLY)
        if DRUG_SGLT2 in adjunct_drug or "SGLT2" in adjunct_drug:
            adjunct_drug = DRUG_DPP4_RENAL

    # Hypoglycemia contraindication must be tied only to explicit hypo signals.
    if hypoglycemia_risk_prob > 0.70 or glucose_after_dose < 70:
        contraindications.append(CONTRA_AVOID_AGGRESSIVE_INSULIN)

    if severity == SEVERITY_MILD and hba1c < 7.2 and fasting_glucose < 130 and diet_adherence >= 75:
        adjunct_drug = DRUG_LIFESTYLE

    confidence = 0.45
    confidence += min(0.35, max(0.0, severity_conf * 0.35))

    signal_strength = 0.0
    if hba1c > 9.0:
        signal_strength += 0.08
    if bmi > 30.0:
        signal_strength += 0.05
    if creatinine > 1.5:
        signal_strength += 0.05
    if fasting_glucose > 180:
        signal_strength += 0.04
    if age >= 65:
        signal_strength -= 0.02
    if activity_level >= 2 and diet_adherence >= 80:
        signal_strength -= 0.02

    confidence = max(0.2, min(0.95, confidence + signal_strength - (0.03 * len(contraindications))))

    explanation = _build_explanation(
        hba1c=hba1c,
        bmi=bmi,
        creatinine=creatinine,
        glucose_after_dose=glucose_after_dose,
        severity=severity,
        adjunct=adjunct_drug,
        contraindications=contraindications,
    )

    result = DrugRecommendationResult(
        primary_therapy=primary_therapy,
        adjunct_drug=adjunct_drug,
        contraindications=contraindications,
        confidence=round(confidence, 3),
        explanation=explanation,
    )

    return result.to_dict()
