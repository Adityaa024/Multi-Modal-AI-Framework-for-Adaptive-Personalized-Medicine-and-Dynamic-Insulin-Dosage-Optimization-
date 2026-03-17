from __future__ import annotations


def test_evaluation_dashboard_contract(client) -> None:
    response = client.get("/api/v1/predictions/evaluation-dashboard")
    assert response.status_code == 200, response.text

    body = response.json()
    for key in [
        "mae",
        "rmse",
        "roc_auc_ovr_macro",
        "roc_curves",
        "confusion_matrix",
        "shap_summary",
    ]:
        assert key in body


def test_evaluation_dashboard_payload_shapes(client) -> None:
    response = client.get("/api/v1/predictions/evaluation-dashboard")
    assert response.status_code == 200, response.text

    body = response.json()

    assert isinstance(body["mae"], (int, float))
    assert isinstance(body["rmse"], (int, float))
    assert isinstance(body["roc_auc_ovr_macro"], (int, float))
    assert body["mae"] >= 0
    assert body["rmse"] >= 0
    assert 0 <= body["roc_auc_ovr_macro"] <= 1

    roc_curves = body["roc_curves"]
    assert isinstance(roc_curves, list)
    assert len(roc_curves) >= 1
    for series in roc_curves:
        assert "label" in series
        assert "fpr" in series and "tpr" in series
        assert isinstance(series["label"], str)
        assert isinstance(series["fpr"], list)
        assert isinstance(series["tpr"], list)
        assert len(series["fpr"]) == len(series["tpr"])

    cm = body["confusion_matrix"]
    assert isinstance(cm["labels"], list)
    assert isinstance(cm["matrix"], list)
    assert len(cm["labels"]) == len(cm["matrix"])
    assert all(isinstance(label, str) for label in cm["labels"])
    assert all(isinstance(row, list) for row in cm["matrix"])

    shap_summary = body["shap_summary"]
    assert isinstance(shap_summary, list)
    assert len(shap_summary) > 0
    for row in shap_summary:
        assert "feature" in row and "mean_abs_shap" in row
        assert isinstance(row["feature"], str)
        assert isinstance(row["mean_abs_shap"], (int, float))
        assert row["mean_abs_shap"] >= 0