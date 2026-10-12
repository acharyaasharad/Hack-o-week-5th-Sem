"""Metrics service computing classification and regression metrics and confusion matrices.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
)
import logging

logger = logging.getLogger(__name__)

class MetricsService:
    @staticmethod
    def evaluate_classification(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Calculates accuracy, balanced accuracy, precision, recall, F1, and ROC-AUC."""
        metrics = {
            "accuracy": float(round(accuracy_score(y_true, y_pred), 4)),
            "balanced_accuracy": float(round(balanced_accuracy_score(y_true, y_pred), 4)),
            "precision": float(round(precision_score(y_true, y_pred, average="weighted", zero_division=0), 4)),
            "recall": float(round(recall_score(y_true, y_pred, average="weighted", zero_division=0), 4)),
            "f1": float(round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 4)),
            "roc_auc": None,
        }

        # Calculate ROC-AUC if probability estimates are provided
        if y_prob is not None:
            try:
                unique_classes = np.unique(y_true)
                if len(unique_classes) == 2:
                    # Binary classification
                    # If y_prob is 2D, take positive class column
                    prob_col = y_prob[:, 1] if (len(y_prob.shape) == 2 and y_prob.shape[1] == 2) else y_prob
                    auc = roc_auc_score(y_true, prob_col)
                    metrics["roc_auc"] = float(round(auc, 4))
                elif len(unique_classes) > 2 and len(y_prob.shape) == 2:
                    auc = roc_auc_score(y_true, y_prob, multi_class="ovr")
                    metrics["roc_auc"] = float(round(auc, 4))
            except Exception as e:
                logger.warning("ROC-AUC computation skipped: %s", e)

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred)
        unique_labels = [str(c) for c in np.unique(y_true)]
        metrics["confusion_matrix"] = {
            "labels": unique_labels,
            "matrix": cm.tolist(),
        }

        return metrics

    @staticmethod
    def evaluate_regression(
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Calculates MAE, RMSE, and R2 score for regression tasks."""
        mae = float(round(mean_absolute_error(y_true, y_pred), 3))
        rmse = float(round(root_mean_squared_error(y_true, y_pred), 3))
        r2 = float(round(r2_score(y_true, y_pred), 4))

        # Residuals
        residuals = (y_true - y_pred).tolist()

        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "residuals_summary": {
                "mean_residual": float(round(np.mean(residuals), 3)),
                "std_residual": float(round(np.std(residuals), 3)),
            }
        }
