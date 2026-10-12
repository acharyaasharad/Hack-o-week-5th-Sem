"""Visualization service for building Plotly-compatible payloads:
PCA 2D scatter plots, Elbow curves, Dendrogram calculations (SciPy),
Correlation heatmaps, and Category spending profiles.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, dendrogram
import logging

import config
from services.preprocessing import PreprocessingService

logger = logging.getLogger(__name__)

class VisualizationService:
    @staticmethod
    def compute_correlation_heatmap(df: pd.DataFrame, numeric_features: List[str]) -> Dict[str, Any]:
        """Calculates pairwise Pearson correlation matrix for numeric features."""
        if not numeric_features or len(numeric_features) < 2:
            return {"columns": [], "z": []}

        sub_df = df[numeric_features].dropna()
        corr_matrix = sub_df.corr(method="pearson")

        # Round values
        z_vals = [[float(round(val, 3)) for val in row] for row in corr_matrix.values]

        return {
            "columns": list(corr_matrix.columns),
            "z": z_vals,
        }

    @staticmethod
    def compute_dendrogram_data(
        df: pd.DataFrame,
        numeric_features: List[str],
        categorical_features: Optional[List[str]] = None,
        linkage_method: str = "ward",
        metric: str = "euclidean",
        max_rows: int = config.MAX_DENDROGRAM_ROWS,
        scaling_method: str = "standard",
        log_transform: bool = False,
    ) -> Dict[str, Any]:
        """Calculates hierarchical linkage tree and dendrogram coordinates using SciPy.
        Imposes a strict row-count guard to protect server and browser performance.
        """
        n_rows = len(df)
        if n_rows > max_rows:
            return {
                "available": False,
                "reason": (
                    f"Dataset contains {n_rows} rows, exceeding the safe dendrogram limit of {max_rows} records. "
                    "Hierarchical tree calculation requires quadratic O(N^2) memory and rendering. "
                    "Please filter the dataset or rely on Agglomerative cluster labels."
                )
            }

        # Ward requires euclidean metric
        if linkage_method == "ward":
            metric = "euclidean"

        try:
            # Preprocess features
            preprocessor, _ = PreprocessingService.create_preprocessor(
                numeric_features=numeric_features,
                categorical_features=categorical_features,
                scaling_method=scaling_method,
                log_transform=log_transform,
            )

            cols = numeric_features + (categorical_features or [])
            X_df = df[cols].copy()
            X_trans = preprocessor.fit_transform(X_df)

            # Compute linkage matrix
            Z = linkage(X_trans, method=linkage_method, metric=metric)

            # Compute dendrogram leaf coordinates (truncate mode for clean visuals)
            dendro = dendrogram(Z, no_plot=True, truncate_mode="lastp", p=30)

            return {
                "available": True,
                "icoord": dendro["icoord"],
                "dcoord": dendro["dcoord"],
                "ivl": dendro["ivl"],
                "leaves": [int(l) for l in dendro["leaves"]],
                "color_list": dendro["color_list"],
                "linkage_method": linkage_method,
                "metric": metric,
                "leaf_count": len(dendro["leaves"]),
            }
        except Exception as e:
            logger.error("Dendrogram calculation failed: %s", e)
            return {"available": False, "reason": f"Dendrogram computation failed: {str(e)}"}
