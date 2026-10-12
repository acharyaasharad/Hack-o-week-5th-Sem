"""Regularization service inspecting L1 vs L2 penalties, coefficient shrinkage,
and sparsity in Ridge, Lasso, Logistic Regression, XGBoost, and LightGBM.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import logging

from services.training_service import TrainingService

logger = logging.getLogger(__name__)

class RegularizationService:
    @staticmethod
    def run_regularization_sweep(
        splits: Dict[str, Any],
        model_id: str,
        task: str,
        strength_param: str,
        strengths: List[float],
    ) -> Dict[str, Any]:
        """Sweeps regularization penalty strengths and measures coefficient count and validation scores."""
        training_svc = TrainingService()
        train_scores = []
        val_scores = []
        zero_coef_counts = []

        for s in strengths:
            params = {strength_param: s}
            res = training_svc.train_model(splits=splits, model_id=model_id, task=task, params=params)
            train_scores.append(res["primary_train_score"])
            val_scores.append(res["primary_val_score"])

            # Inspect model coefficients if linear
            estimator = training_svc._last_fitted_pipeline.named_steps["model"]
            if hasattr(estimator, "coef_"):
                coefs = np.ravel(estimator.coef_)
                # Coefficients within epsilon threshold of 0
                n_zero = int(np.sum(np.abs(coefs) < 1e-4))
                zero_coef_counts.append(n_zero)
            else:
                zero_coef_counts.append(None)

        best_idx = int(np.argmax(val_scores))

        return {
            "model_id": model_id,
            "strength_param": strength_param,
            "strengths": strengths,
            "train_scores": train_scores,
            "val_scores": val_scores,
            "zero_coef_counts": zero_coef_counts,
            "best_strength": strengths[best_idx],
            "best_val_score": val_scores[best_idx],
        }
