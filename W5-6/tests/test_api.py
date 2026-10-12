"""Integration tests for Touchline Analytics Flask REST API endpoints."""

import unittest
import json
from app import app


class TestFlaskAPI(unittest.TestCase):
    """Verifies HTTP status codes, JSON response formatting, and error handling."""

    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

    def test_health_endpoint(self):
        """Verifies GET /api/health returns 200 and dataset counts."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("status"), "healthy")
        self.assertGreater(data.get("players_loaded", 0), 100)

    def test_dashboard_endpoint(self):
        """Verifies GET /api/dashboard returns 200 and KPI metrics."""
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("kpis", data.get("data", {}))

    def test_players_endpoint_pagination(self):
        """Verifies GET /api/players handles pagination and filtering."""
        response = self.client.get("/api/players?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        players_data = data.get("data", {})
        self.assertEqual(len(players_data.get("players", [])), 10)
        self.assertEqual(players_data.get("page"), 1)
        self.assertEqual(players_data.get("page_size"), 10)

    def test_single_player_endpoint(self):
        """Verifies GET /api/players/<id> returns 200 for valid ID and 404 for unknown ID."""
        res_valid = self.client.get("/api/players/1")
        self.assertEqual(res_valid.status_code, 200)
        data = res_valid.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["player_id"], 1)

        res_invalid = self.client.get("/api/players/999999")
        self.assertEqual(res_invalid.status_code, 404)

    def test_compare_endpoint(self):
        """Verifies GET /api/compare?ids=1,2 returns comparison data."""
        response = self.client.get("/api/compare?ids=1,2")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(len(data.get("players", [])), 2)
        self.assertIn("radar", data)

    def test_analytics_endpoints(self):
        """Verifies positions, clubs, leagues, and correlation endpoints."""
        for endpoint in ["/api/analytics/positions", "/api/analytics/clubs", "/api/analytics/leagues", "/api/analytics/correlation"]:
            res = self.client.get(endpoint)
            self.assertEqual(res.status_code, 200, f"Endpoint {endpoint} should return 200")
            data = res.get_json()
            self.assertTrue(data.get("success"))

    def test_export_players_csv(self):
        """Verifies GET /api/export/players.csv downloads valid CSV with headers."""
        response = self.client.get("/api/export/players.csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        content = response.data.decode("utf-8")
        self.assertIn("player_id", content)
        self.assertIn("player_name", content)

    def test_reset_dataset_endpoint(self):
        """Verifies POST /api/dataset/reset successfully resets dataset."""
        response = self.client.post("/api/dataset/reset")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))


if __name__ == "__main__":
    unittest.main()
