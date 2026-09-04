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
    """Train the XGBoost regressor with CV and report MAE and RMSE."""

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

    print(f"Total dataset size: {len(df)}")
    
    # Create train, validation, and test splits (64% train, 16% val, 20% test)
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42
    )

    print(f"Train split size: {len(X_train)} ({(len(X_train)/len(df)):.1%})")
    print(f"Validation split size: {len(X_val)} ({(len(X_val)/len(df)):.1%})")
    print(f"Test split size: {len(X_test)} ({(len(X_test)/len(df)):.1%})")

    from sklearn.model_selection import RandomizedSearchCV
    
    param_grid = {
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [4, 6, 8],
        'n_estimators': [200, 500],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0],
    }

    base_model = XGBRegressor(
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
    )
    
    print("\nStarting Hyperparameter Optimization (3-Fold CV)...")
    search = RandomizedSearchCV(
        base_model,
        param_distributions=param_grid,
        n_iter=5,
        scoring="neg_mean_absolute_error",
        cv=3,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    search.fit(X_train_full, y_train_full)
    
    print(f"Best hyperparameters found: {search.best_params_}")
    
    model = XGBRegressor(
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
        **search.best_params_
    )

    feature_weights = np.ones(len(DOSE_REGRESSION_FEATURE_NAMES), dtype=float)
    feature_weights[DOSE_REGRESSION_FEATURE_NAMES.index("previous_insulin_dose_units")] = 3.0

    # Fit final model with feature weights
    model.fit(
        X_train_full,
        y_train_full,
        feature_weights=feature_weights,
    )

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\nFinal Test Set Metrics:")
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

