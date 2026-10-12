"""Unit tests for DataManager ETL, data integrity validation, and cleansing rules."""

import unittest
from pathlib import Path
import tempfile
import pandas as pd

from services.data_manager import DataManager
import config


class TestDataManager(unittest.TestCase):
    """Verifies DataManager ingestion, validation, and data quality tracking."""

    def setUp(self):
        self.data_manager = DataManager()

    def test_default_datasets_load_successfully(self):
        """Verifies bundled players and matches datasets load with expected rows."""
        players = self.data_manager.get_players_df()
        matches = self.data_manager.get_matches_df()

        self.assertFalse(players.empty, "Players dataset should not be empty")
        self.assertGreaterEqual(len(players), 100, "Should have at least 100 players")
        self.assertFalse(matches.empty, "Matches dataset should not be empty")
        self.assertGreaterEqual(len(matches), 100, "Should have at least 100 matches")

    def test_derived_columns_exist(self):
        """Verifies all mandatory derived football metrics are created."""
        players = self.data_manager.get_players_df()
        expected_cols = [
            "goals_per_90",
            "assists_per_90",
            "goal_contributions",
            "goal_contributions_per_90",
            "pass_completion_pct",
            "shot_accuracy_pct",
            "xg_difference",
            "xa_difference",
            "defensive_actions",
            "defensive_actions_per_90",
        ]
        for col in expected_cols:
            self.assertIn(col, players.columns, f"Column {col} must exist in cleaned dataframe")

    def test_missing_required_columns_fails_gracefully(self):
        """Ensures uploading a CSV lacking required headers raises a ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            f.write("player_id,player_name,wrong_column\n1,Test Player,val\n")
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValueError):
                self.data_manager.load_data(temp_path, is_custom=True)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_shots_on_target_constraint(self):
        """Verifies shots_on_target is clamped to never exceed total shots."""
        players = self.data_manager.get_players_df()
        invalid_mask = players["shots_on_target"] > players["shots"]
        self.assertEqual(invalid_mask.sum(), 0, "No player should have shots_on_target > shots")

    def test_passes_completed_constraint(self):
        """Verifies completed passes never exceed attempted passes."""
        players = self.data_manager.get_players_df()
        invalid_mask = players["passes_completed"] > players["passes_attempted"]
        self.assertEqual(invalid_mask.sum(), 0, "No player should have passes_completed > passes_attempted")

    def test_data_quality_report_structure(self):
        """Ensures the generated quality report contains structured audit metrics."""
        report = self.data_manager.get_data_quality_report()
        self.assertIn("completeness_score", report)
        self.assertIn("players", report)
        self.assertIn("matches", report)
        self.assertGreaterEqual(report["completeness_score"], 90.0)


if __name__ == "__main__":
    unittest.main()
