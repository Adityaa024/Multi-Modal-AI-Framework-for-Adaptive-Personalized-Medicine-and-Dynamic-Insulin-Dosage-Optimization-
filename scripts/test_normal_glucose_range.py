"""
Test the API with normal glucose range patients (80-250 mg/dL only).
This simulates a cohort of patients with healthier baseline glucose levels.
"""
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


SEED = 20260319
N_PATIENTS = 500
FEATURE_MODE = "full"


@dataclass
class TestResult:
    index: int
    passed: bool
    reasons: list[str]


def _build_normal_glucose_patient(rng: Random) -> dict[str, float | int | str]:
    """Generate synthetic patient profile with normal glucose range (80-250 mg/dL)."""

    age = rng.randint(30, 80)
    weight_kg = round(rng.uniform(45.0, 140.0), 1)
    height_cm = round(rng.uniform(150.0, 190.0), 1)

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m**2), 1)

    # CONSTRAINT: Only normal glucose range
    profile = {
        "age": age,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "bmi": bmi,
        "fasting_glucose_mgdl": round(rng.uniform(80.0, 250.0), 1),  # **NORMAL RANGE ONLY**
        "hba1c": round(rng.uniform(5.5, 12.5), 1),
        "creatinine_mgdl": round(rng.uniform(0.6, 3.0), 2),
        "diet_adherence_score": round(rng.uniform(30.0, 95.0), 1),
        "activity_level": rng.randint(1, 3),
        "previous_insulin_dose_units": round(rng.uniform(0.0, 40.0), 1),
        "glucose_after_dose_mgdl": round(rng.uniform(80.0, 250.0), 1),  # **NORMAL RANGE ONLY**
        "feature_mode": FEATURE_MODE,
    }

    return profile


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _compute_hypoglycemia_alert_like_api(
    hypo_risk: float, activity_level: int, glucose_after_mgdl: float
) -> bool:
    """Replicate the API's _is_hypoglycemia_alert logic exactly."""
    if hypo_risk >= 0.35:
        return True
    if hypo_risk >= 0.30:
        return True
    if hypo_risk >= 0.30 and glucose_after_mgdl < 100:
        return True
    if hypo_risk >= 0.25 and activity_level == 3:
        return True
    return False


def _validate_response(payload: dict[str, Any], body: dict[str, Any], index: int) -> TestResult:
    """Validate response for clinical/safety consistency checks."""

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

    # 4) risk_alert matches API policy: hypo_alert OR hyper_alert
    if isinstance(risk_alert, bool) and _is_finite_number(hypoglycemia_risk) and _is_finite_number(hyperglycemia_risk):
        activity_level = payload.get("activity_level", 1)
        glucose_after_dose_mgdl = payload.get("glucose_after_dose_mgdl", 100.0)
        
        hypo_alert = _compute_hypoglycemia_alert_like_api(
            float(hypoglycemia_risk), int(activity_level), float(glucose_after_dose_mgdl)
        )
        hyper_alert = float(hyperglycemia_risk) > 0.70
        expected_alert = hypo_alert or hyper_alert
        
        if risk_alert != expected_alert:
            reasons.append(
                f"risk_alert mismatch: expected {expected_alert}, got {risk_alert}"
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
        MAX_ADJUSTMENT = 100.0
        if (
            isinstance(adjustment_display, str)
            and "adaptive rules" in adjustment_display
            and abs(float(adjustment_percent)) > MAX_ADJUSTMENT
        ):
            reasons.append(
                f"Absurd adjustment percentage: {adjustment_percent}%"
            )
    else:
        reasons.append(f"Invalid adjustment_percent value: {adjustment_percent}")

    return TestResult(index=index, passed=len(reasons) == 0, reasons=reasons)


def run_normal_glucose_test(n_patients: int = N_PATIENTS, seed: int = SEED) -> int:
    """Run testing for normal glucose range patients only."""

    rng = Random(seed)
    client = TestClient(app)
    
    passed_count = 0
    failed_count = 0
    failures: list[tuple[int, dict[str, Any], list[str]]] = []
    
    dosed_min = float('inf')
    dosed_max = float('-inf')
    dosed_sum = 0.0
    dosed_count = 0
    
    print(f"\n{'='*80}")
    print(f"NORMAL GLUCOSE RANGE TEST: N={n_patients} patients (glucose 80-250 mg/dL)")
    print(f"{'='*80}")

    for i in range(n_patients):
        payload = _build_normal_glucose_patient(rng)
        
        try:
            response = client.post("/api/v1/predictions/predict-dose", json=payload)
            response.raise_for_status()
            body = response.json()
            
            result = _validate_response(payload, body, i)
            if result.passed:
                passed_count += 1
                dose = body.get("recommended_dose_units", 0.0)
                dosed_min = min(dosed_min, dose)
                dosed_max = max(dosed_max, dose)
                dosed_sum += dose
                dosed_count += 1
            else:
                failed_count += 1
                failures.append((i, payload, result.reasons))
                
        except Exception as e:
            failed_count += 1
            failures.append((i, payload, [f"Exception: {str(e)}"]))

    # Compute statistics
    pass_rate = (passed_count / n_patients * 100.0) if n_patients > 0 else 0.0
    mean_dose = dosed_sum / dosed_count if dosed_count > 0 else 0.0
    
    print(f"\nRESULTS:")
    print(f"  Total tested:      {n_patients}")
    print(f"  Passed:            {passed_count}")
    print(f"  Failed:            {failed_count}")
    print(f"  Pass rate:         {pass_rate:.1f}%")
    print(f"\nDOSE STATISTICS (from passed cases):")
    print(f"  Min dose:          {dosed_min:.1f} units")
    print(f"  Max dose:          {dosed_max:.1f} units")
    print(f"  Mean dose:         {mean_dose:.2f} units")
    print(f"  Sample size:       {dosed_count}")
    
    if failures:
        print(f"\nFAILED CASES (showing first 10):")
        for idx, payload, reasons in failures[:10]:
            print(f"\n[FAIL #{idx}] glucose_fasting={payload.get('fasting_glucose_mgdl')}, "
                  f"glucose_after={payload.get('glucose_after_dose_mgdl')}")
            for reason in reasons:
                print(f"  - {reason}")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(run_normal_glucose_test())
