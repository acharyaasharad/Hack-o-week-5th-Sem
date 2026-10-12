"""Evaluation service for calculating dimensionality reduction metrics:
PCA explained variance, reconstruction error, and scikit-learn trustworthiness.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.manifold import trustworthiness
import logging

logger = logging.getLogger(__name__)

class EvaluationService:
    @staticmethod
    def compute_trustworthiness(
        X_high: np.ndarray,
        X_embedded: np.ndarray,
        n_neighbors: int = 5
    ) -> Optional[float]:
        """Calculates neighborhood trustworthiness between high-dim and 2D embedding.
        Trustworthiness ranges from 0 to 1 (1 indicates perfect preservation of local ranks).
        Requires sample size > 2 * n_neighbors + 1.
        """
        n_samples = len(X_high)
        if n_samples <= 2 * n_neighbors + 1:
            return None

        try:
            score = trustworthiness(X_high, X_embedded, n_neighbors=n_neighbors)
            return float(round(score, 4))
        except Exception as e:
            logger.warning("Trustworthiness calculation failed: %s", e)
            return None

    @staticmethod
    def compute_reconstruction_error(
        X_original_scaled: np.ndarray,
        X_reconstructed_scaled: np.ndarray
    ) -> float:
        """Computes Mean Squared Reconstruction Error in transformed feature space."""
        diff = X_original_scaled - X_reconstructed_scaled
        mse = np.mean(np.square(diff))
        return float(round(mse, 4))
