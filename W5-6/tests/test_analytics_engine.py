"""Unit tests for AnalyticsEngine calculations, filtering, and aggregations."""

import unittest
from services.data_manager import DataManager
from services.analytics_engine import AnalyticsEngine


class TestAnalyticsEngine(unittest.TestCase):
    """Verifies KPI calculations, position analytics, and filter routines."""

    def setUp(self):
        self.data_manager = DataManager()
        self.analytics = AnalyticsEngine(self.data_manager)

    def test_dashboard_kpis(self):
        """Verifies all six dashboard KPI metrics are computed."""
        stats = self.analytics.get_dashboard_stats()
        kpis = stats.get("kpis", {})

        self.assertGreater(kpis.get("total_players", 0), 100)
        self.assertGreater(kpis.get("total_clubs", 0), 10)
        self.assertGreaterEqual(kpis.get("total_competitions", 0), 2)
        self.assertGreater(kpis.get("total_goals", 0), 100)
        self.assertGreater(kpis.get("average_rating", 0.0), 6.0)
        self.assertGreater(kpis.get("total_matches", 0), 100)

    def test_filter_players_by_position(self):
        """Verifies filtering by position returns only players of that position."""
        res = self.analytics.filter_players({"position": "Forward", "page_size": 50})
        players = res.get("players", [])
        self.assertGreater(len(players), 0)
        for p in players:
            self.assertEqual(p["position"], "Forward")

    def test_filter_players_by_search(self):
        """Verifies case-insensitive partial name search."""
        all_players = self.data_manager.get_players_df()
        first_player_name = all_players.iloc[0]["player_name"]
        search_term = first_player_name.split()[0].lower()

        res = self.analytics.filter_players({"search": search_term})
        players = res.get("players", [])
        self.assertGreater(len(players), 0)
        for p in players:
            self.assertIn(search_term, p["player_name"].lower())

    def test_position_analytics(self):
        """Verifies position aggregation returns data for all 4 positions."""
        pos_data = self.analytics.get_position_analytics()
        self.assertEqual(len(pos_data), 4)
        positions = [p["position"] for p in pos_data]
        for expected in ["Goalkeeper", "Defender", "Midfielder", "Forward"]:
            self.assertIn(expected, positions)

    def test_correlation_matrix(self):
        """Verifies correlation matrix returns valid columns and square matrix."""
        corr = self.analytics.get_correlation_matrix()
        cols = corr.get("columns", [])
        matrix = corr.get("matrix", [])

        self.assertGreaterEqual(len(cols), 5)
        self.assertEqual(len(matrix), len(cols))
        self.assertEqual(len(matrix[0]), len(cols))


if __name__ == "__main__":
    unittest.main()
