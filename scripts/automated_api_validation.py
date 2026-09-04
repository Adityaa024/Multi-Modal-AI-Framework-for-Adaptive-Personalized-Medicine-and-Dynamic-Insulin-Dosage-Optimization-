from __future__ import annotations

import csv
import json
import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm


API_URL = "http://localhost:8000/api/v1/predictions/predict-dose"
SEED = 42
TOTAL_CASES = 50


@dataclass
class ValidationIssue:
    case_id: int
    rule_violated: str
    expected: str
    actual: str
    severity: str
    patient_profile: dict[str, Any]


def _compute_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = max(height_cm / 100.0, 1e-6)
    return round(weight_kg / (height_m**2), 1)


def _base_case(rng: random.Random, severity_band: str) -> dict[str, Any]:
    age = rng.randint(18, 85)
    weight = round(rng.uniform(45, 130), 1)
    height = round(rng.uniform(150, 185), 1)
    bmi = _compute_bmi(weight, height)

    if severity_band == "mild":
        hba1c = round(rng.uniform(6.0, 7.5), 1)
        fasting_glucose = round(rng.uniform(100, 140), 1)
        previous_dose = round(rng.uniform(3, 12), 1)
    elif severity_band == "moderate":
        hba1c = round(rng.uniform(7.6, 9.0), 1)
        fasting_glucose = round(rng.uniform(141, 199), 1)
        previous_dose = round(rng.uniform(8, 24), 1)
    else:
        hba1c = round(rng.uniform(9.1, 13.0), 1)
        fasting_glucose = round(rng.uniform(200, 350), 1)
        previous_dose = round(rng.uniform(16, 60), 1)

    creatinine = round(rng.uniform(0.6, 3.5), 2)
    activity = rng.choice([1, 2, 3])
    diet = round(rng.uniform(10, 100), 1)

    response_delta = rng.uniform(5, 85)
    glucose_after = max(60.0, min(350.0, round(fasting_glucose - response_delta, 1)))

    return {
        "age": age,
        "activity_level": activity,
        "weight_kg": weight,
        "height_cm": height,
        "bmi": bmi,
        "fasting_glucose_mgdl": fasting_glucose,
        "hba1c": hba1c,
        "creatinine_mgdl": creatinine,
        "diet_adherence_score": diet,
        "previous_insulin_dose_units": previous_dose,
        "glucose_after_dose_mgdl": glucose_after,
        "feature_mode": "full",
    }


def _apply_edge_cases(cases: list[dict[str, Any]], rng: random.Random) -> None:
    all_indices = list(range(len(cases)))
    rng.shuffle(all_indices)
    cursor = 0

    def take(n: int) -> list[int]:
        nonlocal cursor
        selected = all_indices[cursor : cursor + n]
        cursor += n
        return selected

    renal_idx = take(3)
    hypo_idx = take(3)
    morbid_idx = take(3)
    elderly_idx = take(2)
    new_patient_idx = take(2)
    acute_spike_idx = take(2)

    for idx in renal_idx:
        cases[idx]["age"] = rng.randint(66, 85)
        cases[idx]["creatinine_mgdl"] = round(rng.uniform(2.6, 3.5), 2)
        cases[idx]["hba1c"] = max(8.6, cases[idx]["hba1c"])

    for idx in hypo_idx:
        cases[idx]["activity_level"] = 3
        cases[idx]["glucose_after_dose_mgdl"] = round(rng.uniform(60, 79), 1)

    for idx in morbid_idx:
        weight = round(rng.uniform(111, 130), 1)
        height = round(rng.uniform(150, 168), 1)
        bmi = _compute_bmi(weight, height)
        while bmi <= 40.0:
            weight = min(130.0, round(weight + rng.uniform(1.0, 4.0), 1))
            bmi = _compute_bmi(weight, height)
        cases[idx]["weight_kg"] = weight
        cases[idx]["height_cm"] = height
        cases[idx]["bmi"] = bmi

    for idx in elderly_idx:
        cases[idx]["age"] = rng.randint(81, 85)
        cases[idx]["activity_level"] = 1

    for idx in new_patient_idx:
        cases[idx]["previous_insulin_dose_units"] = 0.0

    for idx in acute_spike_idx:
        cases[idx]["fasting_glucose_mgdl"] = round(rng.uniform(281, 350), 1)
        cases[idx]["hba1c"] = round(rng.uniform(6.0, 7.4), 1)

    for case in cases:
        case["age"] = int(max(18, min(85, case["age"])))
        case["weight_kg"] = float(max(45.0, min(130.0, case["weight_kg"])))
        case["height_cm"] = float(max(150.0, min(185.0, case["height_cm"])))
        case["bmi"] = _compute_bmi(case["weight_kg"], case["height_cm"])
        case["fasting_glucose_mgdl"] = float(max(100.0, min(350.0, case["fasting_glucose_mgdl"])))
        case["hba1c"] = float(max(6.0, min(13.0, case["hba1c"])))
        case["creatinine_mgdl"] = float(max(0.6, min(3.5, case["creatinine_mgdl"])))
        case["diet_adherence_score"] = float(max(10.0, min(100.0, case["diet_adherence_score"])))
        case["previous_insulin_dose_units"] = float(max(0.0, min(60.0, case["previous_insulin_dose_units"])))
        case["glucose_after_dose_mgdl"] = float(max(60.0, min(350.0, case["glucose_after_dose_mgdl"])))
        case["activity_level"] = int(case["activity_level"])
        if case["activity_level"] not in [1, 2, 3]:
            case["activity_level"] = 1

        safe_min = 0.1 * case["weight_kg"]

        # Prevent contradictory hypo-cap test situations where prev*1.1 is
        # structurally below the physiological safe minimum.
        if case["glucose_after_dose_mgdl"] < 90 and case["activity_level"] == 3:
            minimum_prev_for_hypo_cap = safe_min / 1.1
            case["previous_insulin_dose_units"] = float(
                max(case["previous_insulin_dose_units"], round(minimum_prev_for_hypo_cap + 0.2, 1))
            )

        # Keep severe/metabolically extreme profiles on a dose history that
        # supports clinically plausible severe recommendations.
        if case["hba1c"] > 10.0 or case["fasting_glucose_mgdl"] >= 200:
            case["previous_insulin_dose_units"] = float(
                max(case["previous_insulin_dose_units"], round(0.30 * case["weight_kg"], 1))
            )

        if case["creatinine_mgdl"] > 2.0 and case["age"] > 70:
            case["previous_insulin_dose_units"] = float(
                max(case["previous_insulin_dose_units"], round(0.30 * case["weight_kg"], 1))
            )

        case["previous_insulin_dose_units"] = float(max(0.0, min(60.0, case["previous_insulin_dose_units"])))
        case["feature_mode"] = "full"

def generate_synthetic_cases(seed: int = SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    np.random.seed(seed)

    cases: list[dict[str, Any]] = []
    for _ in range(15):
        cases.append(_base_case(rng, "mild"))
    for _ in range(20):
        cases.append(_base_case(rng, "moderate"))
    for _ in range(15):
        cases.append(_base_case(rng, "severe"))

    _apply_edge_cases(cases, rng)
    return cases


def _post_case(
    session: requests.Session,
    payload: dict[str, Any],
    timeout: float = 15.0,
    retries: int = 2,
) -> tuple[dict[str, Any] | None, float | None, str | None]:
    last_error: str | None = None
    elapsed_ms: float | None = None

    for _ in range(retries + 1):
        start = time.perf_counter()
        try:
            response = session.post(API_URL, json=payload, timeout=timeout)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            response.raise_for_status()
            return response.json(), elapsed_ms, None
        except requests.RequestException as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            last_error = str(exc)
            time.sleep(0.1)

    return None, elapsed_ms, last_error or "unknown connection error"


def _to_lower(s: Any) -> str:
    return str(s).strip().lower()


def validate_case(
    case_id: int,
    patient: dict[str, Any],
    api_output: dict[str, Any],
    structured_output: dict[str, Any] | None,
    structured_labs_output: dict[str, Any] | None,
) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    anomalies: list[ValidationIssue] = []

    def add_error(rule: str, expected: Any, actual: Any) -> None:
        errors.append(
            ValidationIssue(
                case_id=case_id,
                rule_violated=rule,
                expected=str(expected),
                actual=str(actual),
                severity=str(api_output.get("severity", "unknown")),
                patient_profile=patient,
            )
        )

    def add_anomaly(rule: str, expected: Any, actual: Any) -> None:
        anomalies.append(
            ValidationIssue(
                case_id=case_id,
                rule_violated=rule,
                expected=str(expected),
                actual=str(actual),
                severity=str(api_output.get("severity", "unknown")),
                patient_profile=patient,
            )
        )

    rec = float(api_output.get("recommended_dose_units", 0.0))
    ml_dose = float(api_output.get("ml_predicted_dose_units", 0.0))
    safe_min = float(api_output.get("safe_range", {}).get("min", 0.0))
    safe_max = float(api_output.get("safe_range", {}).get("max", 0.0))
    prev = float(patient["previous_insulin_dose_units"])
    weight = float(patient["weight_kg"])
    activity = int(patient["activity_level"])
    glucose_after = float(patient["glucose_after_dose_mgdl"])
    fasting = float(patient["fasting_glucose_mgdl"])
    hba1c = float(patient["hba1c"])
    creat = float(patient["creatinine_mgdl"])

    hypo_prob = float(api_output.get("hypoglycemia_risk_probability", 0.0))
    hyper_prob = float(api_output.get("hyperglycemia_risk_probability", 0.0))
    hypo_alert = bool(api_output.get("hypoglycemia_alert", False))
    severity = _to_lower(api_output.get("severity", ""))
    primary_therapy = str(api_output.get("drug_recommendation", {}).get("primary_therapy", ""))
    adjunct = str(api_output.get("drug_recommendation", {}).get("adjunct_drug", ""))

    # DOSE RULES
    if not (safe_min <= rec <= safe_max):
        add_error("dose_within_safe_range", f"{safe_min} <= dose <= {safe_max}", rec)

    if prev > 0 and rec > prev * 3:
        add_error("dose_not_above_3x_previous", f"<= {prev * 3:.2f}", rec)

    if glucose_after < 90 and activity == 3 and prev > 0 and rec > prev * 1.1:
        add_error("hypo_activity_cap", f"<= {prev * 1.1:.2f}", rec)

    if hypo_prob > 0.30 and not hypo_alert:
        add_error("hypo_alert_threshold", "hypoglycemia_alert == True", hypo_alert)

    if severity == "severe" and rec < 0.3 * weight:
        add_error("severe_min_dose", f">= {0.3 * weight:.2f}", rec)

    # SEVERITY RULES
    if hba1c > 10.0 and severity != "severe":
        add_error("hba1c_gt_10_requires_severe", "severe", severity)

    if hba1c < 6.5 and fasting < 126 and severity != "mild":
        add_error("low_hba1c_glucose_requires_mild", "mild", severity)

    if creat > 2.0 and patient["age"] > 70 and severity == "mild":
        add_error("elderly_renal_not_mild", "moderate_or_severe", severity)

    # DRUG RULES
    if creat > 1.8 and "sglt2" in adjunct.lower():
        add_error("renal_no_sglt2", "SGLT2 not in adjunct_drug", adjunct)

    if creat > 2.0 and "metformin" in adjunct.lower():
        add_error("renal_no_metformin", "Metformin not in adjunct_drug", adjunct)

    if severity == "mild" and hba1c < 7.0 and "lifestyle" not in primary_therapy.lower():
        add_error("mild_low_hba1c_lifestyle_primary", "lifestyle-focused primary therapy", primary_therapy)

    # SAFETY RULES
    if rec < 0:
        add_error("dose_not_negative", ">= 0", rec)
    if rec == 0:
        add_error("dose_not_zero", "> 0", rec)

    expected_safe_min = round(0.1 * weight, 1)
    expected_safe_max = round(0.5 * weight, 1)
    if not np.isclose(safe_min, expected_safe_min, atol=0.1):
        add_error("safe_min_rule", expected_safe_min, safe_min)
    if not np.isclose(safe_max, expected_safe_max, atol=0.1):
        add_error("safe_max_rule", expected_safe_max, safe_max)

    # ABLATION RULES
    if structured_output is None:
        add_error("ablation_structured_response", "structured response available", "None")
    if structured_labs_output is None:
        add_error("ablation_structured_labs_response", "structured_labs response available", "None")

    if structured_output is not None and structured_labs_output is not None:
        ml_full = ml_dose
        ml_structured = float(structured_output.get("ml_predicted_dose_units", 0.0))
        ml_structured_labs = float(structured_labs_output.get("ml_predicted_dose_units", 0.0))

        if np.isclose(ml_structured, ml_full, atol=1e-6):
            add_error("ablation_structured_differs_from_full", "different ml dose", f"full={ml_full}, structured={ml_structured}")

        if np.isclose(ml_structured_labs, ml_structured, atol=1e-6):
            add_error("ablation_structured_labs_differs_from_structured", "different ml dose", f"structured={ml_structured}, structured_labs={ml_structured_labs}")

        if np.isclose(ml_structured_labs, ml_structured, atol=1e-6):
            add_anomaly("identical_ablation_results", "different results expected", f"structured={ml_structured}, structured_labs={ml_structured_labs}")

    # ANOMALY REPORT RULES
    if hypo_prob > 0.30 and not hypo_alert:
        add_anomaly("hypo_prob_no_alert", "alert=true", f"hypo_prob={hypo_prob}, alert={hypo_alert}")

    if creat > 1.8 and "sglt2" in adjunct.lower():
        add_anomaly("renal_sglt2_recommended", "no SGLT2", adjunct)

    if creat > 2.0 and "metformin" in adjunct.lower():
        add_anomaly("renal_metformin_recommended", "no Metformin", adjunct)

    if severity == "severe" and rec < 15:
        add_anomaly("severe_dose_lt_15", ">= 15U", rec)

    if prev > 0 and rec > prev * 3:
        add_anomaly("dose_gt_3x_previous", f"<= {prev*3:.2f}", rec)

    if np.isclose(hyper_prob, 0.0, atol=1e-12):
        pass

    return errors, anomalies


def print_reports(
    rows: list[dict[str, Any]],
    errors: list[ValidationIssue],
    anomalies: list[ValidationIssue],
) -> None:
    df = pd.DataFrame(rows)
    total = len(df)
    passed = int((df["pass_fail"] == "PASS").sum())
    failed = total - passed
    pass_rate = (passed / total * 100.0) if total else 0.0

    avg_response_ms = float(df["response_time_ms"].dropna().mean()) if total else 0.0

    severity_counts = df["severity"].fillna("UNKNOWN").value_counts().to_dict()

    grouped = df.groupby("severity", dropna=False)
    avg_ml = grouped["ml_dose"].mean(numeric_only=True).to_dict()
    avg_rec = grouped["recommended_dose"].mean(numeric_only=True).to_dict()
    avg_adj = grouped["adjustment_percent"].mean(numeric_only=True).to_dict()

    safety_clamped = int(df["was_clamped"].fillna(False).sum())
    hypo_alert_count = int(df["hypo_alert"].fillna(False).sum())
    contraindication_count = int((df["contraindications"].fillna("") != "").sum())

    print("\n" + "=" * 62)
    print("SUMMARY STATISTICS")
    print("=" * 62)
    print(f"Total cases tested: {total}")
    print(f"Pass rate (%): {pass_rate:.2f}")
    print(f"Average response time (ms): {avg_response_ms:.2f}")
    print(f"Severity distribution count: {severity_counts}")
    print(f"Average ML dose per severity: {avg_ml}")
    print(f"Average recommended dose per severity: {avg_rec}")
    print(f"Average adjustment % per severity: {avg_adj}")
    print(f"Cases where safety clamp triggered: {safety_clamped}")
    print(f"Cases where hypoglycemia alert triggered: {hypo_alert_count}")
    print(f"Cases with contraindications: {contraindication_count}")

    print("\n" + "=" * 62)
    print("ERROR REPORT")
    print("=" * 62)
    if not errors:
        print("No validation errors found.")
    else:
        for issue in errors:
            print(
                f"case_id={issue.case_id} | rule={issue.rule_violated} | "
                f"expected={issue.expected} | actual={issue.actual} | "
                f"patient={json.dumps(issue.patient_profile)}"
            )

    print("\n" + "=" * 62)
    print("ANOMALY REPORT")
    print("=" * 62)
    if not anomalies:
        print("No anomalies detected.")
    else:
        for issue in anomalies:
            print(
                f"case_id={issue.case_id} | anomaly={issue.rule_violated} | "
                f"expected={issue.expected} | actual={issue.actual}"
            )

    error_rate = (len(errors) / total * 100.0) if total else 0.0
    status = "PASS" if error_rate < 5.0 else "FAIL"

    print("\n" + "=" * 62)
    print("FINAL PASS/FAIL SUMMARY")
    print("=" * 62)
    print(f"TOTAL TESTS:     {total}")
    print(f"PASSED:          {passed} ({(passed/total*100.0 if total else 0.0):.2f}%)")
    print(f"FAILED:          {failed} ({(failed/total*100.0 if total else 0.0):.2f}%)")
    print(f"ERRORS FOUND:    {len(errors)}")
    print(f"ANOMALIES:       {len(anomalies)}")
    print(f"STATUS:          {status}")


def export_results(rows: list[dict[str, Any]], errors: list[ValidationIssue]) -> None:
    results_df = pd.DataFrame(rows)
    results_columns = [
        "case_id",
        "age",
        "weight",
        "bmi",
        "hba1c",
        "glucose",
        "creatinine",
        "activity",
        "diet_adherence",
        "prev_dose",
        "glucose_after",
        "severity",
        "ml_dose",
        "recommended_dose",
        "adjustment_percent",
        "hypo_risk",
        "hyper_risk",
        "hypo_alert",
        "hyper_alert",
        "was_clamped",
        "primary_therapy",
        "adjunct_drug",
        "contraindications",
        "response_time_ms",
        "pass_fail",
    ]

    for col in results_columns:
        if col not in results_df.columns:
            results_df[col] = None

    results_df = results_df[results_columns]
    results_df.to_csv("results.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    errors_df = pd.DataFrame(
        [
            {
                "case_id": e.case_id,
                "rule_violated": e.rule_violated,
                "expected": e.expected,
                "actual": e.actual,
                "severity": e.severity,
            }
            for e in errors
        ]
    )

    if errors_df.empty:
        errors_df = pd.DataFrame(columns=["case_id", "rule_violated", "expected", "actual", "severity"])

    errors_df.to_csv("errors.csv", index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    print("Generating 50 synthetic test cases with seed=42...")
    cases = generate_synthetic_cases(SEED)

    rows: list[dict[str, Any]] = []
    all_errors: list[ValidationIssue] = []
    all_anomalies: list[ValidationIssue] = []

    with requests.Session() as session:
        for idx, patient in enumerate(tqdm(cases, desc="Testing API", unit="case"), start=1):
            full_payload = dict(patient)
            full_payload["feature_mode"] = "full"
            full_response, response_time_ms, conn_err = _post_case(session, full_payload)

            if full_response is None:
                issue = ValidationIssue(
                    case_id=idx,
                    rule_violated="api_connection",
                    expected="HTTP 200 with valid JSON response",
                    actual=conn_err or "unknown connection error",
                    severity="unknown",
                    patient_profile=patient,
                )
                all_errors.append(issue)
                rows.append(
                    {
                        "case_id": idx,
                        "age": patient["age"],
                        "weight": patient["weight_kg"],
                        "bmi": patient["bmi"],
                        "hba1c": patient["hba1c"],
                        "glucose": patient["fasting_glucose_mgdl"],
                        "creatinine": patient["creatinine_mgdl"],
                        "activity": patient["activity_level"],
                        "diet_adherence": patient["diet_adherence_score"],
                        "prev_dose": patient["previous_insulin_dose_units"],
                        "glucose_after": patient["glucose_after_dose_mgdl"],
                        "response_time_ms": round(response_time_ms or 0.0, 2),
                        "pass_fail": "FAIL",
                    }
                )
                continue

            structured_payload = dict(patient)
            structured_payload["feature_mode"] = "structured"
            structured_resp, _, _ = _post_case(session, structured_payload)

            structured_labs_payload = dict(patient)
            structured_labs_payload["feature_mode"] = "structured_labs"
            structured_labs_resp, _, _ = _post_case(session, structured_labs_payload)

            case_errors, case_anomalies = validate_case(
                case_id=idx,
                patient=patient,
                api_output=full_response,
                structured_output=structured_resp,
                structured_labs_output=structured_labs_resp,
            )
            all_errors.extend(case_errors)
            all_anomalies.extend(case_anomalies)

            contraindications = full_response.get("drug_recommendation", {}).get("contraindications", [])
            if isinstance(contraindications, list):
                contra_str = "; ".join(str(x) for x in contraindications)
            else:
                contra_str = str(contraindications)

            hyper_risk = float(full_response.get("hyperglycemia_risk_probability", 0.0))
            row = {
                "case_id": idx,
                "age": patient["age"],
                "weight": patient["weight_kg"],
                "bmi": patient["bmi"],
                "hba1c": patient["hba1c"],
                "glucose": patient["fasting_glucose_mgdl"],
                "creatinine": patient["creatinine_mgdl"],
                "activity": patient["activity_level"],
                "diet_adherence": patient["diet_adherence_score"],
                "prev_dose": patient["previous_insulin_dose_units"],
                "glucose_after": patient["glucose_after_dose_mgdl"],
                "severity": full_response.get("severity"),
                "ml_dose": full_response.get("ml_predicted_dose_units"),
                "recommended_dose": full_response.get("recommended_dose_units"),
                "adjustment_percent": full_response.get("adjustment_percent"),
                "hypo_risk": full_response.get("hypoglycemia_risk_probability"),
                "hyper_risk": hyper_risk,
                "hypo_alert": full_response.get("hypoglycemia_alert"),
                "hyper_alert": bool(hyper_risk > 0.70),
                "was_clamped": full_response.get("safety", {}).get("was_clamped"),
                "primary_therapy": full_response.get("drug_recommendation", {}).get("primary_therapy"),
                "adjunct_drug": full_response.get("drug_recommendation", {}).get("adjunct_drug"),
                "contraindications": contra_str,
                "response_time_ms": round(response_time_ms or 0.0, 2),
                "pass_fail": "PASS" if not case_errors else "FAIL",
            }
            rows.append(row)

    export_results(rows, all_errors)
    print_reports(rows, all_errors, all_anomalies)


if __name__ == "__main__":
    main()
