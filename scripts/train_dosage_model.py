"""Train the engineered XGBoost regressor for insulin dose prediction."""

from __future__ import annotations

import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.services.ml.preprocessing import (
    DOSE_REGRESSION_FEATURE_NAMES,
    build_dose_regression_frame,
)


DATA_PATH = Path("data") / "synthetic_t2d_patients.csv"
MODEL_PATH = Path("data") / "dosage_model.pkl"


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Assemble engineered features used for insulin dose regression."""

    return build_dose_regression_frame(df)


def train_and_evaluate() -> None:
    """Train the XGBoost regressor and report MAE and RMSE."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Synthetic dataset not found at {DATA_PATH}. "
            "Run `scripts/generate_synthetic_t2d_data.py` first."
        )

    df = pd.read_csv(DATA_PATH)

    if "simulated_optimal_insulin_dose_units" not in df.columns:
        raise ValueError(
            "Expected column 'simulated_optimal_insulin_dose_units' not found. "
            "Ensure the dataset was generated with the latest script."
        )

    X = build_feature_matrix(df)
    y = df["simulated_optimal_insulin_dose_units"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = XGBRegressor(
        objective="reg:squarederror",
        learning_rate=0.05,
        n_estimators=500,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )

    feature_weights = np.ones(len(DOSE_REGRESSION_FEATURE_NAMES), dtype=float)
    feature_weights[DOSE_REGRESSION_FEATURE_NAMES.index("previous_insulin_dose_units")] = 3.0

    model.fit(
        X_train,
        y_train,
        feature_weights=feature_weights,
    )

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))

    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as f:
        pickle.dump(
            {
                "model": model,
                "feature_names": DOSE_REGRESSION_FEATURE_NAMES,
                "metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                },
            },
            f,
        )

    print(f"\nSaved trained dosage model to {MODEL_PATH}")


if __name__ == "__main__":
    train_and_evaluate()

