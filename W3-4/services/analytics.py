"""
AnalyticsEngine Service for MovieScope
Computes statistical metrics, aggregations, distributions, correlations,
time trends, exports, and generates Matplotlib / Seaborn visualization charts.
"""

from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for Flask
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


class AnalyticsEngine:
    """Computes analytics and renders visualizations for MovieScope."""

    CHARTS_DIR = Path(__file__).resolve().parent.parent / "static" / "charts"

    # Styling colors for clean light analytics theme (white background, crisp dark text, vibrant accents)
    THEME_COLORS = {
        "bg": "#ffffff",
        "card_bg": "#ffffff",
        "accent_blue": "#2563eb",
        "accent_teal": "#0d9488",
        "accent_cyan": "#0284c7",
        "accent_emerald": "#10b981",
        "accent_amber": "#f59e0b",
        "accent_coral": "#f43f5e",
        "text": "#0f172a",
        "text_muted": "#64748b",
        "grid": "#e2e8f0",
        "border": "#cbd5e1",
    }

    def __init__(self, data_manager: Optional[Any] = None):
        self.data_manager = data_manager
        self.CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    def set_data_manager(self, data_manager: Any) -> None:
        """Sets or updates the active DataManager."""
        self.data_manager = data_manager

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculates live KPI metrics for dashboard overview."""
        if not self.data_manager:
            return {}

        movies_df = self.data_manager.get_movies_df()
        ratings_df = self.data_manager.get_ratings_df()
        merged_df = self.data_manager.get_merged_data()

        total_movies = len(movies_df)
        total_ratings = len(ratings_df)
        unique_users = int(ratings_df["userId"].nunique()) if not ratings_df.empty else 0

        # Unique genres count
        unique_genres = set()
        for genres in movies_df["genre_list"]:
            for g in genres:
                if g and g != "Unknown":
                    unique_genres.add(g)
        num_genres = len(unique_genres)

        # Overall average rating
        overall_avg = float(ratings_df["rating"].mean()) if not ratings_df.empty else 0.0

        # Highest rated movie (with threshold: min 5 ratings if available, else max votes)
        highest_rated = None
        if not merged_df.empty:
            eligible = merged_df[merged_df["rating_count"] >= 5]
            if eligible.empty:
                eligible = merged_df[merged_df["rating_count"] > 0]

            if not eligible.empty:
                # Sort by average_rating desc, then rating_count desc
                top_row = eligible.sort_values(
                    by=["average_rating", "rating_count"], ascending=[False, False]
                ).iloc[0]
                highest_rated = {
                    "movieId": int(top_row["movieId"]),
                    "title": top_row["title"],
                    "average_rating": float(top_row["average_rating"]),
                    "rating_count": int(top_row["rating_count"]),
                }

        return {
            "total_movies": total_movies,
            "total_ratings": total_ratings,
            "unique_users": unique_users,
            "num_genres": num_genres,
            "overall_average_rating": round(overall_avg, 2),
            "highest_rated_movie": highest_rated,
        }

    def get_movie_summary(
        self,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        min_rating: Optional[float] = None,
        min_votes: Optional[int] = None,
        sort_by: str = "rating",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 12,
    ) -> Dict[str, Any]:
        """Filters, sorts, and paginates movies."""
        if not self.data_manager:
            return {"items": [], "total_count": 0, "page": 1, "total_pages": 0}

        df = self.data_manager.get_merged_data().copy()

        # 1. Search by title
        if search and search.strip():
            term = search.strip().lower()
            df = df[df["title"].str.lower().str.contains(term, regex=False)]

        # 2. Filter by genre
        if genre and genre.strip() and genre.lower() != "all":
            selected_genre = genre.strip()
            df = df[df["genre_list"].apply(lambda g_list: selected_genre in g_list)]

        # 3. Filter by minimum rating
        if min_rating is not None and min_rating > 0:
            df = df[df["average_rating"] >= float(min_rating)]

        # 4. Filter by minimum ratings count
        if min_votes is not None and min_votes > 0:
            df = df[df["rating_count"] >= int(min_votes)]

        total_count = len(df)

        # 5. Sorting
        ascending = sort_order.lower() == "asc"
        if sort_by == "title":
            df = df.sort_values(by="title", ascending=ascending)
        elif sort_by == "popularity":
            df = df.sort_values(by="rating_count", ascending=ascending)
        elif sort_by == "year":
            df = df.sort_values(by="release_year", ascending=ascending, na_position="last")
        else:  # default 'rating'
            df = df.sort_values(by=["average_rating", "rating_count"], ascending=[ascending, ascending])

        # 6. Pagination
        page = max(1, int(page))
        page_size = max(1, min(100, int(page_size)))
        total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_df = df.iloc[start_idx:end_idx]

        items = []
        for _, row in paged_df.iterrows():
            items.append(
                {
                    "movieId": int(row["movieId"]),
                    "title": row["title"],
                    "release_year": int(row["release_year"]) if pd.notna(row["release_year"]) else None,
                    "genres": row["genres"],
                    "genre_list": row["genre_list"],
                    "average_rating": float(row["average_rating"]),
                    "rating_count": int(row["rating_count"]),
                }
            )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_top_rated_movies(self, limit: int = 10, min_ratings: int = 5) -> List[Dict[str, Any]]:
        """Returns top-ranked movies subject to minimum ratings count threshold."""
        if not self.data_manager:
            return []

        df = self.data_manager.get_merged_data()
        if df.empty:
            return []

        eligible = df[df["rating_count"] >= min_ratings]
        if eligible.empty:
            eligible = df[df["rating_count"] > 0]

        top = eligible.sort_values(by=["average_rating", "rating_count"], ascending=[False, False]).head(limit)

        results = []
        for _, row in top.iterrows():
            results.append(
                {
                    "movieId": int(row["movieId"]),
                    "title": row["title"],
                    "release_year": int(row["release_year"]) if pd.notna(row["release_year"]) else None,
                    "genres": row["genres"],
                    "average_rating": float(row["average_rating"]),
                    "rating_count": int(row["rating_count"]),
                }
            )
        return results

    def get_genre_statistics(self) -> List[Dict[str, Any]]:
        """
        Calculates genre-level statistics.
        Multi-genre movies correctly contribute to all their constituent genre categories.
        """
        if not self.data_manager:
            return []

        df = self.data_manager.get_merged_data()
        if df.empty:
            return []

        # Explode genre_list so multi-genre movies contribute to each
        exploded = df.explode("genre_list")
        exploded = exploded[exploded["genre_list"].notna() & (exploded["genre_list"] != "") & (exploded["genre_list"] != "Unknown")]

        if exploded.empty:
            return []

        stats = (
            exploded.groupby("genre_list")
            .agg(
                movie_count=("movieId", "count"),
                average_rating=("average_rating", lambda s: s[s > 0].mean() if len(s[s > 0]) > 0 else 0.0),
                total_ratings=("rating_count", "sum"),
            )
            .reset_index()
        )

        stats["average_rating"] = stats["average_rating"].round(2)
        stats = stats.sort_values(by="movie_count", ascending=False)

        results = []
        for _, row in stats.iterrows():
            results.append(
                {
                    "genre": str(row["genre_list"]),
                    "movie_count": int(row["movie_count"]),
                    "average_rating": float(row["average_rating"]),
                    "total_ratings": int(row["total_ratings"]),
                }
            )
        return results

    def get_rating_distribution(self) -> Dict[str, Any]:
        """Returns statistical distribution of user ratings and movie averages."""
        if not self.data_manager:
            return {}

        ratings_df = self.data_manager.get_ratings_df()
        merged_df = self.data_manager.get_merged_data()

        if ratings_df.empty:
            return {"user_ratings_dist": {}, "movie_avg_dist": {}, "stats": {}}

        # Distribution of individual user ratings (0.5 to 5.0)
        user_counts = ratings_df["rating"].value_counts().sort_index().to_dict()
        user_dist = {str(k): int(v) for k, v in user_counts.items()}

        # Numerical calculations with NumPy
        ratings_arr = ratings_df["rating"].to_numpy()
        summary_stats = {
            "mean": round(float(np.mean(ratings_arr)), 2),
            "median": round(float(np.median(ratings_arr)), 2),
            "std": round(float(np.std(ratings_arr)), 2),
            "q25": round(float(np.percentile(ratings_arr, 25)), 2),
            "q75": round(float(np.percentile(ratings_arr, 75)), 2),
            "min": float(np.min(ratings_arr)),
            "max": float(np.max(ratings_arr)),
        }

        # Movie average rating histogram bins
        valid_movie_avgs = merged_df[merged_df["rating_count"] > 0]["average_rating"].to_numpy()
        counts, bin_edges = np.histogram(valid_movie_avgs, bins=10, range=(1.0, 5.0))
        movie_avg_bins = [
            {"range": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}", "count": int(counts[i])}
            for i in range(len(counts))
        ]

        return {
            "user_ratings_dist": user_dist,
            "movie_avg_bins": movie_avg_bins,
            "stats": summary_stats,
        }

    def get_rating_year_trends(self) -> List[Dict[str, Any]]:
        """Groups movies and ratings by release year/decade."""
        if not self.data_manager:
            return []

        df = self.data_manager.get_merged_data()
        valid_years = df[df["release_year"].notna() & (df["release_year"] > 1900)].copy()

        if valid_years.empty:
            return []

        # Decade or yearly aggregation
        valid_years["decade"] = (valid_years["release_year"] // 10) * 10
        trends = (
            valid_years.groupby("decade")
            .agg(
                movie_count=("movieId", "count"),
                average_rating=("average_rating", lambda s: s[s > 0].mean() if len(s[s > 0]) > 0 else 0.0),
                total_votes=("rating_count", "sum"),
            )
            .reset_index()
            .sort_values(by="decade")
        )

        trends["average_rating"] = trends["average_rating"].round(2)
        return [
            {
                "decade": f"{int(r['decade'])}s",
                "movie_count": int(r["movie_count"]),
                "average_rating": float(r["average_rating"]),
                "total_votes": int(r["total_votes"]),
            }
            for _, r in trends.iterrows()
        ]

    def get_movie_distribution(self, movie_id: int) -> Dict[str, Any]:
        """Returns ratings distribution for a single movie."""
        if not self.data_manager:
            return {}

        ratings_df = self.data_manager.get_ratings_df()
        movie_ratings = ratings_df[ratings_df["movieId"] == int(movie_id)]

        if movie_ratings.empty:
            return {"movieId": movie_id, "counts": {}, "total": 0}

        counts = movie_ratings["rating"].value_counts().sort_index().to_dict()
        formatted_counts = {str(k): int(v) for k, v in counts.items()}

        return {
            "movieId": movie_id,
            "counts": formatted_counts,
            "total": len(movie_ratings),
            "average": round(float(movie_ratings["rating"].mean()), 2),
        }

    # ----------------------------------------------------------------------
    # Matplotlib & Seaborn Chart Generators
    # ----------------------------------------------------------------------

    def _setup_chart_style(self, fig, ax, title: str, xlabel: str, ylabel: str) -> None:
        """Applies clean, bright modern chart styling."""
        fig.patch.set_facecolor(self.THEME_COLORS["card_bg"])
        ax.set_facecolor(self.THEME_COLORS["card_bg"])

        ax.set_title(title, fontsize=13, fontweight="bold", color=self.THEME_COLORS["text"], pad=14)
        ax.set_xlabel(xlabel, fontsize=11, color=self.THEME_COLORS["text_muted"], labelpad=8)
        ax.set_ylabel(ylabel, fontsize=11, color=self.THEME_COLORS["text_muted"], labelpad=8)

        ax.tick_params(colors=self.THEME_COLORS["text_muted"], labelsize=10)
        ax.grid(color=self.THEME_COLORS["grid"], linestyle="--", linewidth=0.8, alpha=0.8)

        for spine in ax.spines.values():
            spine.set_color(self.THEME_COLORS["border"])

    def generate_rating_histogram(self, filename: str = "ratings_distribution.png") -> Path:
        """Chart 1: Distribution of Individual Movie Ratings using Seaborn."""
        out_path = self.CHARTS_DIR / filename
        ratings_df = self.data_manager.get_ratings_df() if self.data_manager else pd.DataFrame()

        fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)

        if ratings_df.empty:
            ax.text(0.5, 0.5, "No rating data available", ha="center", va="center", color=self.THEME_COLORS["text_muted"])
            self._setup_chart_style(fig, ax, "Rating Distribution", "Rating Value", "Frequency")
        else:
            sns.histplot(
                data=ratings_df,
                x="rating",
                bins=10,
                kde=True,
                color=self.THEME_COLORS["accent_blue"],
                edgecolor="#1d4ed8",
                alpha=0.85,
                ax=ax,
            )
            ax.set_xticks(np.arange(0.5, 5.5, 0.5))
            self._setup_chart_style(
                fig,
                ax,
                "Distribution of User Ratings (0.5 to 5.0 Stars)",
                "Rating Value (★)",
                "Number of Ratings Submitted",
            )

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_genre_chart(self, filename: str = "genres_chart.png") -> Path:
        """Chart 2: Average Rating by Genre (Sorted Bar Chart)."""
        out_path = self.CHARTS_DIR / filename
        genre_stats = self.get_genre_statistics()

        fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)

        if not genre_stats:
            ax.text(0.5, 0.5, "No genre statistics available", ha="center", va="center", color=self.THEME_COLORS["text_muted"])
            self._setup_chart_style(fig, ax, "Average Rating by Genre", "Genre", "Rating")
        else:
            # Sort by average rating
            sorted_genres = sorted(genre_stats, key=lambda x: x["average_rating"], reverse=True)[:12]
            genres = [x["genre"] for x in sorted_genres]
            ratings = [x["average_rating"] for x in sorted_genres]
            counts = [x["movie_count"] for x in sorted_genres]

            bars = ax.bar(genres, ratings, color=self.THEME_COLORS["accent_teal"], edgecolor="#0f766e", alpha=0.88)

            # Annotate bar values
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.annotate(
                    f"{height:.1f}★\n(n={count})",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=self.THEME_COLORS["text"],
                )

            ax.set_ylim(0, 5.5)
            plt.xticks(rotation=35, ha="right")
            self._setup_chart_style(
                fig,
                ax,
                "Average Rating by Genre (Top Genres by Score)",
                "Genre (Multi-genre movies contribute to each category)",
                "Average Rating (★)",
            )

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_popularity_chart(self, filename: str = "ratings_popularity.png") -> Path:
        """Chart 3: Ratings Versus Popularity (Scatter Plot)."""
        out_path = self.CHARTS_DIR / filename
        df = self.data_manager.get_merged_data() if self.data_manager else pd.DataFrame()

        fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)

        if df.empty or df["rating_count"].max() == 0:
            ax.text(0.5, 0.5, "No rating count data available", ha="center", va="center", color=self.THEME_COLORS["text_muted"])
            self._setup_chart_style(fig, ax, "Ratings vs Popularity", "Rating Count", "Average Rating")
        else:
            rated_df = df[df["rating_count"] > 0]
            sns.scatterplot(
                data=rated_df,
                x="rating_count",
                y="average_rating",
                color=self.THEME_COLORS["accent_cyan"],
                alpha=0.88,
                s=65,
                edgecolor="#0284c7",
                ax=ax,
            )

            # Trend line if >= 3 data points
            if len(rated_df) >= 3:
                sns.regplot(
                    data=rated_df,
                    x="rating_count",
                    y="average_rating",
                    scatter=False,
                    color=self.THEME_COLORS["accent_coral"],
                    ax=ax,
                    line_kws={"linewidth": 1.8, "linestyle": "--"},
                )

            self._setup_chart_style(
                fig,
                ax,
                "Ratings vs Popularity (Number of Reviews vs Quality)",
                "Number of Ratings (Popularity)",
                "Average Rating (★)",
            )
            ax.set_ylim(0.5, 5.2)

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_correlation_heatmap(self, filename: str = "correlation_heatmap.png") -> Path:
        """Chart 4: Numerical Feature Correlation Heatmap using Seaborn."""
        out_path = self.CHARTS_DIR / filename
        df = self.data_manager.get_merged_data() if self.data_manager else pd.DataFrame()

        fig, ax = plt.subplots(figsize=(7, 5.2), dpi=150)

        numeric_cols = ["average_rating", "rating_count", "rating_std", "release_year"]
        available_cols = [c for c in numeric_cols if c in df.columns]

        if df.empty or len(df) < 3 or len(available_cols) < 2:
            ax.text(0.5, 0.5, "Insufficient numeric data for correlation", ha="center", va="center", color=self.THEME_COLORS["text_muted"])
            self._setup_chart_style(fig, ax, "Correlation Heatmap", "", "")
        else:
            corr_df = df[available_cols].dropna().corr()
            col_labels = {
                "average_rating": "Avg Rating",
                "rating_count": "Rating Count",
                "rating_std": "Rating StdDev",
                "release_year": "Release Year",
            }
            corr_df = corr_df.rename(index=col_labels, columns=col_labels)

            sns.heatmap(
                corr_df,
                annot=True,
                fmt=".2f",
                cmap="Blues",
                vmin=-1.0,
                vmax=1.0,
                linewidths=1.5,
                linecolor="#ffffff",
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )

            fig.patch.set_facecolor(self.THEME_COLORS["card_bg"])
            ax.set_facecolor(self.THEME_COLORS["card_bg"])
            ax.set_title("Numerical Correlation Matrix", fontsize=13, fontweight="bold", color=self.THEME_COLORS["text"], pad=14)
            ax.tick_params(colors=self.THEME_COLORS["text_muted"], labelsize=10)

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_trends_chart(self, filename: str = "trends_chart.png") -> Path:
        """Chart 5: Release Decade Trends in Ratings & Film Output."""
        out_path = self.CHARTS_DIR / filename
        trends = self.get_rating_year_trends()

        fig, ax1 = plt.subplots(figsize=(8, 4.8), dpi=150)

        if not trends:
            ax1.text(0.5, 0.5, "No release year trends available", ha="center", va="center", color=self.THEME_COLORS["text_muted"])
            self._setup_chart_style(fig, ax1, "Decade Trends", "Decade", "Average Rating")
        else:
            decades = [t["decade"] for t in trends]
            ratings = [t["average_rating"] for t in trends]
            counts = [t["movie_count"] for t in trends]

            # Line plot for ratings
            ax1.plot(decades, ratings, color=self.THEME_COLORS["accent_blue"], marker="o", linewidth=2.5, label="Avg Rating")
            ax1.set_ylim(2.0, 5.0)

            # Secondary axis for movie counts
            ax2 = ax1.twinx()
            ax2.bar(decades, counts, color=self.THEME_COLORS["accent_teal"], alpha=0.35, width=0.4, label="Film Count")
            ax2.set_ylabel("Number of Films", color=self.THEME_COLORS["text_muted"], fontsize=11, labelpad=8)
            ax2.tick_params(colors=self.THEME_COLORS["text_muted"], labelsize=10)

            self._setup_chart_style(fig, ax1, "Movie Trends Across Release Decades", "Release Decade", "Average Rating (★)")

            # Combined legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", facecolor=self.THEME_COLORS["card_bg"], edgecolor=self.THEME_COLORS["grid"], labelcolor=self.THEME_COLORS["text"])

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    # ----------------------------------------------------------------------
    # Export Helpers (CSV & Plain Text Report)
    # ----------------------------------------------------------------------

    def export_filtered_movies(self, **kwargs) -> str:
        """Generates CSV string of movies matching filters."""
        summary = self.get_movie_summary(page=1, page_size=10000, **kwargs)
        df = pd.DataFrame(summary["items"])
        if df.empty:
            return "movieId,title,release_year,genres,average_rating,rating_count\n"
        output = StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    def export_genre_statistics(self) -> str:
        """Generates CSV string of genre analysis."""
        genres = self.get_genre_statistics()
        df = pd.DataFrame(genres)
        if df.empty:
            return "genre,movie_count,average_rating,total_ratings\n"
        output = StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    def export_top_movies(self, min_ratings: int = 5) -> str:
        """Generates CSV string of top-rated movies."""
        top = self.get_top_rated_movies(limit=100, min_ratings=min_ratings)
        df = pd.DataFrame(top)
        if df.empty:
            return "movieId,title,release_year,genres,average_rating,rating_count\n"
        output = StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    def export_analysis_report(self) -> str:
        """Generates comprehensive plain-text analysis report."""
        stats = self.get_dashboard_stats()
        quality = self.data_manager.get_data_quality_report() if self.data_manager else {}
        genres = self.get_genre_statistics()
        top_movies = self.get_top_rated_movies(limit=5)

        lines = [
            "==================================================================",
            "                 MOVIESCOPE ANALYTICAL REPORT                     ",
            "==================================================================",
            f"Dataset Source:          {quality.get('source', 'Unknown')}",
            f"Total Movies:            {stats.get('total_movies', 0)}",
            f"Total Ratings:           {stats.get('total_ratings', 0)}",
            f"Unique Users:            {stats.get('unique_users', 0)}",
            f"Unique Genres:           {stats.get('num_genres', 0)}",
            f"Overall Mean Rating:     {stats.get('overall_average_rating', 0.0)}★",
            "",
            "------------------------------------------------------------------",
            "DATA INTEGRITY & QUALITY",
            "------------------------------------------------------------------",
            f"- Valid Movies Retained:       {quality.get('movies_valid', 0)}",
            f"- Movie Duplicates Removed:    {quality.get('movie_duplicates_removed', 0)}",
            f"- Valid Ratings Retained:      {quality.get('ratings_valid', 0)}",
            f"- Rating Duplicates Removed:   {quality.get('ratings_duplicates_removed', 0)}",
            f"- Out-of-Range Ratings:        {quality.get('ratings_invalid_range_removed', 0)}",
            "",
            "------------------------------------------------------------------",
            "TOP 5 HIGHEST RATED FILMS (Min 5 Reviews)",
            "------------------------------------------------------------------",
        ]

        for i, m in enumerate(top_movies, 1):
            lines.append(f"{i}. {m['title']} — {m['average_rating']}★ ({m['rating_count']} reviews)")

        lines.extend([
            "",
            "------------------------------------------------------------------",
            "TOP GENRES BY MOVIE COUNT",
            "------------------------------------------------------------------",
        ])

        for g in genres[:8]:
            lines.append(f"- {g['genre']:<15} {g['movie_count']} films | {g['average_rating']}★ avg | {g['total_ratings']} reviews")

        lines.extend([
            "",
            "==================================================================",
            "End of MovieScope Report.",
            "==================================================================",
        ])

        return "\n".join(lines)
