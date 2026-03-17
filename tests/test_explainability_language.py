from __future__ import annotations

from app.services.ml.explainability import _describe_feature


def test_fasting_glucose_contextual_language_ranges() -> None:
    low = _describe_feature("fasting_glucose_mgdl", 70, 0.2)
    near_target = _describe_feature("fasting_glucose_mgdl", 110, 0.2)
    elevated = _describe_feature("fasting_glucose_mgdl", 150, 0.2)
    high = _describe_feature("fasting_glucose_mgdl", 220, 0.2)

    assert "low fasting glucose" in low
    assert "near-target fasting glucose" in near_target
    assert "elevated fasting glucose" in elevated
    assert "high fasting glucose" in high


def test_hba1c_contextual_language_ranges() -> None:
    near_target = _describe_feature("hba1c", 6.8, 0.2)
    suboptimal = _describe_feature("hba1c", 8.0, 0.2)
    poor = _describe_feature("hba1c", 9.4, 0.2)

    assert "near target HbA1c" in near_target
    assert "suboptimally controlled HbA1c" in suboptimal
    assert "poorly controlled HbA1c" in poor
