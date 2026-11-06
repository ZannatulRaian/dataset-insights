"""Optional machine learning: train a Linear Regression model."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from backend.services.analyzer import numeric_columns


class PredictionError(Exception):
    pass


def train_model(df: pd.DataFrame, target: str, features: list, test_size: float = 0.2) -> dict:
    num = numeric_columns(df)
    if target not in num:
        raise PredictionError(f"Target '{target}' must be a numeric column.")
    if not features:
        raise PredictionError("Select at least one feature column.")
    for f in features:
        if f not in num:
            raise PredictionError(f"Feature '{f}' must be a numeric column.")
    if target in features:
        raise PredictionError("The target cannot also be a feature.")

    data = df[features + [target]].dropna()
    if len(data) < 10:
        raise PredictionError("Need at least 10 complete rows to train a model.")

    X, y = data[features], data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    model = LinearRegression().fit(X_train, y_train)
    preds = model.predict(X_test)

    sample = [
        {"actual": round(float(a), 3), "predicted": round(float(p), 3)}
        for a, p in list(zip(y_test, preds))[:10]
    ]
    return {
        "target": target,
        "features": features,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mae": round(float(mean_absolute_error(y_test, preds)), 4),
        "r2": round(float(r2_score(y_test, preds)), 4),
        "intercept": round(float(model.intercept_), 4),
        "coefficients": {f: round(float(c), 4) for f, c in zip(features, np.ravel(model.coef_))},
        "sample_predictions": sample,
        "chart": {
            "data": [
                {
                    "type": "scatter",
                    "mode": "markers",
                    "x": [float(v) for v in y_test],
                    "y": [float(v) for v in preds],
                    "name": "Predictions",
                }
            ],
            "layout": {
                "title": "Actual vs predicted",
                "xaxis": {"title": "Actual"},
                "yaxis": {"title": "Predicted"},
            },
        },
    }
