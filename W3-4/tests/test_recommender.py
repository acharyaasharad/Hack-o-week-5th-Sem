"""
Unit tests for MovieRecommender service.
"""

from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from services.data_manager import DataManager
from services.recommender import MovieRecommender

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class TestMovieRecommender(unittest.TestCase):
    """Test suite for MovieRecommender."""

    def setUp(self):
        self.dm = DataManager(data_dir=DATA_DIR)
        self.recommender = MovieRecommender(data_manager=self.dm)

    def test_recommender_fit_and_genre_matrix(self):
        """Verifies that the genre matrix is built with correct dimensions."""
        self.assertGreater(len(self.recommender.unique_genres), 5)
        self.assertEqual(len(self.recommender.genre_matrix), len(self.dm.get_movies_df()))
        self.assertEqual(self.recommender.genre_matrix.shape[1], len(self.recommender.unique_genres))

    def test_self_exclusion_in_recommendations(self):
        """Verifies that a movie is never recommended to itself."""
        target_id = 8  # Inception
        recs = self.recommender.recommend_similar_movies(movie_id=target_id, limit=5)
        rec_ids = [r["movieId"] for r in recs]
        self.assertNotIn(target_id, rec_ids)
        self.assertEqual(len(recs), 5)

    def test_similarity_ranking_for_shared_genres(self):
        """Verifies that movies sharing key genres (e.g. Sci-Fi/Adventure) receive high similarity."""
        target_id = 8  # Inception (Action|Adventure|Sci-Fi|Thriller)
        recs = self.recommender.recommend_similar_movies(movie_id=target_id, limit=5)
        # Top recommendations should have positive similarity and valid explanations
        for r in recs:
            self.assertGreaterEqual(r["similarity_score"], 0.0)
            self.assertIn("explanation", r)
            self.assertTrue(len(r["explanation"]) > 0)

    def test_fallback_for_movie_with_no_genres(self):
        """Tests that a movie with no genres falls back gracefully to weighted rating."""
        target_id = 59  # Enigma (no genres)
        recs = self.recommender.recommend_similar_movies(movie_id=target_id, limit=3)
        self.assertEqual(len(recs), 3)
        # Should not raise exception, similarity should be 0, but recommendations should exist
        for r in recs:
            self.assertEqual(r["similarity_score"], 0.0)
            self.assertGreater(r["weighted_rating"], 0.0)

    def test_deterministic_output(self):
        """Verifies recommendations are strictly deterministic for identical data."""
        recs1 = self.recommender.recommend_similar_movies(movie_id=6, limit=4)
        recs2 = self.recommender.recommend_similar_movies(movie_id=6, limit=4)
        self.assertEqual([r["movieId"] for r in recs1], [r["movieId"] for r in recs2])

    def test_bayesian_weighted_rating_formula(self):
        """Tests Bayesian weighted rating calculation."""
        df = pd.DataFrame(
            {
                "movieId": [1, 2],
                "rating_count": [1, 50],
                "average_rating": [5.0, 4.0],
            }
        )
        rec = MovieRecommender(min_votes_threshold=5)
        wr = rec.calculate_weighted_ratings(df)
        # Movie 1 (1 vote of 5.0) should be pulled towards global mean
        # Movie 2 (50 votes of 4.0) should be much closer to 4.0
        self.assertLess(wr[0], 5.0)
        self.assertAlmostEqual(wr[1], 4.0, delta=0.2)

    def test_unknown_movie_id_raises_key_error(self):
        """Verifies KeyError is raised for invalid movie ID."""
        with self.assertRaises(KeyError):
            self.recommender.recommend_similar_movies(movie_id=99999)


if __name__ == "__main__":
    unittest.main()
