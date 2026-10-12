"""
Unit tests for DataManager service.
"""

from pathlib import Path
import unittest
import pandas as pd
from services.data_manager import DataManager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class TestDataManager(unittest.TestCase):
    """Test suite for DataManager."""

    def setUp(self):
        self.dm = DataManager(data_dir=DATA_DIR)

    def test_sample_dataset_loaded(self):
        """Verifies that sample movies and ratings load successfully."""
        self.assertFalse(self.dm.get_movies_df().empty)
        self.assertFalse(self.dm.get_ratings_df().empty)
        self.assertFalse(self.dm.get_merged_data().empty)
        self.assertEqual(self.dm.source_type, "Sample Dataset")

    def test_required_columns_validation(self):
        """Verifies that column validation raises ValueError if columns are missing."""
        bad_df = pd.DataFrame({"id": [1], "name": ["Test"]})
        with self.assertRaises(ValueError):
            self.dm.validate_columns(bad_df, ["movieId", "title", "genres"], "Test")

    def test_release_year_extraction(self):
        """Tests extraction of release year from movie titles."""
        self.assertEqual(self.dm.extract_year("Toy Story (1995)"), 1995)
        self.assertEqual(self.dm.extract_year("The Matrix (1999)"), 1999)
        self.assertIsNone(self.dm.extract_year("No Year In Title"))
        self.assertIsNone(self.dm.extract_year("Invalid Year (9999)"))

    def test_rating_range_and_deduplication(self):
        """Tests that ratings outside [0.5, 5.0] are discarded and duplicate pairs are deduplicated."""
        raw_ratings = pd.DataFrame(
            {
                "userId": [1, 1, 2, 3],
                "movieId": [1, 1, 1, 1],
                "rating": [4.0, 5.0, 6.5, 0.2],  # 6.5 and 0.2 are out of bounds
                "timestamp": [100, 200, 300, 400],
            }
        )
        cleaned, stats = self.dm.clean_ratings(raw_ratings, valid_movie_ids={1})

        # Only userId 1 should survive, and deduplication keeps latest timestamp (rating 5.0)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["userId"], 1)
        self.assertEqual(cleaned.iloc[0]["rating"], 5.0)
        self.assertEqual(stats["out_of_range_removed"], 2)
        self.assertEqual(stats["duplicates_removed"], 1)

    def test_unknown_movie_id_filtered(self):
        """Tests that ratings for unknown movie IDs are filtered."""
        raw_ratings = pd.DataFrame(
            {
                "userId": [1, 2],
                "movieId": [1, 99999],  # 99999 is unknown
                "rating": [4.0, 3.5],
                "timestamp": [100, 200],
            }
        )
        cleaned, stats = self.dm.clean_ratings(raw_ratings, valid_movie_ids={1})
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(stats["unknown_movie_removed"], 1)

    def test_left_join_preserves_unrated_movies(self):
        """Tests that movies with 0 ratings are retained with rating_count = 0."""
        merged = self.dm.get_merged_data()
        movie_60 = merged[merged["movieId"] == 60]
        self.assertFalse(movie_60.empty)
        self.assertEqual(movie_60.iloc[0]["rating_count"], 0)
        self.assertEqual(movie_60.iloc[0]["average_rating"], 0.0)

    def test_data_quality_report(self):
        """Tests that the data quality report returns complete diagnostic metrics."""
        report = self.dm.get_data_quality_report()
        self.assertIn("movies_loaded", report)
        self.assertIn("ratings_loaded", report)
        self.assertIn("cleaning_operations", report)
        self.assertTrue(len(report["cleaning_operations"]) > 0)


if __name__ == "__main__":
    unittest.main()
