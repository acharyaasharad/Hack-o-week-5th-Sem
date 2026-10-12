"""Unit tests for ComparisonEngine player head-to-heads and radar scaling."""

import unittest
from services.data_manager import DataManager
from services.comparison_engine import ComparisonEngine


class TestComparisonEngine(unittest.TestCase):
    """Verifies multi-player comparisons, min-max radar scaling, and leaders."""

    def setUp(self):
        self.data_manager = DataManager()
        self.comparison = ComparisonEngine(self.data_manager)

    def test_compare_minimum_two_players(self):
        """Verifies comparison requires at least 2 distinct players."""
        res_one = self.comparison.compare_players([1])
        self.assertFalse(res_one["success"])
        self.assertIn("At least two distinct players", res_one["message"])

        res_dup = self.comparison.compare_players([1, 1])
        self.assertFalse(res_dup["success"])

    def test_successful_two_player_comparison(self):
        """Verifies head-to-head comparison produces radar, leaders, and verdict."""
        res = self.comparison.compare_players([1, 2])
        self.assertTrue(res["success"])
        self.assertEqual(len(res["players"]), 2)

        radar = res.get("radar", {})
        self.assertIn("labels", radar)
        self.assertEqual(len(radar.get("datasets", [])), 2)

        # Check normalized data points are within [0, 100]
        for ds in radar["datasets"]:
            self.assertEqual(len(ds["data"]), len(radar["labels"]))
            for val in ds["data"]:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 100.0)

        # Leaders and verdict
        self.assertIn("leaders", res)
        self.assertIn("verdict", res)
        self.assertIn("summary_points", res["verdict"])

    def test_four_player_comparison_limit(self):
        """Verifies comparison caps at maximum 4 players even if 5 provided."""
        res = self.comparison.compare_players([1, 2, 3, 4, 5])
        self.assertTrue(res["success"])
        self.assertEqual(len(res["players"]), 4)

    def test_nonexistent_player_id_error(self):
        """Verifies invalid player ID returns descriptive error."""
        res = self.comparison.compare_players([1, 999999])
        self.assertFalse(res["success"])
        self.assertIn("Could not find players", res["message"])


if __name__ == "__main__":
    unittest.main()
