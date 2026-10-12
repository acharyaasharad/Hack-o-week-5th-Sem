"""AnalyticsEngine service for Touchline Analytics.
Calculates dashboard KPIs, multi-dimensional football aggregations, distributions,
and match trends using Pandas and NumPy.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

from services.data_manager import DataManager
from utils.formatters import format_number, format_rating

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Core analytics engine computing statistical summaries and data science aggregations."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def set_data_manager(self, data_manager: DataManager) -> None:
        """Updates active DataManager."""
        self.data_manager = data_manager

    def get_dashboard_stats(self, season: Optional[str] = None, league: Optional[str] = None) -> Dict[str, Any]:
        """Calculates live KPI metrics and high-level charts for the dashboard overview."""
        players_df = self.data_manager.get_players_df()
        matches_df = self.data_manager.get_matches_df()

        if season and not players_df.empty and "season" in players_df.columns:
            players_df = players_df[players_df["season"] == season]
        if league and not players_df.empty and "league" in players_df.columns:
            players_df = players_df[players_df["league"] == league]

        if season and not matches_df.empty and "season" in matches_df.columns:
            matches_df = matches_df[matches_df["season"] == season]
        if league and not matches_df.empty and "league" in matches_df.columns:
            matches_df = matches_df[matches_df["league"] == league]

        # 6 Core KPI Values
        total_players = len(players_df)
        total_clubs = int(players_df["club"].nunique()) if not players_df.empty else 0
        total_competitions = int(players_df["league"].nunique()) if not players_df.empty else 0
        total_goals = int(players_df["goals"].sum()) if not players_df.empty else 0
        avg_rating = round(float(players_df["rating"].mean()), 2) if not players_df.empty else 0.0
        total_matches = len(matches_df)

        # 1. Goals and assists by position
        pos_summary = []
        if not players_df.empty:
            grouped = players_df.groupby("position").agg(
                goals=("goals", "sum"),
                assists=("assists", "sum"),
                count=("player_id", "count"),
                avg_rating=("rating", "mean"),
            ).reset_index()
            # Order logically
            order = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
            grouped["order"] = grouped["position"].map(lambda p: order.index(p) if p in order else 99)
            grouped = grouped.sort_values("order")
            for _, r in grouped.iterrows():
                pos_summary.append({
                    "position": r["position"],
                    "goals": int(r["goals"]),
                    "assists": int(r["assists"]),
                    "player_count": int(r["count"]),
                    "avg_rating": round(float(r["avg_rating"]), 2),
                })

        # 2. Rating distribution histogram bins
        rating_bins = []
        if not players_df.empty and "rating" in players_df.columns:
            ratings = players_df["rating"].dropna().values
            # 8 bins from 6.0 to 9.0
            counts, bin_edges = np.histogram(ratings, bins=np.linspace(6.0, 9.0, 7))
            for i in range(len(counts)):
                label = f"{bin_edges[i]:.1f} - {bin_edges[i+1]:.1f}"
                rating_bins.append({
                    "range": label,
                    "count": int(counts[i]),
                })

        # 3. Match goals over time
        match_trends = []
        if not matches_df.empty and "match_date" in matches_df.columns:
            m_copy = matches_df.copy()
            m_copy["month"] = m_copy["match_date"].dt.strftime("%Y-%m")
            m_grouped = m_copy.groupby("month").agg(
                total_goals=("total_goals", "sum"),
                match_count=("match_id", "count"),
            ).reset_index().sort_values("month")
            for _, r in m_grouped.iterrows():
                match_trends.append({
                    "period": r["month"],
                    "goals": int(r["total_goals"]),
                    "matches": int(r["match_count"]),
                    "avg_goals": round(float(r["total_goals"] / max(r["match_count"], 1)), 2),
                })

        # 4. League comparison
        league_comp = []
        if not players_df.empty:
            lg_grouped = players_df.groupby("league").agg(
                goals=("goals", "sum"),
                assists=("assists", "sum"),
                players=("player_id", "count"),
                avg_rating=("rating", "mean"),
            ).reset_index()
            for _, r in lg_grouped.iterrows():
                league_comp.append({
                    "league": r["league"],
                    "total_goals": int(r["goals"]),
                    "total_assists": int(r["assists"]),
                    "player_count": int(r["players"]),
                    "avg_rating": round(float(r["avg_rating"]), 2),
                })

        # 5. Top performers (min minutes >= 450)
        top_performers = []
        if not players_df.empty:
            eligible = players_df[players_df["minutes_played"] >= 450]
            if eligible.empty:
                eligible = players_df
            top_sorted = eligible.sort_values(by=["goals", "rating"], ascending=False).head(8)
            for idx, r in enumerate(top_sorted.itertuples(), 1):
                top_performers.append({
                    "rank": idx,
                    "player_id": int(r.player_id),
                    "player_name": r.player_name,
                    "club": r.club,
                    "league": r.league,
                    "position": r.position,
                    "goals": int(r.goals),
                    "assists": int(r.assists),
                    "goals_per_90": r.goals_per_90,
                    "rating": round(float(r.rating), 2),
                })

        return {
            "kpis": {
                "total_players": total_players,
                "total_clubs": total_clubs,
                "total_competitions": total_competitions,
                "total_goals": total_goals,
                "average_rating": avg_rating,
                "total_matches": total_matches,
            },
            "position_chart": pos_summary,
            "rating_distribution": rating_bins,
            "match_trends": match_trends,
            "league_comparison": league_comp,
            "top_performers": top_performers,
        }

    def filter_players(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filters, sorts, and paginates players according to sanitized query parameters."""
        df = self.data_manager.get_players_df()
        if df.empty:
            return {
                "players": [],
                "total_count": 0,
                "page": 1,
                "page_size": params.get("page_size", 15),
                "total_pages": 0,
            }

        # Search by player_name (case-insensitive partial match)
        search = params.get("search", "").lower()
        if search:
            df = df[df["player_name"].str.lower().str.contains(search, na=False)]

        # Categorical filters
        for field in ["league", "club", "position", "season"]:
            val = params.get(field)
            if val:
                df = df[df[field] == val]

        # Numeric filters
        if params.get("min_age") is not None:
            df = df[df["age"] >= params["min_age"]]
        if params.get("max_age") is not None:
            df = df[df["age"] <= params["max_age"]]
        if params.get("min_minutes") is not None:
            df = df[df["minutes_played"] >= params["min_minutes"]]
        if params.get("min_appearances") is not None:
            df = df[df["appearances"] >= params["min_appearances"]]
        if params.get("min_rating") is not None:
            df = df[df["rating"] >= params["min_rating"]]
        if params.get("max_rating") is not None:
            df = df[df["rating"] <= params["max_rating"]]

        total_count = len(df)

        # Sorting
        sort_by = params.get("sort_by", "goals")
        ascending = params.get("sort_order", "desc") == "asc"
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=ascending, na_position="last")

        # Pagination
        page = max(1, params.get("page", 1))
        page_size = max(1, params.get("page_size", 15))
        total_pages = int(np.ceil(total_count / page_size)) if total_count > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = df.iloc[start_idx:end_idx]

        records = paginated_df.to_dict(orient="records")
        # Ensure clean JSON serializability
        clean_records = []
        for r in records:
            clean_item = {}
            for k, v in r.items():
                if pd.isna(v):
                    clean_item[k] = None
                elif isinstance(v, (np.integer, int)):
                    clean_item[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    clean_item[k] = round(float(v), 2)
                else:
                    clean_item[k] = v
            clean_records.append(clean_item)

        return {
            "players": clean_records,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_available_filters(self) -> Dict[str, Any]:
        """Returns distinct filter values available in the active dataset."""
        df = self.data_manager.get_players_df()
        if df.empty:
            return {"seasons": [], "leagues": [], "clubs": [], "positions": [], "age_range": [18, 38]}

        return {
            "seasons": sorted(list(df["season"].dropna().unique())),
            "leagues": sorted(list(df["league"].dropna().unique())),
            "clubs": sorted(list(df["club"].dropna().unique())),
            "positions": ["Goalkeeper", "Defender", "Midfielder", "Forward"],
            "age_range": [int(df["age"].min()), int(df["age"].max())],
            "rating_range": [float(df["rating"].min()), float(df["rating"].max())],
        }

    def get_position_analytics(self) -> List[Dict[str, Any]]:
        """Calculates deep position-level comparison statistics."""
        df = self.data_manager.get_players_df()
        if df.empty:
            return []

        grouped = df.groupby("position").agg(
            player_count=("player_id", "count"),
            total_goals=("goals", "sum"),
            total_assists=("assists", "sum"),
            avg_goals_per_90=("goals_per_90", "mean"),
            avg_assists_per_90=("assists_per_90", "mean"),
            avg_rating=("rating", "mean"),
            avg_minutes=("minutes_played", "mean"),
            avg_pass_comp=("pass_completion_pct", "mean"),
        ).reset_index()

        results = []
        for _, r in grouped.iterrows():
            results.append({
                "position": r["position"],
                "player_count": int(r["player_count"]),
                "total_goals": int(r["total_goals"]),
                "total_assists": int(r["total_assists"]),
                "avg_goals_per_90": round(float(r["avg_goals_per_90"]), 2) if not pd.isna(r["avg_goals_per_90"]) else 0.0,
                "avg_assists_per_90": round(float(r["avg_assists_per_90"]), 2) if not pd.isna(r["avg_assists_per_90"]) else 0.0,
                "avg_rating": round(float(r["avg_rating"]), 2),
                "avg_minutes": round(float(r["avg_minutes"]), 1),
                "avg_pass_comp": round(float(r["avg_pass_comp"]), 1) if not pd.isna(r["avg_pass_comp"]) else 0.0,
            })
        return results

    def get_club_analytics(self) -> List[Dict[str, Any]]:
        """Calculates club-level aggregates and efficiency scores."""
        df = self.data_manager.get_players_df()
        if df.empty:
            return []

        grouped = df.groupby(["club", "league"]).agg(
            player_count=("player_id", "count"),
            total_goals=("goals", "sum"),
            total_assists=("assists", "sum"),
            total_shots=("shots", "sum"),
            total_xg=("xg", "sum"),
            avg_rating=("rating", "mean"),
        ).reset_index().sort_values("total_goals", ascending=False)

        results = []
        for _, r in grouped.iterrows():
            results.append({
                "club": r["club"],
                "league": r["league"],
                "player_count": int(r["player_count"]),
                "total_goals": int(r["total_goals"]),
                "total_assists": int(r["total_assists"]),
                "total_shots": int(r["total_shots"]),
                "total_xg": round(float(r["total_xg"]), 2),
                "avg_rating": round(float(r["avg_rating"]), 2),
            })
        return results

    def get_league_analytics(self) -> List[Dict[str, Any]]:
        """Calculates league-level performance comparisons."""
        players_df = self.data_manager.get_players_df()
        matches_df = self.data_manager.get_matches_df()
        if players_df.empty:
            return []

        results = []
        for league in players_df["league"].unique():
            l_players = players_df[players_df["league"] == league]
            l_matches = matches_df[matches_df["league"] == league] if not matches_df.empty else pd.DataFrame()

            results.append({
                "league": league,
                "club_count": int(l_players["club"].nunique()),
                "player_count": len(l_players),
                "total_goals": int(l_players["goals"].sum()),
                "avg_rating": round(float(l_players["rating"].mean()), 2),
                "total_matches": len(l_matches),
                "match_goals_avg": round(float(l_matches["total_goals"].mean()), 2) if not l_matches.empty else 0.0,
            })
        return results

    def get_age_performance_data(self, y_metric: str = "rating") -> List[Dict[str, Any]]:
        """Produces scatter dataset for Age versus selected Performance metric."""
        df = self.data_manager.get_players_df()
        if df.empty or y_metric not in df.columns:
            return []

        clean_df = df.dropna(subset=["age", y_metric])
        results = []
        for _, r in clean_df.iterrows():
            results.append({
                "player_id": int(r["player_id"]),
                "player_name": r["player_name"],
                "position": r["position"],
                "club": r["club"],
                "age": int(r["age"]),
                "y_value": round(float(r[y_metric]), 2),
            })
        return results

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Calculates Pearson correlation matrix across numeric variables."""
        df = self.data_manager.get_players_df()
        if df.empty:
            return {"columns": [], "matrix": []}

        cols = ["age", "minutes_played", "goals", "assists", "xg", "xa", "key_passes", "rating"]
        valid_cols = [c for c in cols if c in df.columns]

        sub_df = df[valid_cols].dropna()
        if len(sub_df) < 3:
            return {"columns": [], "matrix": []}

        corr = sub_df.corr().round(2)
        labels = {
            "age": "Age",
            "minutes_played": "Minutes",
            "goals": "Goals",
            "assists": "Assists",
            "xg": "xG",
            "xa": "xA",
            "key_passes": "Key Passes",
            "rating": "Rating",
        }
        display_cols = [labels.get(c, c) for c in corr.columns]

        return {
            "columns": display_cols,
            "matrix": corr.values.tolist(),
        }

    def get_match_analytics(self, season: Optional[str] = None, league: Optional[str] = None) -> Dict[str, Any]:
        """Produces match trends, result breakdown, and fixture records."""
        df = self.data_manager.get_matches_df()
        if df.empty:
            return {
                "total_matches": 0,
                "total_goals": 0,
                "avg_goals": 0.0,
                "home_wins": 0,
                "away_wins": 0,
                "draws": 0,
                "matches": [],
            }

        if season and "season" in df.columns:
            df = df[df["season"] == season]
        if league and "league" in df.columns:
            df = df[df["league"] == league]

        total_matches = len(df)
        total_goals = int(df["total_goals"].sum())
        avg_goals = round(float(total_goals / max(total_matches, 1)), 2)

        home_wins = int((df["result"] == "Home Win").sum())
        away_wins = int((df["result"] == "Away Win").sum())
        draws = int((df["result"] == "Draw").sum())

        highest_match = {}
        if not df.empty:
            h_row = df.sort_values("total_goals", ascending=False).iloc[0]
            highest_match = {
                "match": f"{h_row['home_team']} {h_row['home_goals']} - {h_row['away_goals']} {h_row['away_team']}",
                "total_goals": int(h_row["total_goals"]),
                "date": h_row["date_str"],
            }

        # Clean fixtures list
        matches_list = df.sort_values("match_date", ascending=False).head(50).to_dict(orient="records")

        return {
            "total_matches": total_matches,
            "total_goals": total_goals,
            "avg_goals": avg_goals,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "draws": draws,
            "highest_match": highest_match,
            "matches": matches_list,
        }
