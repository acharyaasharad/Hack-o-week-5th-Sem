"""Generalization service analyzing the bias-variance trade-off,
model complexity sweeps, learning curves, and synthetic polynomial overfitting demonstrations.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
import logging

import config
from services.training_service import TrainingService

logger = logging.getLogger(__name__)

class GeneralizationService:
    @staticmethod
    def run_complexity_sweep(
        splits: Dict[str, Any],
        model_id: str,
        task: str,
        param_name: str,
        param_values: List[Any],
    ) -> Dict[str, Any]:
        """Sweeps a single complexity parameter (e.g. max_depth, n_estimators) to plot train vs val curves."""
        training_svc = TrainingService()
        train_scores = []
        val_scores = []
        gaps = []

        for val in param_values:
            params = {param_name: val}
            res = training_svc.train_model(splits=splits, model_id=model_id, task=task, params=params)
            train_scores.append(res["primary_train_score"])
            val_scores.append(res["primary_val_score"])
            gaps.append(res["generalization_gap"])

        # Determine best validation index
        best_idx = int(np.argmax(val_scores))
        best_val = param_values[best_idx]

        # Diagnostic heuristic
        diagnosis = "Optimal Generalization: Model reaches balanced performance with minimal generalization gap."
        if gaps[-1] > gaps[0] and val_scores[-1] < val_scores[best_idx]:
            diagnosis = "Overfitting Detected: As model complexity increases, training performance rises while validation score degrades."
        elif val_scores[0] < 0.5 and val_scores[-1] < 0.5:
            diagnosis = "Underfitting Tendency: Both training and validation scores remain subdued across tested parameter range."

        return {
            "model_id": model_id,
            "param_name": param_name,
            "param_values": param_values,
            "train_scores": train_scores,
            "val_scores": val_scores,
            "generalization_gaps": gaps,
            "best_parameter_value": best_val,
            "best_val_score": val_scores[best_idx],
            "diagnostic_insight": diagnosis,
        }

    @staticmethod
    def run_synthetic_demo() -> Dict[str, Any]:
        """Generates noisy sinusoidal regression data and fits Degree 1, Degree 4, and Degree 12 polynomials."""
        np.random.seed(42)
        n_points = 50
        x = np.sort(np.random.uniform(0, 1, n_points))
        # Ground truth function
        y_true = np.sin(2 * np.pi * x)
        y = y_true + np.random.normal(0, 0.25, n_points)

        # Train / val split (80/20)
        idx_train = np.arange(0, n_points, 2)
        idx_val = np.arange(1, n_points, 2)

        x_train, y_train = x[idx_train].reshape(-1, 1), y[idx_train]
        x_val, y_val = x[idx_val].reshape(-1, 1), y[idx_val]

        x_dense = np.linspace(0, 1, 150).reshape(-1, 1)

        degrees = [1, 4, 12]
        models_data = []

        for d in degrees:
            pipe = Pipeline([
                ("poly", PolynomialFeatures(degree=d, include_bias=False)),
                ("linear", LinearRegression())
            ])
            pipe.fit(x_train, y_train)

            train_pred = pipe.predict(x_train)
            val_pred = pipe.predict(x_val)
            dense_pred = pipe.predict(x_dense)

            train_rmse = float(round(root_mean_squared_error(y_train, train_pred), 3))
            val_rmse = float(round(root_mean_squared_error(y_val, val_pred), 3))

            label = "Degree 1 (Underfitting / High Bias)" if d == 1 else (
                "Degree 4 (Balanced / Optimal)" if d == 4 else "Degree 12 (Overfitting / High Variance)"
            )

            models_data.append({
                "degree": d,
                "label": label,
                "train_rmse": train_rmse,
                "val_rmse": val_rmse,
                "curve_y": [float(round(val, 3)) for val in dense_pred],
            })

        return {
            "x_train": [float(round(val, 3)) for val in x_train.flatten()],
            "y_train": [float(round(val, 3)) for val in y_train],
            "x_val": [float(round(val, 3)) for val in x_val.flatten()],
            "y_val": [float(round(val, 3)) for val in y_val],
            "x_dense": [float(round(val, 3)) for val in x_dense.flatten()],
            "models": models_data,
        }
