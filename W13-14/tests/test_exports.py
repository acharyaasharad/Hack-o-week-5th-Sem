import pytest
from app import app, training_service, data_service

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_export_comparison_csv(client):
    # Prime leaderboard
    training_service._leaderboard = [
        {
            "model_id": "decision_tree",
            "task": "classification",
            "parameters": {"max_depth": 5},
            "primary_val_score": 0.85,
            "primary_train_score": 0.95,
            "generalization_gap": 0.10,
            "train_time_seconds": 0.05,
        }
    ]
    res = client.get("/api/export/comparison")
    assert res.status_code == 200
    assert res.headers["Content-Type"].startswith("text/csv")
    assert b"decision_tree" in res.data

def test_export_html_report(client):
    data_service.load_bank_marketing()
    training_service._leaderboard = [
        {
            "model_id": "decision_tree",
            "task": "classification",
            "parameters": {"max_depth": 5},
            "primary_val_score": 0.85,
            "primary_train_score": 0.95,
            "generalization_gap": 0.10,
            "train_time_seconds": 0.05,
        }
    ]
    res = client.get("/api/export/report")
    assert res.status_code == 200
    assert res.headers["Content-Type"].startswith("text/html")
    assert b"Ensemble Learning" in res.data
