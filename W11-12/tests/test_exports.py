import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_exports_csv_and_html(client):
    # Run PCA first
    client.post("/api/pca/run", json={"n_components": 2})

    # PCA CSV
    res_pca = client.get("/api/export/pca.csv")
    assert res_pca.status_code == 200
    assert res_pca.mimetype == "text/csv"
    assert "row_id" in res_pca.data.decode("utf-8")

    # Loadings CSV
    res_loadings = client.get("/api/export/loadings.csv")
    assert res_loadings.status_code == 200
    assert res_loadings.mimetype == "text/csv"
    assert "loading" in res_loadings.data.decode("utf-8")

    # HTML Report
    res_html = client.get("/api/export/report")
    assert res_html.status_code == 200
    assert res_html.mimetype == "text/html"
    assert "Dimensionality Reduction Analysis Report" in res_html.data.decode("utf-8")
