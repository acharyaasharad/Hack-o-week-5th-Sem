import pytest
import pandas as pd
import numpy as np
from services.clustering_service import ClusteringService

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "Fresh": [12000, 7000, 6000, 13000, 20000, 3000, 4000, 15000, 25000, 5000],
        "Milk": [9000, 9500, 8500, 1200, 1500, 7000, 8000, 2000, 3000, 8500],
        "Grocery": [7500, 9500, 7600, 4200, 2000, 9000, 9500, 3000, 4000, 10000],
        "Frozen": [200, 1700, 2400, 6400, 8000, 150, 200, 5000, 9000, 300],
        "Detergents_Paper": [2600, 3200, 3500, 500, 300, 3000, 3400, 600, 400, 4000],
        "Delicassen": [1300, 1700, 7800, 1700, 2000, 500, 800, 2500, 3000, 1000],
    })

def test_kmeans_execution(sample_df):
    cs = ClusteringService()
    res = cs.fit_clustering_model(
        df=sample_df,
        numeric_features=list(sample_df.columns),
        algorithm="kmeans",
        params={"n_clusters": 2, "random_state": 42},
    )
    assert res["status"] == "success"
    assert res["cluster_count"] == 2
    assert "inertia" in res["algorithm_details"]
    assert res["pca_visualization"]["available"]

def test_hierarchical_execution(sample_df):
    cs = ClusteringService()
    res = cs.fit_clustering_model(
        df=sample_df,
        numeric_features=list(sample_df.columns),
        algorithm="hierarchical",
        params={"n_clusters": 2, "linkage": "ward"},
    )
    assert res["status"] == "success"
    assert res["cluster_count"] == 2

def test_dbscan_execution(sample_df):
    cs = ClusteringService()
    res = cs.fit_clustering_model(
        df=sample_df,
        numeric_features=list(sample_df.columns),
        algorithm="dbscan",
        params={"eps": 2.0, "min_samples": 2},
    )
    assert res["status"] == "success"
    assert "noise_count" in res

def test_out_of_sample_prediction(sample_df):
    cs = ClusteringService()
    cs.fit_clustering_model(
        df=sample_df,
        numeric_features=list(sample_df.columns),
        algorithm="kmeans",
        params={"n_clusters": 2, "random_state": 42},
    )
    # Predict new
    new_obs = {col: 10000 for col in sample_df.columns}
    pred = cs.predict_new_customer(new_obs)
    assert pred["supported"]
    assert pred["assigned_cluster"] in [0, 1]
