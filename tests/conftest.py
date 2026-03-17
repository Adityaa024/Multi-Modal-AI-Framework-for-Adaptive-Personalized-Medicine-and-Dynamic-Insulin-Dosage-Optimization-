from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def prediction_payload() -> dict[str, float | int | str | None]:
    return {
        "age": 62,
        "weight_kg": 92,
        "height_cm": 170,
        "bmi": 31.8,
        "fasting_glucose_mgdl": 185,
        "hba1c": 8.6,
        "creatinine_mgdl": 1.2,
        "previous_insulin_dose_units": 18,
        "glucose_after_dose_mgdl": 150,
        "activity_level": 1,
        "diet_adherence_score": 70,
    }


@pytest.fixture(scope="session", autouse=True)
def require_model_artifacts() -> None:
    severity_model = Path("data") / "severity_model.pkl"
    dosage_model = Path("data") / "dosage_model.pkl"
    dataset = Path("data") / "synthetic_t2d_patients.csv"

    missing = [
        p.as_posix() for p in [severity_model, dosage_model, dataset] if not p.exists()
    ]
    if missing:
        pytest.skip(
            f"Required model/data artifacts are missing: {', '.join(missing)}",
            allow_module_level=True,
        )