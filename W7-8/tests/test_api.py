"""Integration tests for Flask API endpoints."""

import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "healthy"
    assert data["app_name"] == "Energy Intelligence"


def test_api_datasets_sample(client):
    resp = client.get("/api/datasets/sample")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert len(data["datasets"]) > 0


def test_api_dataset_summary_and_preview(client):
    summary_resp = client.get("/api/dataset/summary")
    assert summary_resp.status_code == 200
    summary = json.loads(summary_resp.data)
    assert summary["success"] is True

    preview_resp = client.get("/api/dataset/preview?limit=5")
    assert preview_resp.status_code == 200
    preview = json.loads(preview_resp.data)
    assert preview["success"] is True
    assert len(preview["rows"]) <= 5


def test_api_patterns(client):
    resp = client.get("/api/patterns")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert len(data["hourly_profile"]) == 24
    assert len(data["heatmap"]["matrix"]) == 7


def test_api_weather(client):
    resp = client.get("/api/weather")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert "forecast_records" in data


def test_api_optimization_run(client):
    payload = {
        "required_energy": 50.0,
        "max_power": 12.0,
        "start_hour": 0,
        "end_hour": 23,
        "objective": "balanced",
    }
    resp = client.post("/api/optimization/run", json=payload)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert data["summary"]["energy_conserved"] is True


def test_api_optimization_infeasible_rejection(client):
    payload = {
        "required_energy": 100.0,
        "max_power": 2.0,
        "start_hour": 1,
        "end_hour": 5,  # Only 5 hours * 2 kW = 10 kWh max < 100 kWh
    }
    resp = client.post("/api/optimization/run", json=payload)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False
    assert "Infeasible" in data["error"]


def test_api_reports_export_html(client):
    payload = {
        "type": "html",
        "forecast_results": {
            "forecast_series": [
                {"step": 1, "timestamp": "2024-01-02 00:00:00", "predicted_demand": 25.5, "lower_bound": 22.1, "upper_bound": 28.9}
            ]
        }
    }
    resp = client.post("/api/reports/export", json=payload)
    assert resp.status_code == 200
    assert "text/html" in resp.content_type
    assert b"Energy Demand Forecasting" in resp.data
