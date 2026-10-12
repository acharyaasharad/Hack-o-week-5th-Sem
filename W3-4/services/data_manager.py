"""
DataManager Service for MovieScope
Handles CSV loading, column validation, cleaning, deduplication, merging,
and data quality reporting using Pandas.
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


class DataManager:
    """Manages dataset loading, validation, cleaning, and merging."""

    DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else self.DEFAULT_DATA_DIR
        self.sample_movies_path = self.data_dir / "movies.csv"
        self.sample_ratings_path = self.data_dir / "ratings.csv"

        self.movies_raw: pd.DataFrame = pd.DataFrame()
        self.ratings_raw: pd.DataFrame = pd.DataFrame()

        self.movies_df: pd.DataFrame = pd.DataFrame()
        self.ratings_df: pd.DataFrame = pd.DataFrame()
        self.merged_df: pd.DataFrame = pd.DataFrame()

        self.source_type: str = "Sample Dataset"
        self.quality_report: Dict[str, Any] = {}

        # Auto-load initial data if available
        if self.sample_movies_path.exists() and self.sample_ratings_path.exists():
            self.load_data(self.sample_movies_path, self.sample_ratings_path, source="Sample Dataset")

    def validate_columns(self, df: pd.DataFrame, required_columns: List[str], dataset_name: str) -> None:
        """Validates that all required columns are present in the DataFrame."""
        if df.empty:
            raise ValueError(f"{dataset_name} is empty.")
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"{dataset_name} is missing required columns: {', '.join(missing)}")

    def load_movies(self, path: Path) -> pd.DataFrame:
        """Loads and parses movies CSV."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Movies file not found: {path}")
        df = pd.read_csv(path)
        self.validate_columns(df, ["movieId", "title", "genres"], "Movies dataset")
        return df

    def load_ratings(self, path: Path) -> pd.DataFrame:
        """Loads and parses ratings CSV."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Ratings file not found: {path}")
        df = pd.read_csv(path)
        self.validate_columns(df, ["userId", "movieId", "rating"], "Ratings dataset")
        if "timestamp" not in df.columns:
            df["timestamp"] = 0
        return df

    def extract_year(self, title: str) -> Optional[int]:
        """Extracts release year from title string e.g. 'Inception (2010)'."""
        if not isinstance(title, str):
            return None
        match = re.search(r"\((\d{4})\)", title)
        if match:
            year = int(match.group(1))
            if 1880 <= year <= 2035:
                return year
        return None

    def clean_movies(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Cleans and standardizes movie records."""
        stats = {
            "initial_rows": len(df),
            "duplicates_removed": 0,
            "missing_titles_removed": 0,
            "missing_genres_fixed": 0,
        }

        cleaned = df.copy()

        # Coerce movieId to numeric
        cleaned["movieId"] = pd.to_numeric(cleaned["movieId"], errors="coerce")
        cleaned = cleaned.dropna(subset=["movieId"])
        cleaned["movieId"] = cleaned["movieId"].astype(int)

        # Drop duplicate movieId
        dup_count = cleaned.duplicated(subset=["movieId"]).sum()
        stats["duplicates_removed"] = int(dup_count)
        cleaned = cleaned.drop_duplicates(subset=["movieId"], keep="first")

        # Clean titles
        cleaned["title"] = cleaned["title"].astype(str).str.strip()
        invalid_titles = cleaned["title"].isna() | (cleaned["title"] == "")
        stats["missing_titles_removed"] = int(invalid_titles.sum())
        cleaned = cleaned[~invalid_titles]

        # Extract release year
        cleaned["release_year"] = cleaned["title"].apply(self.extract_year)

        # Clean genres: fill missing with 'Unknown'
        cleaned["genres"] = cleaned["genres"].fillna("Unknown").astype(str).str.strip()
        cleaned.loc[cleaned["genres"] == "", "genres"] = "Unknown"
        stats["missing_genres_fixed"] = int((cleaned["genres"] == "Unknown").sum())

        # Create structured genre list
        cleaned["genre_list"] = cleaned["genres"].apply(
            lambda g: [x.strip() for x in g.split("|") if x.strip() and x.strip() != "Unknown"]
        )

        return cleaned, stats

    def clean_ratings(
        self, df: pd.DataFrame, valid_movie_ids: set
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Cleans and validates rating records."""
        stats = {
            "initial_rows": len(df),
            "invalid_numeric_removed": 0,
            "out_of_range_removed": 0,
            "duplicates_removed": 0,
            "unknown_movie_removed": 0,
        }

        cleaned = df.copy()

        # Coerce numeric types
        cleaned["userId"] = pd.to_numeric(cleaned["userId"], errors="coerce")
        cleaned["movieId"] = pd.to_numeric(cleaned["movieId"], errors="coerce")
        cleaned["rating"] = pd.to_numeric(cleaned["rating"], errors="coerce")

        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_numeric(cleaned["timestamp"], errors="coerce").fillna(0)
        else:
            cleaned["timestamp"] = 0

        # Drop records with invalid numbers
        invalid_nums = cleaned[["userId", "movieId", "rating"]].isna().any(axis=1)
        stats["invalid_numeric_removed"] = int(invalid_nums.sum())
        cleaned = cleaned[~invalid_nums]

        cleaned["userId"] = cleaned["userId"].astype(int)
        cleaned["movieId"] = cleaned["movieId"].astype(int)
        cleaned["rating"] = cleaned["rating"].astype(float)
        cleaned["timestamp"] = cleaned["timestamp"].astype(int)

        # Range filter [0.5, 5.0]
        valid_range = (cleaned["rating"] >= 0.5) & (cleaned["rating"] <= 5.0)
        stats["out_of_range_removed"] = int((~valid_range).sum())
        cleaned = cleaned[valid_range]

        # Unknown movie IDs
        valid_movies_mask = cleaned["movieId"].isin(valid_movie_ids)
        stats["unknown_movie_removed"] = int((~valid_movies_mask).sum())
        cleaned = cleaned[valid_movies_mask]

        # Duplicate (userId, movieId) -> keep latest timestamp
        cleaned = cleaned.sort_values(by="timestamp", ascending=True)
        dup_count = cleaned.duplicated(subset=["userId", "movieId"], keep="last").sum()
        stats["duplicates_removed"] = int(dup_count)
        cleaned = cleaned.drop_duplicates(subset=["userId", "movieId"], keep="last")

        return cleaned, stats

    def load_data(self, movies_path: Path, ratings_path: Path, source: str = "Sample Dataset") -> bool:
        """Loads, cleans, and merges movies and ratings datasets."""
        self.source_type = source

        self.movies_raw = self.load_movies(movies_path)
        self.ratings_raw = self.load_ratings(ratings_path)

        # Clean movies
        cleaned_movies, movie_stats = self.clean_movies(self.movies_raw)
        self.movies_df = cleaned_movies
        valid_movie_ids = set(self.movies_df["movieId"].tolist())

        # Clean ratings
        cleaned_ratings, rating_stats = self.clean_ratings(self.ratings_raw, valid_movie_ids)
        self.ratings_df = cleaned_ratings

        # Precompute movie aggregates
        if not self.ratings_df.empty:
            rating_aggs = (
                self.ratings_df.groupby("movieId")
                .agg(
                    rating_count=("rating", "count"),
                    average_rating=("rating", "mean"),
                    rating_std=("rating", lambda s: s.std(ddof=0) if len(s) > 1 else 0.0),
                )
                .reset_index()
            )
            rating_aggs["average_rating"] = rating_aggs["average_rating"].round(2)
            rating_aggs["rating_std"] = rating_aggs["rating_std"].round(2)
        else:
            rating_aggs = pd.DataFrame(columns=["movieId", "rating_count", "average_rating", "rating_std"])

        # Merge with movies (Left Join to preserve movies with zero ratings)
        self.merged_df = pd.merge(self.movies_df, rating_aggs, on="movieId", how="left")
        self.merged_df["rating_count"] = self.merged_df["rating_count"].fillna(0).astype(int)
        self.merged_df["average_rating"] = self.merged_df["average_rating"].fillna(0.0).astype(float)
        self.merged_df["rating_std"] = self.merged_df["rating_std"].fillna(0.0).astype(float)

        # Build Quality Report
        total_unique_users = int(self.ratings_df["userId"].nunique()) if not self.ratings_df.empty else 0
        rated_movies_count = int(self.ratings_df["movieId"].nunique()) if not self.ratings_df.empty else 0
        unrated_movies_count = len(self.movies_df) - rated_movies_count

        ops = []
        if movie_stats["duplicates_removed"] > 0:
            ops.append(f"Removed {movie_stats['duplicates_removed']} duplicate movie records.")
        if movie_stats["missing_genres_fixed"] > 0:
            ops.append(f"Marked {movie_stats['missing_genres_fixed']} movies without genres as 'Unknown'.")
        if rating_stats["invalid_numeric_removed"] > 0:
            ops.append(f"Dropped {rating_stats['invalid_numeric_removed']} non-numeric rating entries.")
        if rating_stats["out_of_range_removed"] > 0:
            ops.append(f"Filtered {rating_stats['out_of_range_removed']} ratings outside [0.5, 5.0] range.")
        if rating_stats["duplicates_removed"] > 0:
            ops.append(f"Deduplicated {rating_stats['duplicates_removed']} user-movie pairs (kept latest timestamp).")
        if rating_stats["unknown_movie_removed"] > 0:
            ops.append(f"Excluded {rating_stats['unknown_movie_removed']} ratings referencing unknown movie IDs.")
        if not ops:
            ops.append("Dataset passed all integrity checks cleanly; standard type normalization applied.")

        self.quality_report = {
            "source": self.source_type,
            "movies_loaded": movie_stats["initial_rows"],
            "movies_valid": len(self.movies_df),
            "movie_duplicates_removed": movie_stats["duplicates_removed"],
            "ratings_loaded": rating_stats["initial_rows"],
            "ratings_valid": len(self.ratings_df),
            "ratings_duplicates_removed": rating_stats["duplicates_removed"],
            "ratings_invalid_range_removed": rating_stats["out_of_range_removed"],
            "ratings_unknown_movie_removed": rating_stats["unknown_movie_removed"],
            "total_unique_users": total_unique_users,
            "rated_movies_count": rated_movies_count,
            "unrated_movies_count": unrated_movies_count,
            "cleaning_operations": ops,
        }

        return True

    def reset_to_sample(self) -> bool:
        """Reloads the default bundled sample dataset."""
        return self.load_data(self.sample_movies_path, self.sample_ratings_path, source="Sample Dataset")

    def get_movies_df(self) -> pd.DataFrame:
        """Returns the cleaned movies DataFrame."""
        return self.movies_df

    def get_ratings_df(self) -> pd.DataFrame:
        """Returns the cleaned ratings DataFrame."""
        return self.ratings_df

    def get_merged_data(self) -> pd.DataFrame:
        """Returns the merged DataFrame with movie info and aggregated rating metrics."""
        return self.merged_df

    def get_movie(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Returns details for a single movie by ID."""
        row = self.merged_df[self.merged_df["movieId"] == int(movie_id)]
        if row.empty:
            return None
        record = row.iloc[0].to_dict()
        return record

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Returns the data quality report."""
        return self.quality_report
