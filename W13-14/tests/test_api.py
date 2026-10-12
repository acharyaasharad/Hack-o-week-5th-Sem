import pytest
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
    assert "xgboost_available" in data
    assert "lightgbm_available" in data

def test_list_datasets(client):
    res = client.get("/api/datasets")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["datasets"]) >= 2

def test_load_dataset(client):
    res = client.post("/api/dataset/load", json={"dataset_id": "bank_marketing"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "summary" in data

def test_models_for_task(client):
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["models"]) >= 4

def test_synthetic_demo_api(client):
    res = client.post("/api/generalization/synthetic-demo", json={})
    assert res.status_code == 200
    data = res.get_json()
    assert "models" in data
