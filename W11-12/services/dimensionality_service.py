"""Dimensionality service executing PCA and t-SNE algorithms.
Constructs scikit-learn Pipelines, calculates explained variance, loadings,
manages perplexity guards and common-sample alignments.
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import inspect
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import logging

import config
from services.preprocessing_service import PreprocessingService
from services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)

class DimensionalityService:
    def __init__(self):
        self._last_pca_result: Optional[Dict[str, Any]] = None
        self._last_tsne_result: Optional[Dict[str, Any]] = None
        self._last_compare_result: Optional[Dict[str, Any]] = None

    def run_pca(
        self,
        df: pd.DataFrame,
        features: List[str],
        n_components: int = 2,
        scaler: str = "standard",
        log_transform: bool = False,
        color_by: Optional[str] = None,
        kmeans_overlay: bool = False,
        kmeans_k: int = 3,
        random_state: int = config.RANDOM_STATE,
    ) -> Dict[str, Any]:
        """Fits PCA pipeline on selected features and extracts loadings and variance."""
        start_time = time.time()
        
        # Build preprocessor
        preprocessor, steps_info = PreprocessingService.create_preprocessor(
            numeric_features=features,
            scaler=scaler,
            log_transform=log_transform,
        )

        n_samples = len(df)
        max_possible_components = min(n_samples, len(features))
        n_comp = min(n_components, max_possible_components)

        pca = PCA(n_components=n_comp, random_state=random_state)
        pipeline = Pipeline([
            ("preprocessing", preprocessor),
            ("pca", pca),
        ])

        X_df = df[features].copy()
        pipeline.fit(X_df)

        fitted_preprocessor = pipeline.named_steps["preprocessing"]
        fitted_pca = pipeline.named_steps["pca"]

        X_trans = fitted_preprocessor.transform(X_df)
        X_pca = fitted_pca.transform(X_trans)
        feature_names = PreprocessingService.get_feature_names(fitted_preprocessor)

        exec_time = float(round(time.time() - start_time, 4))

        # Variance calculations
        exp_var_ratio = [float(round(v * 100, 2)) for v in fitted_pca.explained_variance_ratio_]
        cum_var_ratio = [float(round(v, 2)) for v in np.cumsum(exp_var_ratio)]
        pc1_var = exp_var_ratio[0] if len(exp_var_ratio) > 0 else 0.0
        pc2_var = exp_var_ratio[1] if len(exp_var_ratio) > 1 else 0.0
        total_2d_var = float(round(pc1_var + pc2_var, 2))

        # Loadings table
        loadings = []
        for i, comp in enumerate(fitted_pca.components_):
            comp_name = f"PC{i+1}"
            for f_idx, feat_name in enumerate(feature_names):
                val = float(round(comp[f_idx], 4))
                loadings.append({
                    "component": comp_name,
                    "feature": feat_name,
                    "loading": val,
                    "abs_loading": abs(val),
                })

        # Reconstruction error
        X_reconstructed = fitted_pca.inverse_transform(X_pca)
        recon_error = EvaluationService.compute_reconstruction_error(X_trans, X_reconstructed)

        # Trustworthiness
        trust = EvaluationService.compute_trustworthiness(X_trans, X_pca[:, :2])

        # Cluster overlay
        cluster_labels = None
        if kmeans_overlay:
            km = KMeans(n_clusters=kmeans_k, random_state=random_state)
            cluster_labels = km.fit_predict(X_trans).tolist()

        # Build coordinate payload aligned with stable _row_id
        row_ids = df["_row_id"].tolist() if "_row_id" in df.columns else [f"ROW-{i+1}" for i in range(len(df))]
        color_vals = df[color_by].astype(str).tolist() if color_by and color_by in df.columns else ["Default"] * len(df)

        coordinates = []
        for idx in range(len(df)):
            coord_entry = {
                "row_id": row_ids[idx],
                "x": float(round(X_pca[idx, 0], 3)),
                "y": float(round(X_pca[idx, 1], 3)) if n_comp > 1 else 0.0,
                "color_value": color_vals[idx],
            }
            if n_comp >= 3:
                coord_entry["z"] = float(round(X_pca[idx, 2], 3))
            if cluster_labels:
                coord_entry["kmeans_cluster"] = f"Cluster_{cluster_labels[idx]}"
            coordinates.append(coord_entry)

        result = {
            "status": "success",
            "method": "pca",
            "n_samples": n_samples,
            "n_features": len(features),
            "n_components": n_comp,
            "execution_time_seconds": exec_time,
            "explained_variance_ratio": exp_var_ratio,
            "cumulative_variance_ratio": cum_var_ratio,
            "pc1_variance": pc1_var,
            "pc2_variance": pc2_var,
            "total_2d_variance": total_2d_var,
            "reconstruction_error": recon_error,
            "trustworthiness": trust,
            "loadings": loadings,
            "coordinates": coordinates,
            "color_by": color_by,
            "kmeans_overlay": kmeans_overlay,
            "configuration": {
                "scaler": scaler,
                "log_transform": log_transform,
                "features": features,
            }
        }
        self._last_pca_result = result
        return result

    def run_tsne(
        self,
        df: pd.DataFrame,
        features: List[str],
        perplexity: float = 30.0,
        learning_rate: Any = "auto",
        max_iter: int = 1000,
        init: str = "pca",
        early_exaggeration: float = 12.0,
        n_components: int = 2,
        scaler: str = "standard",
        log_transform: bool = False,
        color_by: Optional[str] = None,
        kmeans_overlay: bool = False,
        kmeans_k: int = 3,
        sample_limit: int = config.MAX_TSNE_SAMPLES,
        random_state: int = config.RANDOM_STATE,
    ) -> Dict[str, Any]:
        """Executes t-SNE with strict perplexity validation and sample bounds."""
        start_time = time.time()
        n_samples = len(df)
        warnings = []

        # Subsample if exceeds sample_limit
        if n_samples > sample_limit:
            df_sampled = df.sample(n=sample_limit, random_state=random_state).sort_index()
            warnings.append(
                f"Dataset contains {n_samples} rows. A reproducible sample of {sample_limit} rows "
                f"was selected to optimize t-SNE execution."
            )
        else:
            df_sampled = df.copy()

        n_run = len(df_sampled)

        # Critical perplexity guard
        if perplexity >= n_run:
            new_perp = max(1.0, float(n_run - 1))
            warnings.append(
                f"Requested perplexity {perplexity} is >= sample count {n_run}. "
                f"Automatically adjusted to valid maximum of {new_perp:.1f}."
            )
            perplexity = new_perp

        # Preprocess features
        preprocessor, _ = PreprocessingService.create_preprocessor(
            numeric_features=features,
            scaler=scaler,
            log_transform=log_transform,
        )

        X_df = df_sampled[features].copy()
        X_trans = preprocessor.fit_transform(X_df)

        # Check scikit-learn TSNE argument compatibility (max_iter vs n_iter)
        tsne_params = {
            "n_components": n_components,
            "perplexity": perplexity,
            "learning_rate": learning_rate,
            "early_exaggeration": early_exaggeration,
            "init": init,
            "random_state": random_state,
        }

        # Inspect parameter signature of sklearn.manifold.TSNE
        sig = inspect.signature(TSNE.__init__)
        if "max_iter" in sig.parameters:
            tsne_params["max_iter"] = max_iter
        elif "n_iter" in sig.parameters:
            tsne_params["n_iter"] = max_iter

        tsne = TSNE(**tsne_params)
        X_tsne = tsne.fit_transform(X_trans)
        exec_time = float(round(time.time() - start_time, 4))

        # KL divergence
        kl_div = getattr(tsne, "kl_divergence_", None)
        if kl_div is not None:
            kl_div = float(round(kl_div, 3))

        # Trustworthiness
        trust = EvaluationService.compute_trustworthiness(X_trans, X_tsne[:, :2])

        # Cluster overlay
        cluster_labels = None
        if kmeans_overlay:
            km = KMeans(n_clusters=kmeans_k, random_state=random_state)
            cluster_labels = km.fit_predict(X_trans).tolist()

        # Coordinates aligned with stable _row_id
        row_ids = df_sampled["_row_id"].tolist() if "_row_id" in df_sampled.columns else [f"ROW-{i+1}" for i in range(len(df_sampled))]
        color_vals = df_sampled[color_by].astype(str).tolist() if color_by and color_by in df_sampled.columns else ["Default"] * len(df_sampled)

        coordinates = []
        for idx in range(len(df_sampled)):
            coord_entry = {
                "row_id": row_ids[idx],
                "x": float(round(X_tsne[idx, 0], 3)),
                "y": float(round(X_tsne[idx, 1], 3)) if n_components > 1 else 0.0,
                "color_value": color_vals[idx],
            }
            if n_components >= 3:
                coord_entry["z"] = float(round(X_tsne[idx, 2], 3))
            if cluster_labels:
                coord_entry["kmeans_cluster"] = f"Cluster_{cluster_labels[idx]}"
            coordinates.append(coord_entry)

        result = {
            "status": "success",
            "method": "tsne",
            "n_samples": n_run,
            "n_features": len(features),
            "perplexity": perplexity,
            "learning_rate": learning_rate,
            "max_iter": max_iter,
            "kl_divergence": kl_div,
            "trustworthiness": trust,
            "execution_time_seconds": exec_time,
            "coordinates": coordinates,
            "color_by": color_by,
            "kmeans_overlay": kmeans_overlay,
            "warnings": warnings,
            "configuration": {
                "scaler": scaler,
                "log_transform": log_transform,
                "features": features,
            }
        }
        self._last_tsne_result = result
        return result

    def run_comparison(
        self,
        df: pd.DataFrame,
        features: List[str],
        perplexity: float = 30.0,
        scaler: str = "standard",
        log_transform: bool = False,
        color_by: Optional[str] = None,
        sample_limit: int = config.MAX_TSNE_SAMPLES,
    ) -> Dict[str, Any]:
        """Executes PCA and t-SNE on the exact same common observation sample."""
        # 1. Deterministic sample alignment
        if len(df) > sample_limit:
            df_common = df.sample(n=sample_limit, random_state=config.RANDOM_STATE).sort_index()
        else:
            df_common = df.copy()

        # 2. Run PCA
        pca_res = self.run_pca(
            df=df_common,
            features=features,
            n_components=2,
            scaler=scaler,
            log_transform=log_transform,
            color_by=color_by,
        )

        # 3. Run t-SNE
        tsne_res = self.run_tsne(
            df=df_common,
            features=features,
            perplexity=perplexity,
            scaler=scaler,
            log_transform=log_transform,
            color_by=color_by,
            sample_limit=sample_limit,
        )

        comparison = {
            "status": "success",
            "n_samples": len(df_common),
            "n_features": len(features),
            "pca": pca_res,
            "tsne": tsne_res,
            "color_by": color_by,
        }
        self._last_compare_result = comparison
        return comparison
