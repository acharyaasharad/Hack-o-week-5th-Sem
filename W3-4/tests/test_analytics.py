"""
Unit tests for AnalyticsEngine service.
"""

from pathlib import Path
import unittest
from services.analytics import AnalyticsEngine
from services.data_manager import DataManager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class TestAnalyticsEngine(unittest.TestCase):
    """Test suite for AnalyticsEngine."""

    def setUp(self):
        self.dm = DataManager(data_dir=DATA_DIR)
        self.analytics = AnalyticsEngine(data_manager=self.dm)

    def test_dashboard_stats(self):
        """Verifies dashboard summary metrics."""
        stats = self.analytics.get_dashboard_stats()
        self.assertEqual(stats["total_movies"], len(self.dm.get_movies_df()))
        self.assertEqual(stats["total_ratings"], len(self.dm.get_ratings_df()))
        self.assertGreater(stats["unique_users"], 0)
        self.assertGreater(stats["overall_average_rating"], 1.0)
        self.assertIsNotNone(stats["highest_rated_movie"])

    def test_movie_search_and_filtering(self):
        """Tests search, filtering, and pagination in movie summary."""
        # 1. Search for 'Dark Knight'
        res = self.analytics.get_movie_summary(search="dark knight")
        self.assertGreaterEqual(res["total_count"], 1)
        self.assertIn("Dark Knight", res["items"][0]["title"])

        # 2. Filter by genre 'Animation'
        anim_res = self.analytics.get_movie_summary(genre="Animation")
        self.assertGreaterEqual(anim_res["total_count"], 3)
        for m in anim_res["items"]:
            self.assertIn("Animation", m["genre_list"])

        # 3. Pagination check
        paged = self.analytics.get_movie_summary(page=1, page_size=5)
        self.assertEqual(len(paged["items"]), 5)
        self.assertGreaterEqual(paged["total_pages"], 2)

    def test_genre_statistics_multi_genre(self):
        """Verifies genre analysis correctly accounts for multi-genre films."""
        genres = self.analytics.get_genre_statistics()
        self.assertGreater(len(genres), 5)
        total_exploded_movies = sum(g["movie_count"] for g in genres)
        # Exploded count should exceed raw total movies because of multi-genre overlaps
        self.assertGreater(total_exploded_movies, len(self.dm.get_movies_df()))

    def test_rating_distribution(self):
        """Tests user rating and movie average distribution calculations."""
        dist = self.analytics.get_rating_distribution()
        self.assertIn("user_ratings_dist", dist)
        self.assertIn("stats", dist)
        self.assertIn("mean", dist["stats"])
        self.assertIn("median", dist["stats"])

    def test_chart_generation(self):
        """Tests that chart images are generated and saved without errors."""
        hist_path = self.analytics.generate_rating_histogram("test_hist.png")
        self.assertTrue(hist_path.exists())
        self.assertGreater(hist_path.stat().st_size, 1000)

        # Cleanup test chart
        hist_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
