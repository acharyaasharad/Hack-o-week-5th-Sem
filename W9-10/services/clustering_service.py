"""Clustering service executing scikit-learn Pipelines with K-Means,
Hierarchical (Agglomerative) Clustering, and DBSCAN.
Also supports Elbow method, hyperparameter comparison, and PCA projection.
"""

from typing import Dict, Any, List, Optional, Tuple
import time
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.decomposition import PCA
import joblib
import logging

import config
from services.preprocessing import PreprocessingService
from services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)

class ClusteringService:
    def __init__(self):
        self._last_fitted_pipeline: Optional[Pipeline] = None
        self._last_algorithm: Optional[str] = None
        self._last_run_result: Optional[Dict[str, Any]] = None
        self._last_labels: Optional[np.ndarray] = None
        self._last_transformed_features: Optional[np.ndarray] = None
        self._last_feature_names: List[str] = []

    def fit_clustering_model(
        self,
        df: pd.DataFrame,
        numeric_features: List[str],
        categorical_features: Optional[List[str]] = None,
        algorithm: str = "kmeans",
        params: Optional[Dict[str, Any]] = None,
        scaling_method: str = "standard",
        log_transform: bool = False,
        numeric_impute_strategy: str = "median",
    ) -> Dict[str, Any]:
        """Constructs and fits the scikit-learn Pipeline([('preprocessing', ...), ('clustering', ...)])."""
        start_time = time.time()
        params = params or {}
        categorical_features = categorical_features or []

        # 1. Build Preprocessor
        preprocessor, steps_info = PreprocessingService.create_preprocessor(
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            scaling_method=scaling_method,
            log_transform=log_transform,
            numeric_impute_strategy=numeric_impute_strategy,
        )

        # 2. Select Estimator
        if algorithm == "kmeans":
            n_clusters = int(params.get("n_clusters", 4))
            init_method = params.get("init", "k-means++")
            n_init = int(params.get("n_init", 10))
            max_iter = int(params.get("max_iter", 300))
            random_state = int(params.get("random_state", config.RANDOM_STATE))

            estimator = KMeans(
                n_clusters=n_clusters,
                init=init_method,
                n_init=n_init,
                max_iter=max_iter,
                random_state=random_state,
            )
            algorithm_name = "K-Means"

        elif algorithm == "hierarchical":
            n_clusters = int(params.get("n_clusters", 4))
            linkage = params.get("linkage", "ward")
            metric = params.get("metric", "euclidean")

            # Note: Ward linkage strictly requires Euclidean metric
            if linkage == "ward" and metric != "euclidean":
                metric = "euclidean"

            estimator = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage=linkage,
                metric=metric,
            )
            algorithm_name = "Hierarchical Clustering"

        elif algorithm == "dbscan":
            eps = float(params.get("eps", 0.7))
            min_samples = int(params.get("min_samples", 5))
            metric = params.get("metric", "euclidean")

            estimator = DBSCAN(
                eps=eps,
                min_samples=min_samples,
                metric=metric,
            )
            algorithm_name = "DBSCAN"
        else:
            raise ValueError(f"Unsupported clustering algorithm: '{algorithm}'")

        # 3. Construct unified Pipeline
        pipeline = Pipeline([
            ("preprocessing", preprocessor),
            ("clustering", estimator),
        ])

        # Prepare input data subset
        selected_cols = numeric_features + categorical_features
        X_df = df[selected_cols].copy()

        # Fit Pipeline
        pipeline.fit(X_df)
        execution_time = float(round(time.time() - start_time, 4))

        # Retrieve fitted objects and transformed data
        fitted_preprocessor = pipeline.named_steps["preprocessing"]
        fitted_clustering = pipeline.named_steps["clustering"]
        X_transformed = fitted_preprocessor.transform(X_df)
        labels = fitted_clustering.labels_

        feature_names = PreprocessingService.get_feature_names(fitted_preprocessor)

        # 4. Evaluate clustering metrics
        eval_results = EvaluationService.evaluate_clustering(
            X_transformed=X_transformed,
            labels=labels,
            algorithm=algorithm
        )

        # Additional algorithm-specific metadata
        algo_details = {}
        if algorithm == "kmeans":
            algo_details["inertia"] = float(round(fitted_clustering.inertia_, 2))
            algo_details["n_iter"] = int(fitted_clustering.n_iter_)
            # Centers in transformed space
            algo_details["cluster_centers_transformed"] = fitted_clustering.cluster_centers_.tolist()

        # 5. Compute PCA 2D projection for visualization
        pca_result = self._compute_pca_visualization(X_transformed, labels)

        # 6. Save State
        self._last_fitted_pipeline = pipeline
        self._last_algorithm = algorithm
        self._last_labels = labels
        self._last_transformed_features = X_transformed
        self._last_feature_names = feature_names

        result = {
            "status": "success",
            "algorithm": algorithm,
            "algorithm_name": algorithm_name,
            "parameters": params,
            "preprocessing": {
                "scaling_method": scaling_method,
                "log_transform": log_transform,
                "numeric_impute_strategy": numeric_impute_strategy,
                "numeric_features": numeric_features,
                "categorical_features": categorical_features,
                "output_dimensions": int(X_transformed.shape[1]),
                "pipeline_steps": steps_info,
            },
            "cluster_count": eval_results["n_clusters"],
            "noise_count": eval_results["noise_count"],
            "noise_percentage": eval_results["noise_percentage"],
            "cluster_sizes": eval_results["cluster_sizes"],
            "metrics": eval_results["metrics"],
            "algorithm_details": algo_details,
            "execution_time_seconds": execution_time,
            "pca_visualization": pca_result,
            "warnings": eval_results["warnings"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._last_run_result = result
        return result

    def _compute_pca_visualization(
        self,
        X_transformed: np.ndarray,
        labels: np.ndarray,
        sample_limit: int = 2000
    ) -> Dict[str, Any]:
        """Projects transformed high-dimensional features to 2D for interactive plotting."""
        n_samples, n_features = X_transformed.shape
        if n_features < 2:
            return {"available": False, "reason": "PCA requires at least 2 features."}

        # Subsample if dataset is extraordinarily huge for browser rendering
        if n_samples > sample_limit:
            idx = np.random.choice(n_samples, sample_limit, replace=False)
            X_eval = X_transformed[idx]
            labels_eval = labels[idx]
        else:
            X_eval = X_transformed
            labels_eval = labels

        pca = PCA(n_components=2, random_state=config.RANDOM_STATE)
        X_pca = pca.fit_transform(X_eval)

        explained_var = [float(round(v * 100, 2)) for v in pca.explained_variance_ratio_]

        return {
            "available": True,
            "pca_x": [float(round(val, 3)) for val in X_pca[:, 0]],
            "pca_y": [float(round(val, 3)) for val in X_pca[:, 1]],
            "labels": [int(l) for l in labels_eval],
            "explained_variance_ratio": explained_var,
            "total_explained_variance": float(round(sum(explained_var), 2)),
        }

    def compute_elbow_curve(
        self,
        df: pd.DataFrame,
        numeric_features: List[str],
        categorical_features: Optional[List[str]] = None,
        k_min: int = 2,
        k_max: int = 10,
        scaling_method: str = "standard",
        log_transform: bool = False,
    ) -> Dict[str, Any]:
        """Computes K-Means inertia across k=k_min..k_max for elbow analysis."""
        categorical_features = categorical_features or []
        preprocessor, _ = PreprocessingService.create_preprocessor(
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            scaling_method=scaling_method,
            log_transform=log_transform,
        )

        selected_cols = numeric_features + categorical_features
        X_df = df[selected_cols].copy()
        X_transformed = preprocessor.fit_transform(X_df)

        max_k = min(k_max, len(X_df) - 1)
        ks = list(range(k_min, max_k + 1))
        inertias = []
        silhouette_scores = []

        for k in ks:
            km = KMeans(n_clusters=k, init="k-means++", n_init=5, max_iter=200, random_state=config.RANDOM_STATE)
            labels = km.fit_predict(X_transformed)
            inertias.append(float(round(km.inertia_, 2)))
            eval_res = EvaluationService.evaluate_clustering(X_transformed, labels, "kmeans")
            silhouette_scores.append(eval_res["metrics"]["silhouette_score"])

        return {
            "k_values": ks,
            "inertias": inertias,
            "silhouette_scores": silhouette_scores,
        }

    def compare_configurations(
        self,
        df: pd.DataFrame,
        numeric_features: List[str],
        categorical_features: Optional[List[str]] = None,
        scaling_method: str = "standard",
        log_transform: bool = False,
    ) -> List[Dict[str, Any]]:
        """Runs a bounded comparison grid across K-Means, Hierarchical, and DBSCAN."""
        results = []
        configs = [
            ("kmeans", {"n_clusters": 3}),
            ("kmeans", {"n_clusters": 4}),
            ("kmeans", {"n_clusters": 5}),
            ("hierarchical", {"n_clusters": 3, "linkage": "ward"}),
            ("hierarchical", {"n_clusters": 4, "linkage": "ward"}),
            ("hierarchical", {"n_clusters": 4, "linkage": "average"}),
            ("dbscan", {"eps": 0.5, "min_samples": 5}),
            ("dbscan", {"eps": 0.7, "min_samples": 5}),
            ("dbscan", {"eps": 1.0, "min_samples": 5}),
        ]

        for algo, p in configs:
            try:
                res = self.fit_clustering_model(
                    df=df,
                    numeric_features=numeric_features,
                    categorical_features=categorical_features,
                    algorithm=algo,
                    params=p,
                    scaling_method=scaling_method,
                    log_transform=log_transform,
                )
                results.append({
                    "algorithm": algo,
                    "algorithm_name": res["algorithm_name"],
                    "parameters": p,
                    "cluster_count": res["cluster_count"],
                    "noise_percentage": res["noise_percentage"],
                    "silhouette_score": res["metrics"]["silhouette_score"],
                    "davies_bouldin_index": res["metrics"]["davies_bouldin_index"],
                    "calinski_harabasz_score": res["metrics"]["calinski_harabasz_score"],
                    "execution_time_seconds": res["execution_time_seconds"],
                    "warnings": res["warnings"],
                })
            except Exception as e:
                logger.warning("Comparison run failed for %s (%s): %s", algo, p, e)

        return results

    def predict_new_customer(self, customer_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Predicts cluster assignment for a new observation using fitted K-Means pipeline."""
        if not self._last_fitted_pipeline or self._last_algorithm != "kmeans":
            return {
                "supported": False,
                "message": (
                    "New customer assignment is currently supported only for K-Means models. "
                    "Hierarchical clustering and DBSCAN are non-inductive in standard scikit-learn."
                )
            }

        try:
            df_new = pd.DataFrame([customer_dict])
            pipeline = self._last_fitted_pipeline
            preprocessor = pipeline.named_steps["preprocessing"]
            kmeans_estimator = pipeline.named_steps["clustering"]

            # Transform and predict
            X_trans = preprocessor.transform(df_new)
            cluster_id = int(kmeans_estimator.predict(X_trans)[0])
            
            # Compute distance to assigned centroid
            centroid = kmeans_estimator.cluster_centers_[cluster_id]
            dist = float(round(np.linalg.norm(X_trans[0] - centroid), 3))

            return {
                "supported": True,
                "assigned_cluster": cluster_id,
                "distance_to_centroid": dist,
                "message": f"Successfully assigned to Cluster {cluster_id}."
            }
        except Exception as e:
            return {"supported": False, "message": f"Prediction failed: {str(e)}"}

    def get_last_run(self) -> Optional[Dict[str, Any]]:
        return self._last_run_result

    def get_last_labels(self) -> Optional[np.ndarray]:
        return self._last_labels
