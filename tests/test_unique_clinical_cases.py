from fastapi.testclient import TestClient

def test_fit_but_insulin_resistant(client: TestClient):
    """
    Case 1: The 'Fit but Insulin Resistant' Athlete.
    Normal BMI, high activity, but very high HbA1c and fasting glucose.
    Should be Severe, should NOT recommend lifestyle changes as primary.
    """
    payload = {
        "age": 35,
        "weight_kg": 70,
        "height_cm": 175,
        "bmi": 22.8,
        "fasting_glucose_mgdl": 220,
        "hba1c": 10.5,
        "creatinine_mgdl": 0.9,
        "previous_insulin_dose_units": 15,
        "glucose_after_dose_mgdl": 180,
        "activity_level": 3,
        "diet_adherence_score": 95,
        "feature_mode": "full"
    }
    
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Assertions
    assert data["severity"] == "Severe", "High fasting/HbA1c should force Severe despite healthy lifestyle"
    assert data["recommended_dose_units"] >= 0.3 * payload["weight_kg"], "Severe should have physiological floor of 0.3 * weight"
    assert "lifestyle" not in data["drug_recommendation"]["primary_therapy"].lower(), "Lifestyle shouldn't be primary for Severe"

def test_elderly_renal_hypo_risk(client: TestClient):
    """
    Case 2: Elderly with Renal Impairment & Hypo Risk.
    Age 82, high creatinine (2.8), borderline low fasting glucose (85), high previous dose (40).
    Should escalate to Severe due to renal+age, cap dose downwards for hypo risk, and contraindicate Metformin/SGLT2.
    """
    payload = {
        "age": 82,
        "weight_kg": 85,
        "height_cm": 165,
        "bmi": 31.2,
        "fasting_glucose_mgdl": 85,
        "hba1c": 8.0,
        "creatinine_mgdl": 2.8,
        "previous_insulin_dose_units": 40,
        "glucose_after_dose_mgdl": 80,
        "activity_level": 1,
        "diet_adherence_score": 75,
        "feature_mode": "full"
    }
    
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["severity"] == "Severe", "Renal impairment + age should escalate to Severe"
    assert data["hypoglycemia_alert"] is True, "Elderly with 85 mg/dL fasting should trigger hypo alert"
    assert "metformin" in data["drug_recommendation"]["contraindications"][0].lower() or "sglt2" in data["drug_recommendation"]["contraindications"][0].lower(), "Renal impairment should trigger contraindications"
    assert "Metformin" not in data["drug_recommendation"]["adjunct_drug"]
    assert "SGLT2" not in data["drug_recommendation"]["adjunct_drug"]

def test_newly_diagnosed_acute_spike(client: TestClient):
    """
    Case 3: Newly Diagnosed Acute Hyperglycemic Spike.
    Age 45, insulin-naive (prev=0). Fasting 380, but HbA1c 7.2 (recent spike).
    Should be Severe (glucose >= 200), flag hyper alert, and safely initiate within bounds.
    """
    payload = {
        "age": 45,
        "weight_kg": 100,
        "height_cm": 175,
        "bmi": 32.6,
        "fasting_glucose_mgdl": 380,
        "hba1c": 7.2,
        "creatinine_mgdl": 1.0,
        "previous_insulin_dose_units": 0,
        "glucose_after_dose_mgdl": 380,
        "activity_level": 2,
        "diet_adherence_score": 50,
        "feature_mode": "full"
    }
    
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["severity"] == "Severe", "Fasting >= 200 must be Severe"
    assert data["risk_alert"] is True, "Should flag risk alert for acute spike"
    assert data["recommended_dose_units"] <= 0.5 * payload["weight_kg"], "Initiation must respect 0.5 * weight cap"

def test_brittle_diabetic_overcorrection(client: TestClient):
    """
    Case 4: Brittle Diabetic with Overcorrection (Hypo Rebound).
    Fasting=180, Prev dose=50, Post-dose=55 (severe hypo event).
    Should flag hypoglycemia alert, drastically reduce dose (cap logic), and log safety explanation.
    """
    payload = {
        "age": 55,
        "weight_kg": 90,
        "height_cm": 170,
        "bmi": 31.1,
        "fasting_glucose_mgdl": 180,
        "hba1c": 8.5,
        "creatinine_mgdl": 1.1,
        "previous_insulin_dose_units": 50,
        "glucose_after_dose_mgdl": 55,
        "activity_level": 1,
        "diet_adherence_score": 60,
        "feature_mode": "full"
    }
    
    response = client.post("/api/v1/predictions/predict-dose", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["hypoglycemia_alert"] is True, "Post-dose glucose of 55 must trigger hypo alert"
    assert data["recommended_dose_units"] <= 50 * 0.9, "Must strictly cap the dose due to high hypo risk (0.9 * prev)"
    assert "capped" in data["adjustment_explanation"].lower() or "override" in data["adjustment_explanation"].lower() or "hypoglycemia" in data["adjustment_explanation"].lower() or "stabilize" in data["adjustment_explanation"].lower(), "Explanation must state that dose was capped, overridden, or stabilized"
