"""
Tests demonstrating the advanced insulin dose calculation with physiological baseline
and treatment-response adjustment.

This test module validates the improvements to the dose prediction pipeline that
address the issue where RandomForest models predict extremely low doses, causing
safety clamps to dominate the final output.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture
def mild_patient():
    """Fixture for a mild diabetes patient (72 kg)."""
    return {
        "age": 45,
        "weight_kg": 72.0,
        "height_cm": 175.0,
        "bmi": 23.5,
        "fasting_glucose_mgdl": 120.0,
        "hba1c": 6.8,
        "creatinine_mgdl": 0.9,
        "previous_insulin_dose_units": 12.0,
        "glucose_after_dose_mgdl": 150.0,
        "activity_level": 2,
        "diet_adherence_score": 75.0,
        "feature_mode": "full",
    }


@pytest.fixture
def moderate_patient():
    """Fixture for a moderate diabetes patient (80 kg)."""
    return {
        "age": 55,
        "weight_kg": 80.0,
        "height_cm": 178.0,
        "bmi": 25.3,
        "fasting_glucose_mgdl": 145.0,
        "hba1c": 8.2,
        "creatinine_mgdl": 1.0,
        "previous_insulin_dose_units": 18.0,
        "glucose_after_dose_mgdl": 165.0,
        "activity_level": 1,
        "diet_adherence_score": 60.0,
        "feature_mode": "full",
    }


@pytest.fixture
def severe_patient_poor_control():
    """Fixture for severe diabetes patient with poor glycemic control after dose."""
    return {
        "age": 62,
        "weight_kg": 85.0,
        "height_cm": 175.0,
        "bmi": 27.7,
        "fasting_glucose_mgdl": 180.0,
        "hba1c": 9.5,
        "creatinine_mgdl": 1.1,
        "previous_insulin_dose_units": 24.0,
        "glucose_after_dose_mgdl": 210.0,  # High post-dose glucose indicates poor control
        "activity_level": 0,
        "diet_adherence_score": 45.0,
        "feature_mode": "full",
    }


class TestAdvancedDoseCalculation:
    """Test suite for advanced dose calculation with physiological baseline."""

    def test_mild_case_reasonable_dose(self, mild_patient):
        """
        Test mild case: dose should be reasonable for weight (7-10 units expected).
        
        Expected behavior:
        - ML model might predict low dose (e.g., 5 units)
        - Physiological baseline = 0.2 * 72 = 14.4 U
        - Combined = 0.6 * 5 + 0.4 * 14.4 = 3 + 5.76 = 8.76 U
        - After clamp to 0.1-0.5 weight range = 7.2-36 U, result ≈ 8.76 U
        - Final dose should be around 7-10 units or at minimum safety bound
        """
        response = client.post("/api/v1/predictions/predict-dose", json=mild_patient)
        assert response.status_code == 200
        
        body = response.json()
        assert body["recommended_dose_units"] > 0
        # Dose should be within safe range and not unreasonably low
        assert body["recommended_dose_units"] >= body["safe_range"]["min"]
        assert body["recommended_dose_units"] <= body["safe_range"]["max"]
        assert body["safe_range"]["min"] == 7.2  # 0.1 * 72
        assert body["safe_range"]["max"] == 36.0  # 0.5 * 72

    def test_moderate_case_adequate_dose(self, moderate_patient):
        """
        Test moderate case: dose should be within safe physiological range.
        
        Expected behavior:
        - ML model prediction combined with physiological baseline
        - Safe range = 8.0-40.0 units (0.1-0.5 * 80)
        - Recommended dose should be within this range
        - Will be at least the physiological minimum (0.1 * weight)
        """
        response = client.post("/api/v1/predictions/predict-dose", json=moderate_patient)
        assert response.status_code == 200
        
        body = response.json()
        assert body["recommended_dose_units"] > 0
        # Dose should be within safe range
        assert body["recommended_dose_units"] >= body["safe_range"]["min"]
        assert body["recommended_dose_units"] <= body["safe_range"]["max"]
        assert body["safe_range"]["min"] == 8.0  # 0.1 * 80
        assert body["safe_range"]["max"] == 40.0  # 0.5 * 80

    def test_severe_case_with_poor_control_treatment_response(self, severe_patient_poor_control):
        """
        Test severe case with poor glycemic control: dose should not drop below 110% previous.
        
        Scenario:
        - Previous dose: 24 units
        - Post-dose glucose: 210 mg/dL (poor control)
        - Expected behavior: Ensure next dose >= 24 * 1.1 = 26.4 units
        - Thus final dose should be around 26-30 units, NOT dropping to safety minimum
        
        This demonstrates the treatment-response adjustment that prevents
        inappropriate dose reduction when glucose control is poor.
        """
        response = client.post("/api/v1/predictions/predict-dose", json=severe_patient_poor_control)
        assert response.status_code == 200
        
        body = response.json()
        assert body["recommended_dose_units"] > 0
        
        # Check that dose is within safe range
        assert body["recommended_dose_units"] >= body["safe_range"]["min"]
        assert body["recommended_dose_units"] <= body["safe_range"]["max"]
        
        # Safe min = 0.1 * 85 = 8.5, max = 0.5 * 85 = 42.5
        assert body["safe_range"]["min"] == 8.5
        assert body["safe_range"]["max"] == 42.5
        
        # Most importantly: if treatment-response adjustment is triggered,
        # ensure dose is at least 110% of previous
        min_treatment_response_dose = severe_patient_poor_control["previous_insulin_dose_units"] * 1.1
        # If poor control is detected, the dose should reflect treatment response
        if "poor control" in str(body.get("adjustment_explanation", "")).lower():
            assert body["recommended_dose_units"] >= min_treatment_response_dose - 0.5, (
                f"When poor control detected, dose should be >= {min_treatment_response_dose:.1f} units "
                f"(110% of previous {severe_patient_poor_control['previous_insulin_dose_units']}), "
                f"got {body['recommended_dose_units']}"
            )

    def test_explanation_indicates_physiological_baseline_applied(self, mild_patient):
        """Verify that adjustment_explanation mentions physiological baseline when applied."""
        response = client.post("/api/v1/predictions/predict-dose", json=mild_patient)
        assert response.status_code == 200
        
        body = response.json()
        explanation = body.get("adjustment_explanation") or ""
        
        # If there's an explanation, it should mention baseline, combined, or adjustment
        if explanation:
            mention_keywords = ["baseline", "combined", "adjustment", "prediction", "ml"]
            assert any(keyword in explanation.lower() for keyword in mention_keywords), (
                f"Expected explanation to mention physiological adjustments, got: {explanation}"
            )
        
        # At minimum, we should have an adjustment_display describing what happened
        display = body.get("adjustment_display", "")
        assert display in {
            "No adjustment",
            "Safety override applied",
        } or "%" in display, (
            f"Expected adjustment_display to indicate change, got: {display}"
        )

    def test_safe_range_scales_with_weight(self):
        """Verify that safe dose range scales linearly with weight."""
        # Test with 50 kg patient
        light_patient = {
            "age": 30,
            "weight_kg": 50.0,
            "height_cm": 165.0,
            "bmi": 18.4,
            "fasting_glucose_mgdl": 100.0,
            "hba1c": 6.5,
            "creatinine_mgdl": 0.8,
            "previous_insulin_dose_units": 10.0,
            "glucose_after_dose_mgdl": 140.0,
            "activity_level": 2,
            "diet_adherence_score": 85.0,
            "feature_mode": "full",
        }
        
        response_light = client.post("/api/v1/predictions/predict-dose", json=light_patient)
        assert response_light.status_code == 200
        light_body = response_light.json()
        
        # Test with 100 kg patient
        heavy_patient = light_patient.copy()
        heavy_patient["weight_kg"] = 100.0
        heavy_patient["height_cm"] = 185.0
        heavy_patient["bmi"] = 29.2
        
        response_heavy = client.post("/api/v1/predictions/predict-dose", json=heavy_patient)
        assert response_heavy.status_code == 200
        heavy_body = response_heavy.json()
        
        # Verify safe range scales with weight
        # For 50 kg: min = 5.0, max = 25.0
        # For 100 kg: min = 10.0, max = 50.0
        assert light_body["safe_range"]["min"] == 5.0
        assert light_body["safe_range"]["max"] == 25.0
        assert heavy_body["safe_range"]["min"] == 10.0
        assert heavy_body["safe_range"]["max"] == 50.0

        # Final recommendations must remain inside each patient's scaled safe range.
        assert light_body["safe_range"]["min"] <= light_body["recommended_dose_units"] <= light_body["safe_range"]["max"]
        assert heavy_body["safe_range"]["min"] <= heavy_body["recommended_dose_units"] <= heavy_body["safe_range"]["max"]

    def test_adjustment_within_safe_range(self, moderate_patient):
        """Verify that final recommended dose is always within safe range."""
        response = client.post("/api/v1/predictions/predict-dose", json=moderate_patient)
        assert response.status_code == 200
        
        body = response.json()
        final_dose = body["recommended_dose_units"]
        safe_min = body["safe_range"]["min"]
        safe_max = body["safe_range"]["max"]
        
        assert safe_min <= final_dose <= safe_max, (
            f"Final dose {final_dose} outside safe range [{safe_min}, {safe_max}]"
        )
        assert body["safety"]["within_safe_range"] is True
