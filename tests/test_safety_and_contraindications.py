from __future__ import annotations

from typing import Any

import pytest

import app.api.routes.predictions as predictions_route


def test_high_risk_profile_triggers_contraindications(client) -> None:
    payload = {
        "age": 70,
        "weight_kg": 48,
        "height_cm": 170,
        "bmi": 16.6,
        "fasting_glucose_mgdl": 72,
        "hba1c": 9.8,
        "creatinine_mgdl": 1.9,
        "previous_insulin_dose_units": 26,
        "glucose_after_dose_mgdl": 68,
        "activity_level": 0,
        "diet_adherence_score": 45,
        "feature_mode": "full",
    }

    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    contraindications = body["drug_recommendation"]["contraindications"]

    assert body["hypoglycemia_risk_probability"] < 1.0
    assert body["hyperglycemia_risk_probability"] < 1.0
    assert any("Avoid Metformin" in c for c in contraindications)
    assert any("Avoid GLP-1" in c for c in contraindications)
    assert any("Avoid aggressive insulin escalation" in c for c in contraindications)


def test_low_glucose_triggers_hypoglycemia_alert(client, prediction_payload) -> None:
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 72,
        "hba1c": 8.1,
        "creatinine_mgdl": 1.1,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["hypoglycemia_alert"] is True
    assert body["risk_alert"] is True
    assert body["hypoglycemia_risk_probability"] >= 0.30


def test_post_dose_below_70_applies_hypoglycemia_floor_without_alert(
    client,
    prediction_payload,
) -> None:
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 130,
        "glucose_after_dose_mgdl": 65,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["hypoglycemia_risk_probability"] >= 0.60
    assert body["hypoglycemia_risk_probability"] < 0.70
    assert body["hypoglycemia_alert"] is True
    assert body["risk_alert"] is True
    assert "Recent post-dose hypoglycemia signal detected" in body["drug_recommendation"]["explanation"]


def test_post_dose_below_60_applies_hypoglycemia_floor_and_alert(
    client,
    prediction_payload,
) -> None:
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 130,
        "glucose_after_dose_mgdl": 55,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["hypoglycemia_risk_probability"] >= 0.75
    assert body["hypoglycemia_alert"] is True
    assert body["risk_alert"] is True
    assert "Recent post-dose hypoglycemia signal detected" in body["drug_recommendation"]["explanation"]


def test_no_hypoglycemia_alert_for_low_probability_and_safe_post_dose(
    client,
    prediction_payload,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        predictions_route,
        "_compute_risk_probabilities",
        lambda glucose_mgdl, dose_units: (0.05, 0.10),
    )

    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 240,
        "glucose_after_dose_mgdl": 160,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["hypoglycemia_risk_probability"] <= 0.1
    assert body["hypoglycemia_alert"] is False


def test_extreme_low_glucose_triggers_hypoglycemia_alert(client, prediction_payload) -> None:
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 45,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["risk_alert"] is True
    assert body["hypoglycemia_risk_probability"] > 0.70


def test_high_creatinine_overrides_metformin(client, prediction_payload) -> None:
    payload = {
        **prediction_payload,
        "creatinine_mgdl": 1.9,
        "hba1c": 9.6,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    recommendation = body["drug_recommendation"]
    contraindications = recommendation["contraindications"]
    assert any("Avoid Metformin" in c for c in contraindications)
    assert "Metformin" not in recommendation["adjunct_drug"]


def test_no_hypo_contraindication_without_hypo_signals(client, prediction_payload) -> None:
    payload = {
        **prediction_payload,
        "previous_insulin_dose_units": 36.0,
        "glucose_after_dose_mgdl": 140.0,
        "fasting_glucose_mgdl": 240.0,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    contraindications = body["drug_recommendation"]["contraindications"]

    assert body["hypoglycemia_risk_probability"] <= 0.70
    assert payload["glucose_after_dose_mgdl"] >= 70
    assert all(
        "Avoid aggressive insulin escalation" not in item
        for item in contraindications
    )


class _FakeSeverityModel:
    def predict(self, X: list[list[float]]) -> list[int]:
        return [2]

    def predict_proba(self, X: list[list[float]]) -> list[list[float]]:
        return [[0.05, 0.15, 0.8]]


class _FakeDosageModel:
    def predict(self, X) -> list[float]:
        return [120.0]


class _FakeLowDoseModel:
    def predict(self, X) -> list[float]:
        return [0.8]


def _fake_load_pickle_model(path):
    path_str = str(path)
    if "severity_model.pkl" in path_str:
        return {
            "model": _FakeSeverityModel(),
            "class_order": ["Mild", "Moderate", "Severe"],
            "int_to_class": {0: "Mild", 1: "Moderate", 2: "Severe"},
        }
    if "dosage_model.pkl" in path_str:
        return _FakeDosageModel()
    raise FileNotFoundError(path_str)


def _fake_explain_dosage_prediction(**kwargs: Any):
    class _Explanation:
        explanation = "Synthetic explanation for deterministic test."

    return _Explanation()


def test_extreme_prediction_is_capped_to_safe_max(
    client,
    prediction_payload,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(predictions_route, "_load_pickle_model", _fake_load_pickle_model)
    monkeypatch.setattr(
        predictions_route,
        "explain_dosage_prediction",
        _fake_explain_dosage_prediction,
    )

    response = client.post(
        "/api/v1/predictions/predict-dose",
        json={**prediction_payload, "feature_mode": "full"},
    )
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["ml_predicted_dose_units"] == 120.0
    assert body["recommended_dose_units"] == 46.0
    assert body["safety"]["safe_max_units"] == 46.0
    assert body["safe_range"]["max"] == 46.0
    assert body["safety"]["was_clamped"] is True
    assert body["safety"]["within_safe_range"] is True
    assert body["adjustment_percent"] == 0.0
    assert body["adjustment_display"] == "Safety override applied"
    assert isinstance(body["adjustment_explanation"], str)


def test_weight_scaled_minimum_prevents_subphysiologic_dose(client, prediction_payload) -> None:
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 70,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["recommended_dose_units"] >= body["safe_range"]["min"]
    if body["recommended_dose_units"] == body["safe_range"]["min"]:
        assert body["safety"]["within_safe_range"] is True


def test_low_ml_dose_suppresses_adjustment_percentage(
    client,
    prediction_payload,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_lowdose_pickle_model(path):
        path_str = str(path)
        if "severity_model.pkl" in path_str:
            return {
                "model": _FakeSeverityModel(),
                "class_order": ["Mild", "Moderate", "Severe"],
                "int_to_class": {0: "Mild", 1: "Moderate", 2: "Severe"},
            }
        if "dosage_model.pkl" in path_str:
            return _FakeLowDoseModel()
        raise FileNotFoundError(path_str)

    monkeypatch.setattr(predictions_route, "_load_pickle_model", _fake_lowdose_pickle_model)
    monkeypatch.setattr(
        predictions_route,
        "explain_dosage_prediction",
        _fake_explain_dosage_prediction,
    )

    payload = {
        **prediction_payload,
        "weight_kg": 6.0,
        "bmi": 20.8,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["ml_predicted_dose_units"] <= 1.0
    assert body["adjustment_percent"] == 0.0
    assert body["adjustment_display"] == "No adjustment"
    assert body["adjustment_explanation"] is None


def test_drug_recommendation_block_has_explanation(client, prediction_payload) -> None:
    response = client.post(
        "/api/v1/predictions/predict-dose",
        json={**prediction_payload, "feature_mode": "full"},
    )
    assert response.status_code == 200, response.text

    body = response.json()
    recommendation = body["drug_recommendation"]

    assert isinstance(recommendation["primary_therapy"], str)
    assert isinstance(recommendation["adjunct_drug"], str)
    assert isinstance(recommendation["explanation"], str)
    assert len(recommendation["explanation"]) > 20


def test_contraindications_align_with_hypoglycemia_alert(client, prediction_payload) -> None:
    # Trigger hypoglycemia_alert via low fasting glucose (< 80) but keep hypo_prob below 0.70
    payload = {
        **prediction_payload,
        "fasting_glucose_mgdl": 75,
        "glucose_after_dose_mgdl": 130,
        "previous_insulin_dose_units": 10,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["hypoglycemia_alert"] is True
    contraindications = body["drug_recommendation"]["contraindications"]
    assert any("Avoid aggressive insulin escalation" in c for c in contraindications)


def test_sglt2_elderly_aki_contraindication_is_deduplicated(client, prediction_payload) -> None:
    # Age > 65 and Creatinine > 2.0 triggers elderly AKI without duplicating > 1.8 renal warning
    payload = {
        **prediction_payload,
        "age": 72,
        "creatinine_mgdl": 2.3,
        "feature_mode": "full",
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    contraindications = body["drug_recommendation"]["contraindications"]
    sglt2_contras = [c for c in contraindications if "SGLT2" in c]
    # Verify exactly 1 consolidated SGLT2 contraindication is present
    assert len(sglt2_contras) == 1
    assert "high risk of AKI in elderly renal impairment" in sglt2_contras[0]
