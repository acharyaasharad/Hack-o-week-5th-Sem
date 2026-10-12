"""Interpretation service extracting feature importances, linear coefficients,
and model diagnostics across fitted ensemble and linear pipelines.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import logging

from services.preprocessing_service import PreprocessingService

logger = logging.getLogger(__name__)

class InterpretationService:
    @staticmethod
    def extract_feature_importance(fitted_pipeline) -> Dict[str, Any]:
        """Extracts feature importances (for trees/ensembles) or coefficients (for linear models)."""
        if not fitted_pipeline:
            return {"available": False, "reason": "No model has been fitted yet."}

        preprocessor = fitted_pipeline.named_steps["preprocessing"]
        estimator = fitted_pipeline.named_steps["model"]

        feature_names = PreprocessingService.get_feature_names(preprocessor)
        if not feature_names:
            # Fallback
            feature_names = [f"Feature_{i}" for i in range(10)]

        # 1. Check tree feature_importances_
        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
            ranked = []
            for name, imp in zip(feature_names, importances):
                ranked.append({"feature": name, "importance": float(round(imp, 4))})
            ranked.sort(key=lambda x: x["importance"], reverse=True)
            return {
                "available": True,
                "type": "feature_importance",
                "items": ranked[:20],
                "explanation": "Gini/impurity reduction or split gain in ensemble trees."
            }

        # 2. Check linear coef_
        if hasattr(estimator, "coef_"):
            coefs = np.ravel(estimator.coef_)
            ranked = []
            for name, c in zip(feature_names, coefs):
                ranked.append({"feature": name, "coefficient": float(round(c, 4)), "abs_weight": float(round(abs(c), 4))})
            ranked.sort(key=lambda x: x["abs_weight"], reverse=True)
            return {
                "available": True,
                "type": "coefficients",
                "items": ranked[:20],
                "explanation": "Standardized linear model regression coefficients."
            }

        return {"available": False, "reason": "Model architecture does not expose feature importances."}
