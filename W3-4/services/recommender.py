"""
MovieRecommender Service for MovieScope
Implements content-based genre similarity (multi-hot encoding + NumPy cosine similarity)
combined with Bayesian weighted ratings (IMDb formula) for robust, deterministic recommendations.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class MovieRecommender:
    """Content-based & rating-aware movie recommendation engine."""

    def __init__(self, data_manager: Optional[Any] = None, min_votes_threshold: int = 5):
        self.data_manager = data_manager
        self.min_votes = min_votes_threshold

        self.unique_genres: List[str] = []
        self.genre_matrix: np.ndarray = np.empty((0, 0))
        self.movie_ids: List[int] = []
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}

        self.global_mean_rating: float = 3.5
        self.weighted_ratings: np.ndarray = np.array([])

        if self.data_manager is not None:
            self.fit()

    def fit(self, data_manager: Optional[Any] = None) -> None:
        """Fits recommendation structures to current dataset."""
        if data_manager:
            self.data_manager = data_manager

        if self.data_manager is None:
            return

        merged_df = self.data_manager.get_merged_data()
        if merged_df.empty:
            self.unique_genres = []
            self.genre_matrix = np.empty((0, 0))
            return

        self.movie_ids = merged_df["movieId"].tolist()
        self.movie_id_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie_id = {i: mid for i, mid in enumerate(self.movie_ids)}

        # Build genre vocabulary
        all_genres = set()
        for genres in merged_df["genre_list"]:
            for g in genres:
                if g and g != "Unknown":
                    all_genres.add(g)

        self.unique_genres = sorted(list(all_genres))
        genre_to_col = {g: i for i, g in enumerate(self.unique_genres)}

        # Build binary multi-hot matrix
        num_movies = len(merged_df)
        num_genres = len(self.unique_genres)

        if num_genres > 0:
            matrix = np.zeros((num_movies, num_genres), dtype=np.float32)
            for row_idx, genres in enumerate(merged_df["genre_list"]):
                for g in genres:
                    if g in genre_to_col:
                        matrix[row_idx, genre_to_col[g]] = 1.0
            self.genre_matrix = matrix
        else:
            self.genre_matrix = np.zeros((num_movies, 1), dtype=np.float32)

        # Precompute Bayesian Weighted Ratings
        self.calculate_weighted_ratings(merged_df)

    def calculate_weighted_ratings(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calculates Bayesian Weighted Rating for all movies using the formula:
        WR = (v / (v + m)) * R + (m / (v + m)) * C
        Where:
          v = rating count
          m = minimum rating threshold
          R = movie average rating
          C = global mean rating
        """
        if df.empty or "average_rating" not in df.columns:
            self.weighted_ratings = np.array([])
            return self.weighted_ratings

        v = df["rating_count"].to_numpy(dtype=np.float32)
        r = df["average_rating"].to_numpy(dtype=np.float32)

        # Compute global average of rated movies
        rated_mask = v > 0
        if np.any(rated_mask):
            self.global_mean_rating = float(np.mean(r[rated_mask]))
        else:
            self.global_mean_rating = 3.5

        c = self.global_mean_rating
        m = float(self.min_votes)

        # Vectorized formula
        denom = v + m
        valid_denom = denom > 0
        wr = np.full_like(v, c, dtype=np.float32)
        np.divide(v * r + m * c, denom, out=wr, where=valid_denom)
        # For movies with 0 ratings, set to C * 0.7 or neutral
        wr = np.where(v > 0, wr, c * 0.7)

        self.weighted_ratings = wr.round(2)
        return self.weighted_ratings

    def calculate_similarity(self, target_idx: int) -> np.ndarray:
        """Computes cosine similarity between target movie and all movies in genre matrix."""
        if self.genre_matrix.size == 0 or target_idx >= len(self.genre_matrix):
            return np.zeros(len(self.movie_ids), dtype=np.float32)

        target_vec = self.genre_matrix[target_idx]
        norm_target = np.linalg.norm(target_vec)

        if norm_target == 0:
            # Target movie has no genres
            return np.zeros(len(self.movie_ids), dtype=np.float32)

        dot_prods = np.dot(self.genre_matrix, target_vec)
        norms = np.linalg.norm(self.genre_matrix, axis=1)

        # Vectorized cosine similarity avoiding divide by zero warnings
        denom = norm_target * norms
        similarities = np.zeros_like(dot_prods, dtype=np.float32)
        valid_mask = denom > 0
        np.divide(dot_prods, denom, out=similarities, where=valid_mask)
        return similarities

    def get_recommendation_explanation(
        self, target_title: str, target_genres: List[str], cand_genres: List[str], cand_rating: float, cand_votes: int
    ) -> str:
        """Generates clear, human-readable rationale for recommendation."""
        shared = [g for g in target_genres if g in cand_genres and g != "Unknown"]
        if shared:
            genre_text = ", ".join(shared)
            explanation = f"Shares {genre_text} with {target_title}."
        else:
            explanation = "Recommended based on overall top audience rating and popularity."

        if cand_votes >= 10:
            explanation += f" Strongly rated ({cand_rating:.1f}★ across {cand_votes} reviews)."
        elif cand_votes > 0:
            explanation += f" Audience rating: {cand_rating:.1f}★ ({cand_votes} reviews)."

        return explanation

    def recommend_similar_movies(self, movie_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recommends top similar movies for a given movie_id.
        Combines Genre Cosine Similarity (65% weight) and Normalized Weighted Rating (35% weight).
        Excludes the movie itself.
        """
        if self.data_manager is None:
            return []

        merged_df = self.data_manager.get_merged_data()
        if merged_df.empty:
            return []

        movie_id = int(movie_id)
        if movie_id not in self.movie_id_to_idx:
            raise KeyError(f"Movie ID {movie_id} not found in dataset.")

        target_idx = self.movie_id_to_idx[movie_id]
        target_row = merged_df.iloc[target_idx]
        target_title = target_row["title"]
        target_genres = target_row["genre_list"]

        # Compute similarities
        sim_scores = self.calculate_similarity(target_idx)
        has_genre_sim = bool(np.any(sim_scores > 0))

        # Normalize weighted ratings [0, 1]
        norm_wr = np.clip(self.weighted_ratings / 5.0, 0.0, 1.0)

        # Combined scoring:
        # If target has genre vector: 65% similarity + 35% weighted rating
        # If target has no genres: 100% weighted rating
        if has_genre_sim:
            combined_scores = 0.65 * sim_scores + 0.35 * norm_wr
        else:
            combined_scores = norm_wr

        # Rank candidates, excluding target movie
        ranked_indices = np.argsort(-combined_scores)

        results = []
        for idx in ranked_indices:
            if idx == target_idx:
                continue  # Exclude self

            cand_row = merged_df.iloc[idx]
            cand_id = int(cand_row["movieId"])
            cand_genres = cand_row["genre_list"]
            cand_rating = float(cand_row["average_rating"])
            cand_votes = int(cand_row["rating_count"])

            sim_val = float(sim_scores[idx]) if has_genre_sim else 0.0
            wr_val = float(self.weighted_ratings[idx]) if len(self.weighted_ratings) > idx else cand_rating
            final_score = float(combined_scores[idx])

            explanation = self.get_recommendation_explanation(
                target_title, target_genres, cand_genres, cand_rating, cand_votes
            )

            results.append(
                {
                    "movieId": cand_id,
                    "title": cand_row["title"],
                    "release_year": int(cand_row["release_year"]) if pd.notna(cand_row["release_year"]) else None,
                    "genres": cand_row["genres"],
                    "genre_list": cand_genres,
                    "average_rating": cand_rating,
                    "rating_count": cand_votes,
                    "similarity_score": round(sim_val, 3),
                    "weighted_rating": round(wr_val, 2),
                    "combined_score": round(final_score, 3),
                    "explanation": explanation,
                }
            )

            if len(results) >= limit:
                break

        return results
