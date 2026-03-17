from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from fastapi.testclient import TestClient

# Ensure repository root is importable when script is executed directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


SEED = 20260304
N_PATIENTS = 100
FEATURE_MODE = "full"
MAX_REASONABLE_ADJUSTMENT_PERCENT = 100.0


@dataclass
class StressResult:
    index: int
    passed: bool
    reasons: list[str]


def _build_patient_profile(rng: Random) -> dict[str, float | int | str]:
    """Generate one synthetic patient profile within requested clinical ranges."""

    age = rng.randint(30, 80)
    weight_kg = round(rng.uniform(45.0, 140.0), 1)
    height_cm = round(rng.uniform(150.0, 190.0), 1)

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m**2), 1)

    profile = {
        "age": age,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bmi": bmi,
        "fasting_glucose_mgdl": round(rng.uniform(60.0, 350.0), 1),
        "hba1c": round(rng.uniform(5.5, 12.5), 1),
        "creatinine_mgdl": round(rng.uniform(0.6, 3.0), 2),
        "diet_adherence_score": round(rng.uniform(30.0, 95.0), 1),
        "activity_level": rng.randint(1, 3),
        "previous_insulin_dose_units": round(rng.uniform(0.0, 40.0), 1),
        "glucose_after_dose_mgdl": round(rng.uniform(50.0, 300.0), 1),
        "feature_mode": FEATURE_MODE,
    }

    return profile


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _validate_response(payload: dict[str, Any], body: dict[str, Any], index: int) -> StressResult:
    """Validate response for clinical/safety consistency checks requested by user."""

    reasons: list[str] = []

    final_dose = body.get("recommended_dose_units")
    ml_dose = body.get("ml_predicted_dose_units")
    adjustment_percent = body.get("adjustment_percent")
    adjustment_display = body.get("adjustment_display")

    safe_range = body.get("safe_range", {})
    safe_min = safe_range.get("min")
    safe_max = safe_range.get("max")

    hypoglycemia_risk = body.get("hypoglycemia_risk_probability")
    hyperglycemia_risk = body.get("hyperglycemia_risk_probability")
    risk_alert = body.get("risk_alert")

    drug = body.get("drug_recommendation", {})
    adjunct_drug = str(drug.get("adjunct_drug", ""))

    # 1) final_dose within safe range
    if not all(_is_finite_number(v) for v in [final_dose, safe_min, safe_max]):
        reasons.append("Dose/safe_range contains non-finite value(s).")
    else:
        if float(final_dose) < float(safe_min) or float(final_dose) > float(safe_max):
            reasons.append(
                f"Final dose {final_dose} outside safe range [{safe_min}, {safe_max}]."
            )

    # 2) no negative dose
    if not _is_finite_number(final_dose) or float(final_dose) < 0:
        reasons.append(f"Final dose invalid or negative: {final_dose}")

    # 3) no infinite/NaN values in core numerics
    numeric_fields = {
        "ml_predicted_dose_units": ml_dose,
        "recommended_dose_units": final_dose,
        "adjustment_percent": adjustment_percent,
        "hypoglycemia_risk_probability": hypoglycemia_risk,
        "hyperglycemia_risk_probability": hyperglycemia_risk,
        "safe_range.min": safe_min,
        "safe_range.max": safe_max,
    }
    for name, value in numeric_fields.items():
        if not _is_finite_number(value):
            reasons.append(f"Non-finite numeric field: {name}={value}")

    # 4) hypoglycemia alert only if risk > 0.7 (plus symmetric hyper rule from backend)
    if isinstance(risk_alert, bool) and _is_finite_number(hypoglycemia_risk) and _is_finite_number(hyperglycemia_risk):
        expected_alert = (float(hypoglycemia_risk) > 0.70) or (float(hyperglycemia_risk) > 0.70)
        if risk_alert != expected_alert:
            reasons.append(
                "risk_alert mismatch: "
                f"risk_alert={risk_alert}, hypo={hypoglycemia_risk}, hyper={hyperglycemia_risk}."
            )
    else:
        reasons.append("Missing or invalid risk fields for alert validation.")

    # 5) metformin avoided if creatinine > 1.5
    if float(payload["creatinine_mgdl"]) > 1.5 and "Metformin" in adjunct_drug:
        reasons.append(
            f"Creatinine {payload['creatinine_mgdl']} > 1.5 but adjunct contains Metformin: {adjunct_drug}"
        )

    # 6) no absurd adjustment percentages
    if _is_finite_number(adjustment_percent):
        if (
            isinstance(adjustment_display, str)
            and adjustment_display.endswith("via adaptive rules")
            and abs(float(adjustment_percent)) > MAX_REASONABLE_ADJUSTMENT_PERCENT
        ):
            reasons.append(
                "Absurd adjustment percentage while adaptive rules are active: "
                f"{adjustment_percent}%"
            )
    else:
        reasons.append(f"Invalid adjustment_percent value: {adjustment_percent}")

    return StressResult(index=index, passed=len(reasons) == 0, reasons=reasons)


def run_stress_test(n_patients: int = N_PATIENTS, seed: int = SEED) -> int:
    """Run deterministic stress testing for the insulin dosing prediction endpoint."""

    rng = Random(seed)
    client = TestClient(app)

    passed = 0
    failed = 0

    for idx in range(1, n_patients + 1):
        payload = _build_patient_profile(rng)

        response = client.post("/api/v1/predictions/predict-dose", json=payload)
        if response.status_code != 200:
            failed += 1
            print(f"[FAIL #{idx}] HTTP {response.status_code}: {response.text}")
            continue

        body = response.json()
        result = _validate_response(payload=payload, body=body, index=idx)

        if result.passed:
            passed += 1
        else:
            failed += 1
            print(f"[FAIL #{idx}] payload={payload}")
            for reason in result.reasons:
                print(f"  - {reason}")

    print("\n=== Stress Test Summary ===")
    print(f"total tested: {n_patients}")
    print(f"passed: {passed}")
    print(f"failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_stress_test())
