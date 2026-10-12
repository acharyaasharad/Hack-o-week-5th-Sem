import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["rows_loaded"] > 0

def test_api_datasets_and_load(client):
    res = client.get("/api/datasets")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["datasets"]) >= 2

    # Load Iris
    load_res = client.post("/api/dataset/load", json={"dataset_id": "iris"})
    assert load_res.status_code == 200
    assert load_res.get_json()["summary"]["total_rows"] == 150

def test_api_pca_and_tsne_run(client):
    # Switch back to wine
    client.post("/api/dataset/load", json={"dataset_id": "wine"})

    # Run PCA
    pca_res = client.post("/api/pca/run", json={"n_components": 2})
    assert pca_res.status_code == 200
    pdata = pca_res.get_json()
    assert pdata["status"] == "success"
    assert "explained_variance_ratio" in pdata

    # Run t-SNE
    tsne_res = client.post("/api/tsne/run", json={"perplexity": 20.0, "max_iter": 300})
    assert tsne_res.status_code == 200
    tdata = tsne_res.get_json()
    assert tdata["status"] == "success"

def test_api_compare_run(client):
    client.post("/api/dataset/load", json={"dataset_id": "wine"})
    res = client.post("/api/compare/run", json={"perplexity": 25.0})
    assert res.status_code == 200
    data = res.get_json()
    assert "pca" in data
    assert "tsne" in data
