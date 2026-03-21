"""
Train a diabetes severity classifier from the synthetic T2D dataset.

Severity classes:
- Mild
- Moderate
- Severe

The labels are derived from HbA1c and fasting glucose using a simple,
transparent rule. An XGBoost classifier is then trained to approximate
this rule (and potentially capture interactions with other covariates).

The trained model is saved as `severity_model.pkl` for downstream use.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


DATA_PATH = Path("data") / "synthetic_t2d_patients.csv"
MODEL_PATH = Path("data") / "severity_model.pkl"


def derive_severity_labels(df: pd.DataFrame) -> pd.Series:
    """
    Derive a discrete diabetes severity label from HbA1c and fasting glucose.

    This rule is intentionally simple, reflecting common clinical thresholds:
    - Mild:   HbA1c < 7.5 and fasting glucose < 140 mg/dL
    - Severe: HbA1c >= 9.5 or fasting glucose >= 200 mg/dL
    - Moderate: all remaining cases

    Returns a categorical series with values: "Mild", "Moderate", "Severe".
    """

    hba1c = df["hba1c"]
    fasting = df["fasting_glucose_mgdl"]

    mild_mask = (hba1c < 7.5) & (fasting < 140)
    severe_mask = (hba1c >= 9.5) | (fasting >= 200)

    labels = np.where(mild_mask, "Mild", "Moderate")
    labels = np.where(severe_mask, "Severe", labels)

    return pd.Series(labels, index=df.index, name="severity")


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select and assemble the feature set used for classification.

    This includes anthropometrics, labs, and lifestyle-related fields
    from the synthetic dataset.
    """

    feature_cols = [
        "age",
        "weight_kg",
        "height_cm",
        "bmi",
        "fasting_glucose_mgdl",
        "hba1c",
        "creatinine_mgdl",
        "previous_insulin_dose_units",
        "glucose_after_dose_mgdl",
        "activity_level",
        "diet_adherence_score",
    ]

    return df[feature_cols].copy()


def train_and_evaluate() -> None:
    """
    Load the synthetic dataset, train an XGBoost classifier, evaluate it,
    and persist the trained model to disk.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Synthetic dataset not found at {DATA_PATH}. "
            "Run `scripts/generate_synthetic_t2d_data.py` first."
        )

    df = pd.read_csv(DATA_PATH)

    y = derive_severity_labels(df)
    X = build_feature_matrix(df)

    # XGBoost's scikit-learn wrapper expects class labels to be numeric.
    class_order = ["Mild", "Moderate", "Severe"]
    class_to_int = {c: i for i, c in enumerate(class_order)}
    int_to_class = {i: c for c, i in class_to_int.items()}
    y_int = y.map(class_to_int).astype(int)

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X,
        y_int,
        test_size=0.2,
        random_state=42,
        stratify=y_int,
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.15,
        random_state=42,
        stratify=y_train_full,
    )

    train_class_counts = np.bincount(y_train, minlength=3)
    total_count = float(train_class_counts.sum())
    class_weights = {
        cls: total_count / (len(train_class_counts) * max(1.0, count))
        for cls, count in enumerate(train_class_counts)
    }
    sample_weight = np.array([class_weights[int(label)] for label in y_train], dtype=float)

    model = XGBClassifier(
        n_estimators=600,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        gamma=0.1,
        reg_alpha=0.2,
        reg_lambda=2.0,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
        num_class=3,
    )

    model.fit(
        X_train,
        y_train,
        sample_weight=sample_weight,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # Predictions and evaluation
    y_pred_int = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    y_test_str = np.array([int_to_class[int(v)] for v in y_test])
    y_pred_str = np.array([int_to_class[int(v)] for v in y_pred_int])

    accuracy = accuracy_score(y_test_str, y_pred_str)
    print(f"Accuracy: {accuracy:.4f}")

    # For ROC-AUC in the multiclass setting, use a one-vs-rest scheme.
    roc_auc = roc_auc_score(
        y_test,
        y_proba,
        multi_class="ovr",
    )
    print(f"ROC-AUC (OvR, macro): {roc_auc:.4f}")

    cm = confusion_matrix(y_test_str, y_pred_str, labels=class_order)
    print("Confusion matrix (rows=true, cols=pred):")
    print(pd.DataFrame(cm, index=class_order, columns=class_order))

    print("\nClassification report:")
    print(classification_report(y_test_str, y_pred_str, target_names=class_order))

    # Persist the trained model.
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump(
            {
                "model": model,
                "class_order": class_order,
                "class_to_int": class_to_int,
                "int_to_class": int_to_class,
            },
            f,
        )

    print(f"\nSaved trained severity model to {MODEL_PATH}")


if __name__ == "__main__":
    train_and_evaluate()

