"""Profiling service for customer clusters.
Calculates statistical profiles (mean, median, sum, proportions) in original monetary units,
computes Channel/Region distributions, and dynamically generates interpretable descriptions
and suggested business actions based on empirical spending patterns.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ProfilingService:
    @staticmethod
    def generate_cluster_profiles(
        df: pd.DataFrame,
        labels: np.ndarray,
        numeric_features: List[str],
        context_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Profiles clusters strictly using original raw feature values."""
        df_copy = df.copy()
        df_copy["_cluster"] = labels

        total_customers = len(df_copy)
        unique_labels = sorted(list(np.unique(labels)))

        # Dataset overall averages for relative comparisons
        overall_means = df_copy[numeric_features].mean().to_dict()
        overall_medians = df_copy[numeric_features].median().to_dict()

        profiles = {}
        for l in unique_labels:
            cluster_df = df_copy[df_copy["_cluster"] == l]
            cluster_size = len(cluster_df)
            pct = float(round((cluster_size / total_customers) * 100, 2))
            is_noise = bool(l == -1)

            # Feature statistics in original units
            means = {col: float(round(cluster_df[col].mean(), 2)) for col in numeric_features}
            medians = {col: float(round(cluster_df[col].median(), 2)) for col in numeric_features}
            sums = {col: float(round(cluster_df[col].sum(), 2)) for col in numeric_features}

            # Relative spending index: (cluster_mean / overall_mean)
            relative_index = {}
            for col in numeric_features:
                base = overall_means.get(col, 1.0)
                relative_index[col] = float(round(means[col] / base, 2)) if base > 0 else 1.0

            # Context columns distribution (e.g. Channel & Region)
            context_dist = {}
            if context_columns:
                for ctx in context_columns:
                    if ctx in cluster_df.columns:
                        counts = cluster_df[ctx].value_counts().to_dict()
                        context_dist[ctx] = {str(k): int(v) for k, v in counts.items()}

            # Dynamic heuristic interpretation and business suggestion
            description, suggestions = ProfilingService._derive_interpretation(
                cluster_label=l,
                is_noise=is_noise,
                relative_index=relative_index,
                means=means,
                context_dist=context_dist
            )

            cluster_key = "Noise (-1)" if is_noise else f"Cluster {l}"
            profiles[cluster_key] = {
                "cluster_id": int(l),
                "is_noise": bool(is_noise),
                "customer_count": cluster_size,
                "percentage_of_total": pct,
                "means": means,
                "medians": medians,
                "sums": sums,
                "relative_index": relative_index,
                "context_distributions": context_dist,
                "derived_description": description,
                "suggested_actions": suggestions,
            }

        return {
            "total_customers": total_customers,
            "overall_means": {k: float(round(v, 2)) for k, v in overall_means.items()},
            "overall_medians": {k: float(round(v, 2)) for k, v in overall_medians.items()},
            "clusters": profiles,
        }

    @staticmethod
    def _derive_interpretation(
        cluster_label: int,
        is_noise: bool,
        relative_index: Dict[str, float],
        means: Dict[str, float],
        context_dist: Dict[str, Any]
    ) -> (str, List[str]):
        """Generates statistical heuristic interpretations from empirical spending ratios."""
        if is_noise:
            return (
                "Outliers & Noise Points: Observations marked by DBSCAN that do not satisfy "
                "density criteria with respect to neighboring points. Often represent rare purchase "
                "anomalies or very high spenders with unique profiles.",
                [
                    "Examine individual rows manually for data entry errors or VIP client behavior.",
                    "Do not target as a unified commercial persona, as points do not share high mutual density."
                ]
            )

        # Identify high categories (relative index >= 1.3)
        high_cats = [col for col, idx in relative_index.items() if idx >= 1.3]
        low_cats = [col for col, idx in relative_index.items() if idx <= 0.7]

        # Top dominant spend category
        sorted_by_spend = sorted(means.items(), key=lambda x: x[1], reverse=True)
        top_cat = sorted_by_spend[0][0] if sorted_by_spend else "General"

        desc_parts = []
        suggestions = []

        if len(high_cats) >= 3 and all(idx >= 1.2 for idx in relative_index.values()):
            desc_parts.append("High-Volume Multi-Category Buyers: Substantially above-average purchasing across almost all spending categories.")
            suggestions.append("Prioritize account management and premium wholesale logistics contracts.")
            suggestions.append("Offer volume tier discounts and cross-category bulk incentives.")
        elif set(["Grocery", "Milk", "Detergents_Paper"]).issubset(set(high_cats)):
            desc_parts.append("Retail & Grocery Dominant Profile: Characterized by heavy spending on Grocery, Milk, and Detergents/Paper.")
            suggestions.append("Ideal segment for supermarket and convenience store replenishment programs.")
            suggestions.append("Bundle paper goods and dairy product promotions.")
        elif set(["Fresh", "Frozen"]).issubset(set(high_cats)):
            desc_parts.append("Fresh & Perishables Focused (HoReCa): Significant spending on Fresh produce and Frozen goods.")
            suggestions.append("Target with cold-chain delivery reliability and fresh farm-to-table supply contracts.")
            suggestions.append("Frequent replenishment scheduling to reduce spoilage risk.")
        elif len(high_cats) == 1:
            desc_parts.append(f"Specialized {high_cats[0]} Buyers: Purchasing profile strongly dominated by {high_cats[0]} goods.")
            suggestions.append(f"Focus sales campaigns on {high_cats[0]} inventory depth and bulk pricing.")
        elif len(low_cats) >= 4:
            desc_parts.append("Modest / Low-Volume Buyers: Below-average spending across most tracked wholesale categories.")
            suggestions.append("Assess minimum order size constraints or automated ordering portals to reduce servicing costs.")
            suggestions.append("Explore introductory cross-sell opportunities.")
        else:
            desc_parts.append("Balanced Core Segment: Moderate, evenly distributed purchasing behavior aligned with average wholesale levels.")
            suggestions.append("Maintain steady catalog exposure and periodic standard promotions.")

        description = " ".join(desc_parts) if desc_parts else "Standard wholesale customer cohort with balanced category distribution."
        return description, suggestions
