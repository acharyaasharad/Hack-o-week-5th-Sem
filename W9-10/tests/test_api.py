import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "supported_algorithms" in data

def test_dataset_summary_and_preview(client):
    res = client.get("/api/dataset/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_rows"] == 440

    res_prev = client.get("/api/dataset/preview?page=1&page_size=5")
    assert res_prev.status_code == 200
    prev_data = res_prev.get_json()
    assert len(prev_data["data"]) == 5

def test_clustering_run_endpoint(client):
    payload = {
        "algorithm": "kmeans",
        "params": {"n_clusters": 3, "random_state": 42},
        "numeric_features": ["Fresh", "Milk", "Grocery", "Frozen"],
        "scaling_method": "standard",
        "log_transform": False,
    }
    res = client.post("/api/clustering/run", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["cluster_count"] == 3
    assert "metrics" in data

def test_customer_lookup_endpoint(client):
    # First fit a kmeans model
    client.post("/api/clustering/run", json={"algorithm": "kmeans", "params": {"n_clusters": 3}})
    lookup_payload = {
        "Fresh": 10000,
        "Milk": 5000,
        "Grocery": 6000,
        "Frozen": 2000,
        "Detergents_Paper": 1500,
        "Delicassen": 800,
    }
    res = client.post("/api/clustering/customer-lookup", json=lookup_payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["supported"]
    assert "assigned_cluster" in data

def test_elbow_and_correlation_endpoints(client):
    res_elbow = client.get("/api/clustering/elbow?k_min=2&k_max=4")
    assert res_elbow.status_code == 200
    elbow_data = res_elbow.get_json()
    assert len(elbow_data["k_values"]) == 3

    res_corr = client.get("/api/visualization/correlation")
    assert res_corr.status_code == 200
    corr_data = res_corr.get_json()
    assert len(corr_data["columns"]) > 0
