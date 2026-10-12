import pytest
import numpy as np
from services.evaluation_service import EvaluationService

def test_evaluation_valid_clusters():
    X = np.array([
        [1.0, 1.0], [1.2, 1.1], [0.9, 0.8],
        [8.0, 8.0], [8.2, 8.1], [7.9, 7.8],
    ])
    labels = np.array([0, 0, 0, 1, 1, 1])
    res = EvaluationService.evaluate_clustering(X, labels, "kmeans")
    assert res["n_clusters"] == 2
    assert res["metrics"]["silhouette_score"] is not None
    assert res["metrics"]["silhouette_score"] > 0.5
    assert res["metrics"]["davies_bouldin_index"] is not None
    assert res["metrics"]["calinski_harabasz_score"] is not None

def test_evaluation_singleton_and_all_noise():
    # Only 1 cluster -> metrics should be None, not crashed or zeroed
    X = np.array([[1.0, 1.0], [1.2, 1.1]])
    labels = np.array([0, 0])
    res = EvaluationService.evaluate_clustering(X, labels, "kmeans")
    assert res["metrics"]["silhouette_score"] is None

    # All noise (-1) in DBSCAN
    X_noise = np.array([[1.0, 1.0], [5.0, 5.0]])
    labels_noise = np.array([-1, -1])
    res_noise = EvaluationService.evaluate_clustering(X_noise, labels_noise, "dbscan")
    assert res_noise["noise_percentage"] == 100.0
    assert res_noise["metrics"]["silhouette_score"] is None
