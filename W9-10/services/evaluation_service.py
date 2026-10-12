"""Evaluation service for calculating unsupervised clustering metrics:
Silhouette Score, Davies–Bouldin Index, and Calinski–Harabasz Score.
Includes safeguards for singleton clusters, all-noise DBSCAN, and undefined metrics.
"""

from typing import Dict, Any, List, Optional
import time
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import logging

logger = logging.getLogger(__name__)

class EvaluationService:
    @staticmethod
    def evaluate_clustering(
        X_transformed: np.ndarray,
        labels: np.ndarray,
        algorithm: str = "kmeans"
    ) -> Dict[str, Any]:
        """Calculates clustering metrics safely.
        Returns explicit None / null for undefined metric states rather than arbitrary zeros.
        """
        n_samples = len(labels)
        unique_labels = np.unique(labels)
        
        # Check for noise points (label -1, typical of DBSCAN)
        is_noise = (labels == -1)
        noise_count = int(np.sum(is_noise))
        noise_pct = float(round((noise_count / n_samples) * 100, 2)) if n_samples > 0 else 0.0

        # Non-noise clusters
        non_noise_labels = [label for label in unique_labels if label != -1]
        n_clusters = len(non_noise_labels)

        # Cluster sizes
        cluster_sizes = {}
        for l in unique_labels:
            key = "Noise (-1)" if l == -1 else f"Cluster {l}"
            cluster_sizes[key] = int(np.sum(labels == l))

        warnings = []
        metrics = {
            "silhouette_score": None,
            "davies_bouldin_index": None,
            "calinski_harabasz_score": None,
        }

        # Subsetting for DBSCAN metrics: compute on non-noise points if noise is present
        if noise_count > 0:
            eval_mask = ~is_noise
            X_eval = X_transformed[eval_mask]
            labels_eval = labels[eval_mask]
            eval_samples = len(labels_eval)
            warnings.append(
                f"Evaluation metrics computed on {eval_samples}/{n_samples} non-noise points "
                f"({100 - noise_pct:.1f}% coverage). Noise points (-1) were excluded from score calculation."
            )
        else:
            X_eval = X_transformed
            labels_eval = labels
            eval_samples = n_samples

        # Guard: At least 2 clusters and strictly fewer clusters than evaluation samples
        unique_eval_labels = np.unique(labels_eval) if eval_samples > 0 else []
        n_eval_clusters = len(unique_eval_labels)

        if n_eval_clusters < 2:
            warnings.append(
                f"Only {n_eval_clusters} usable cluster discovered. "
                "Silhouette, Davies-Bouldin, and Calinski-Harabasz metrics require at least 2 distinct clusters."
            )
            return {
                "n_clusters": n_clusters,
                "noise_count": noise_count,
                "noise_percentage": noise_pct,
                "evaluated_samples": eval_samples,
                "cluster_sizes": cluster_sizes,
                "metrics": metrics,
                "warnings": warnings,
            }

        if n_eval_clusters >= eval_samples:
            warnings.append("Cluster count equals or exceeds sample count; metric calculation undefined.")
            return {
                "n_clusters": n_clusters,
                "noise_count": noise_count,
                "noise_percentage": noise_pct,
                "evaluated_samples": eval_samples,
                "cluster_sizes": cluster_sizes,
                "metrics": metrics,
                "warnings": warnings,
            }

        # 1. Silhouette Score
        try:
            sil = silhouette_score(X_eval, labels_eval)
            metrics["silhouette_score"] = float(round(sil, 4))
        except Exception as e:
            logger.warning("Silhouette calculation failed: %s", e)
            warnings.append(f"Silhouette score could not be calculated: {str(e)}")

        # 2. Davies-Bouldin Index
        try:
            db = davies_bouldin_score(X_eval, labels_eval)
            metrics["davies_bouldin_index"] = float(round(db, 4))
        except Exception as e:
            logger.warning("Davies-Bouldin calculation failed: %s", e)
            warnings.append(f"Davies-Bouldin index could not be calculated: {str(e)}")

        # 3. Calinski-Harabasz Score
        try:
            ch = calinski_harabasz_score(X_eval, labels_eval)
            metrics["calinski_harabasz_score"] = float(round(ch, 2))
        except Exception as e:
            logger.warning("Calinski-Harabasz calculation failed: %s", e)
            warnings.append(f"Calinski-Harabasz score could not be calculated: {str(e)}")

        return {
            "n_clusters": n_clusters,
            "noise_count": noise_count,
            "noise_percentage": noise_pct,
            "evaluated_samples": eval_samples,
            "cluster_sizes": cluster_sizes,
            "metrics": metrics,
            "warnings": warnings,
        }
