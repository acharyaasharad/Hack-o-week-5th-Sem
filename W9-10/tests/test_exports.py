import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_export_clusters_csv(client):
    # Ensure clustering has run
    client.post("/api/clustering/run", json={"algorithm": "kmeans", "params": {"n_clusters": 3}})
    res = client.get("/api/export/clusters.csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "Cluster_Label" in res.data.decode("utf-8")

def test_export_profiles_csv(client):
    client.post("/api/clustering/run", json={"algorithm": "kmeans", "params": {"n_clusters": 3}})
    res = client.get("/api/export/profiles.csv")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "Mean_Fresh" in res.data.decode("utf-8")

def test_export_html_report(client):
    client.post("/api/clustering/run", json={"algorithm": "kmeans", "params": {"n_clusters": 3}})
    res = client.get("/api/export/report.html")
    assert res.status_code == 200
    assert res.mimetype == "text/html"
    assert "Customer Segmentation & Intelligence Report" in res.data.decode("utf-8")
    assert "UCI Machine Learning Repository" in res.data.decode("utf-8")
