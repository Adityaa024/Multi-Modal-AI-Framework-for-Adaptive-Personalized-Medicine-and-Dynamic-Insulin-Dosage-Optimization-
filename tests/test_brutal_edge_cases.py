import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extreme_hypoglycemia_risk():
    payload = {
        "age": 95,
        "weight_kg": 45,
        "height_cm": 150,
        "bmi": 20.0,
        "fasting_glucose_mgdl": 50,
        "hba1c": 6.5,
        "creatinine_mgdl": 4.5,
        "previous_insulin_dose_units": 60,
        "glucose_after_dose_mgdl": 45,
        "activity_level": 1,
        "diet_adherence_score": 20,
        "feature_mode": "full"
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["hypoglycemia_alert"] is True, "Glucose of 45 must trigger hypoglycemia alert"
    # Dose should be clamped due to low weight (45kg * 0.1 = 4.5U or similar) and severe hypo risk
    assert data["recommended_dose_units"] <= 15.0, "Dose should be clamped heavily for low weight and extreme hypo risk"

def test_extreme_hyperglycemia_risk():
    payload = {
        "age": 25,
        "weight_kg": 150,
        "height_cm": 160,
        "bmi": 58.6,
        "fasting_glucose_mgdl": 600,
        "hba1c": 15.0,
        "creatinine_mgdl": 0.5,
        "previous_insulin_dose_units": 0,
        "glucose_after_dose_mgdl": 600,
        "activity_level": 1,
        "diet_adherence_score": 10,
        "feature_mode": "full"
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["severity"] == "Severe", "Glucose of 600 must trigger Severe severity"
    assert data["risk_alert"] is True, "Must trigger risk alert"
    # Dose should be clamped to weight max (150 * 0.5 = 75U)
    assert data["recommended_dose_units"] <= 75.0, "Dose must not exceed ADA upper bound for weight (75U)"

def test_missing_or_invalid_fields():
    # Attempting to send completely invalid payload missing required fields
    payload = {
        "age": "invalid_string",
        "weight_kg": -10,
        "feature_mode": "unknown_mode"
    }
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    # FastAPI/Pydantic should return 422 Unprocessable Entity
    assert response.status_code == 422
