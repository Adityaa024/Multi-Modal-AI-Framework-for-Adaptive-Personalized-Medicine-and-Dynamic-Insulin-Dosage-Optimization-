from __future__ import annotations

import pytest


REQUIRED_TOP_LEVEL = {
    "severity",
    "feature_mode",
    "ml_predicted_dose_units",
    "recommended_dose_units",
    "adjustment_percent",
    "adjustment_display",
    "adjustment_explanation",
    "confidence_score",
    "severity_probabilities",
    "uncertainty_entropy",
    "risk_alert",
    "hypoglycemia_alert",
    "hypoglycemia_risk_probability",
    "hyperglycemia_risk_probability",
    "safe_range",
    "safety",
    "drug_recommendation",
}

REQUIRED_DRUG = {
    "primary_therapy",
    "adjunct_drug",
    "contraindications",
    "confidence",
    "explanation",
}

REQUIRED_SAFETY = {
    "safe_min_units",
    "safe_max_units",
    "was_clamped",
    "within_safe_range",
    "exceeds_max_allowed",
    "warning_message",
}


def _assert_predict_response_types(body: dict) -> None:
    assert isinstance(body["severity"], str)
    assert isinstance(body["feature_mode"], str)
    assert isinstance(body["ml_predicted_dose_units"], (int, float))
    assert isinstance(body["recommended_dose_units"], (int, float))
    assert isinstance(body["adjustment_percent"], (int, float))
    assert isinstance(body["adjustment_display"], str)
    assert isinstance(body["adjustment_explanation"], (str, type(None)))
    assert isinstance(body["confidence_score"], (int, float))
    assert isinstance(body["uncertainty_entropy"], (int, float))
    assert isinstance(body["risk_alert"], bool)
    assert isinstance(body["hypoglycemia_alert"], bool)
    assert isinstance(body["hypoglycemia_risk_probability"], (int, float))
    assert isinstance(body["hyperglycemia_risk_probability"], (int, float))

    safe_range = body["safe_range"]
    assert isinstance(safe_range, dict)
    assert {"min", "max"}.issubset(safe_range.keys())
    assert isinstance(safe_range["min"], (int, float))
    assert isinstance(safe_range["max"], (int, float))

    probabilities = body["severity_probabilities"]
    assert isinstance(probabilities, dict)
    assert {"mild", "moderate", "severe"}.issubset(probabilities.keys())
    assert all(isinstance(probabilities[k], (int, float)) for k in ["mild", "moderate", "severe"])

    safety = body["safety"]
    assert isinstance(safety["safe_min_units"], (int, float))
    assert isinstance(safety["safe_max_units"], (int, float))
    assert isinstance(safety["was_clamped"], bool)
    assert isinstance(safety["within_safe_range"], bool)
    assert isinstance(safety["exceeds_max_allowed"], bool)
    assert isinstance(safety["warning_message"], (str, type(None)))

    recommendation = body["drug_recommendation"]
    assert isinstance(recommendation["primary_therapy"], str)
    assert isinstance(recommendation["adjunct_drug"], str)
    assert isinstance(recommendation["contraindications"], list)
    assert isinstance(recommendation["confidence"], (int, float))
    assert isinstance(recommendation["explanation"], str)


@pytest.mark.parametrize("feature_mode", ["full", "structured", "structured_labs"])
def test_predict_dose_contract_by_mode(client, prediction_payload, feature_mode: str) -> None:
    payload = {**prediction_payload, "feature_mode": feature_mode}

    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert REQUIRED_TOP_LEVEL.issubset(body.keys())
    assert REQUIRED_DRUG.issubset(body["drug_recommendation"].keys())
    assert REQUIRED_SAFETY.issubset(body["safety"].keys())
    assert body["feature_mode"] == feature_mode
    _assert_predict_response_types(body)


def test_predict_dose_probability_ranges(client, prediction_payload) -> None:
    response = client.post(
        "/api/v1/predictions/predict-dose",
        json={**prediction_payload, "feature_mode": "full"},
    )
    assert response.status_code == 200, response.text

    body = response.json()
    assert 0.0 <= body["confidence_score"] <= 1.0
    assert 0.0 <= body["uncertainty_entropy"] <= 1.0
    assert 0.0 <= body["hypoglycemia_risk_probability"] <= 1.0
    assert 0.0 <= body["hyperglycemia_risk_probability"] <= 1.0
    assert 0.0 <= body["drug_recommendation"]["confidence"] <= 1.0


def test_predict_dose_exposes_safety_bounds(client, prediction_payload) -> None:
    response = client.post(
        "/api/v1/predictions/predict-dose",
        json={**prediction_payload, "feature_mode": "full"},
    )
    assert response.status_code == 200, response.text

    body = response.json()
    safety = body["safety"]
    assert safety["safe_min_units"] >= 0
    assert safety["safe_max_units"] > safety["safe_min_units"]
    assert body["safe_range"]["min"] == safety["safe_min_units"]
    assert body["safe_range"]["max"] == safety["safe_max_units"]


def test_adjustment_percent_matches_final_numbers(client, prediction_payload) -> None:
    response = client.post(
        "/api/v1/predictions/predict-dose",
        json={**prediction_payload, "feature_mode": "full"},
    )
    assert response.status_code == 200, response.text

    body = response.json()
    ml_dose = float(body["ml_predicted_dose_units"])
    adaptive_dose = float(body["recommended_dose_units"])
    reported_adjustment = float(body["adjustment_percent"])

    if body["adjustment_display"] in {"Safety override applied", "No adjustment"}:
        assert reported_adjustment == 0.0
    else:
        # Check adjustment display mentions the adjustment approach
        assert ("via" in body["adjustment_display"].lower()) or ("adjustment" in body["adjustment_display"].lower())
        assert ml_dose > 1.0
        expected_adjustment = ((adaptive_dose - ml_dose) / ml_dose) * 100.0
        assert reported_adjustment == pytest.approx(expected_adjustment, abs=0.05)