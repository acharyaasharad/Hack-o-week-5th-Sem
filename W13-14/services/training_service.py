"""Training service executing model fits, evaluations, and arena leaderboards.
Fits preprocessors only on the training split to guarantee leakage prevention.
"""

from typing import Dict, Any, List, Optional
import time
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
import logging

import config
from services.preprocessing_service import PreprocessingService
from services.model_registry import ModelRegistry
from services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

class TrainingService:
    def __init__(self):
        self._last_fitted_pipeline: Optional[Pipeline] = None
        self._last_model_id: Optional[str] = None
        self._last_task: Optional[str] = None
        self._last_target_encoder: Optional[LabelEncoder] = None
        self._leaderboard: List[Dict[str, Any]] = []

    def train_model(
        self,
        splits: Dict[str, Any],
        model_id: str,
        task: str = "classification",
        params: Optional[Dict[str, Any]] = None,
        scaler: str = "standard",
    ) -> Dict[str, Any]:
        """Trains a single model pipeline on the training split and evaluates on validation split."""
        start_time = time.time()
        params = params or {}

        X_train = splits["X_train"]
        y_train = splits["y_train"]
        X_val = splits["X_val"]
        y_val = splits["y_val"]

        # Infer numeric and categorical features
        num_features = list(X_train.select_dtypes(include=[np.number]).columns)
        cat_features = [c for c in X_train.columns if c not in num_features]

        # Scaler logic: tree models do not require scaling
        model_scaler = "none" if model_id in ["decision_tree", "bagging", "random_forest", "gradient_boosting", "xgboost", "lightgbm"] else scaler

        # 1. Build preprocessor
        preprocessor = PreprocessingService.build_preprocessor(
            numeric_features=num_features,
            categorical_features=cat_features,
            scaler=model_scaler,
        )

        # 2. Handle string labels for classification models requiring numeric target (e.g. XGBoost)
        target_encoder = None
        y_train_fit = y_train
        y_val_eval = y_val
        if task == "classification" and y_train.dtype == object:
            target_encoder = LabelEncoder()
            y_train_fit = target_encoder.fit_transform(y_train)
            y_val_eval = target_encoder.transform(y_val)

        # 3. Create estimator & Pipeline
        estimator = ModelRegistry.create_estimator(model_id=model_id, task=task, params=params)
        pipeline = Pipeline([
            ("preprocessing", preprocessor),
            ("model", estimator),
        ])

        # 4. Fit Pipeline
        pipeline.fit(X_train, y_train_fit)
        train_time = float(round(time.time() - start_time, 4))

        # 5. Predict on train and validation
        p_start = time.time()
        y_train_pred = pipeline.predict(X_train)
        y_val_pred = pipeline.predict(X_val)
        pred_time = float(round(time.time() - p_start, 4))

        # Predict probabilities if supported
        y_train_prob = None
        y_val_prob = None
        if task == "classification" and hasattr(pipeline.named_steps["model"], "predict_proba"):
            try:
                y_train_prob = pipeline.predict_proba(X_train)
                y_val_prob = pipeline.predict_proba(X_val)
            except Exception:
                pass

        # 6. Evaluate metrics
        if task == "classification":
            train_metrics = MetricsService.evaluate_classification(y_train_fit, y_train_pred, y_train_prob)
            val_metrics = MetricsService.evaluate_classification(y_val_eval, y_val_pred, y_val_prob)
            gen_gap = float(round(train_metrics["accuracy"] - val_metrics["accuracy"], 4))
            primary_val_score = val_metrics["accuracy"]
            primary_train_score = train_metrics["accuracy"]
        else:
            train_metrics = MetricsService.evaluate_regression(y_train_fit, y_train_pred)
            val_metrics = MetricsService.evaluate_regression(y_val_eval, y_val_pred)
            gen_gap = float(round(train_metrics["r2"] - val_metrics["r2"], 4))
            primary_val_score = val_metrics["r2"]
            primary_train_score = train_metrics["r2"]

        # Cache last fitted pipeline for prediction playground
        self._last_fitted_pipeline = pipeline
        self._last_model_id = model_id
        self._last_task = task
        self._last_target_encoder = target_encoder

        res = {
            "model_id": model_id,
            "task": task,
            "parameters": params,
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "primary_val_score": primary_val_score,
            "primary_train_score": primary_train_score,
            "generalization_gap": gen_gap,
            "train_time_seconds": train_time,
            "pred_time_seconds": pred_time,
            "feature_count": len(X_train.columns),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
        }
        return res

    def compare_arena_models(
        self,
        splits: Dict[str, Any],
        task: str = "classification",
        model_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Trains multiple candidate models across the arena on identical splits."""
        if not model_ids:
            all_models = ModelRegistry.get_supported_models(task=task)
            model_ids = [m["id"] for m in all_models]

        results = []
        for mid in model_ids:
            try:
                res = self.train_model(splits=splits, model_id=mid, task=task)
                results.append(res)
            except Exception as e:
                logger.warning("Arena model %s failed: %s", mid, e)

        # Sort leaderboard: for classification higher accuracy is best, for regression higher R2 is best
        results.sort(key=lambda x: x["primary_val_score"], reverse=True)
        self._leaderboard = results
        return results

    def evaluate_final_test(self, splits: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates the currently selected best model on the strictly held-out test split."""
        if not self._last_fitted_pipeline:
            raise ValueError("No model has been trained yet.")

        X_test = splits["X_test"]
        y_test = splits["y_test"]

        y_test_eval = y_test
        if self._last_target_encoder:
            y_test_eval = self._last_target_encoder.transform(y_test)

        pipeline = self._last_fitted_pipeline
        y_test_pred = pipeline.predict(X_test)

        y_test_prob = None
        if self._last_task == "classification" and hasattr(pipeline.named_steps["model"], "predict_proba"):
            try:
                y_test_prob = pipeline.predict_proba(X_test)
            except Exception:
                pass

        if self._last_task == "classification":
            test_metrics = MetricsService.evaluate_classification(y_test_eval, y_test_pred, y_test_prob)
        else:
            test_metrics = MetricsService.evaluate_regression(y_test_eval, y_test_pred)

        return {
            "model_id": self._last_model_id,
            "task": self._last_task,
            "test_metrics": test_metrics,
            "test_samples": len(X_test),
        }
