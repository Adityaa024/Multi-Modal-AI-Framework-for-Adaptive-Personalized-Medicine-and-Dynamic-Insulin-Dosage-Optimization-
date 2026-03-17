from __future__ import annotations

import pickle
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


MODEL_PATH = Path("data") / "dosage_model.pkl"
client = TestClient(app)


def _predict(payload: dict) -> dict:
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_trained_dosage_model_mae_below_3() -> None:
    assert MODEL_PATH.exists(), "Trained dosage model artifact is missing."

    with MODEL_PATH.open("rb") as f:
        payload = pickle.load(f)

    assert isinstance(payload, dict)
    assert payload["metrics"]["mae"] < 3.0


def test_moderate_profile_predicts_16_to_20_units() -> None:
    payload = {
        "age": 58,
        "weight_kg": 80.0,
        "height_cm": 175.0,
        "bmi": 26.1,
        "fasting_glucose_mgdl": 172.0,
        "hba1c": 7.9,
        "creatinine_mgdl": 1.0,
        "previous_insulin_dose_units": 16.0,
        "glucose_after_dose_mgdl": 168.0,
        "activity_level": 1,
        "diet_adherence_score": 68.0,
        "feature_mode": "full",
    }

    body = _predict(payload)

    assert 16.0 <= float(body["recommended_dose_units"]) <= 20.0
    assert 0.2 * payload["weight_kg"] <= float(body["recommended_dose_units"]) <= 0.6 * payload["weight_kg"]


def test_severe_profile_predicts_22_to_28_units() -> None:
    payload = {
        "age": 64,
        "weight_kg": 95.0,
        "height_cm": 176.0,
        "bmi": 30.7,
        "fasting_glucose_mgdl": 235.0,
        "hba1c": 10.8,
        "creatinine_mgdl": 1.2,
        "previous_insulin_dose_units": 24.0,
        "glucose_after_dose_mgdl": 210.0,
        "activity_level": 1,
        "diet_adherence_score": 48.0,
        "feature_mode": "full",
    }

    body = _predict(payload)

    assert 22.0 <= float(body["recommended_dose_units"]) <= 28.0
    assert 0.2 * payload["weight_kg"] <= float(body["recommended_dose_units"]) <= 0.6 * payload["weight_kg"]