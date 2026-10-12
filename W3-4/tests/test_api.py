"""
Unit tests for Flask API endpoints.
"""

import unittest
from app import app


class TestMovieScopeAPI(unittest.TestCase):
    """Test suite for Flask API routes."""

    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        """Tests /api/health returns HTTP 200 and expected status fields."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("movies_count", data)

    def test_dashboard_endpoint(self):
        """Tests /api/dashboard returns HTTP 200 and KPI metrics."""
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("total_movies", data["data"])
        self.assertIn("overall_average_rating", data["data"])

    def test_data_quality_endpoint(self):
        """Tests /api/data-quality returns valid data cleaning report."""
        response = self.client.get("/api/data-quality")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("movies_valid", data["data"])

    def test_movies_endpoint_and_pagination(self):
        """Tests /api/movies with query filtering."""
        response = self.client.get("/api/movies?page=1&page_size=5")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["items"]), 5)
        self.assertEqual(data["data"]["page"], 1)

    def test_single_movie_endpoint(self):
        """Tests /api/movies/<id> for valid and invalid IDs."""
        # Valid movie
        res_valid = self.client.get("/api/movies/1")
        self.assertEqual(res_valid.status_code, 200)
        self.assertTrue(res_valid.get_json()["success"])

        # Invalid movie
        res_invalid = self.client.get("/api/movies/999999")
        self.assertEqual(res_invalid.status_code, 404)
        self.assertFalse(res_invalid.get_json()["success"])

    def test_recommendations_endpoint(self):
        """Tests /api/recommendations/<id>."""
        response = self.client.get("/api/recommendations/1?limit=3")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 3)

    def test_chart_endpoint(self):
        """Tests /api/charts/ratings serves image/png."""
        response = self.client.get("/api/charts/ratings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "image/png")

    def test_export_endpoint(self):
        """Tests /api/export/movies returns CSV attachment."""
        response = self.client.get("/api/export/movies")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))


if __name__ == "__main__":
    unittest.main()
