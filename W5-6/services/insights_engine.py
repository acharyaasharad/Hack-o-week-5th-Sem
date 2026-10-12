"""InsightsEngine service for Touchline Analytics.
Generates deterministic, factual insights derived directly from dataset aggregations.
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np
import logging

from services.data_manager import DataManager

logger = logging.getLogger(__name__)


class InsightsEngine:
    """Computes deterministic analytical observations backed by mathematical evidence."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def set_data_manager(self, data_manager: DataManager) -> None:
        """Updates active DataManager."""
        self.data_manager = data_manager

    def generate_insights(self) -> List[Dict[str, Any]]:
        """Calculates 5-6 deterministic observations from current player and match data."""
        players_df = self.data_manager.get_players_df()
        matches_df = self.data_manager.get_matches_df()

        if players_df.empty:
            return []

        insights = []

        # 1. Top Clinical Finisher (Highest xG Overperformance among Forwards)
        forwards = players_df[(players_df["position"] == "Forward") & (players_df["minutes_played"] >= 500)]
        if not forwards.empty:
            top_overperformer = forwards.sort_values("xg_difference", ascending=False).iloc[0]
            insights.append({
                "category": "Finishing Efficiency",
                "tag": "Clinical Outperformance",
                "icon": "zap",
                "title": f"{top_overperformer['player_name']} Leads Finishing Delta",
                "description": (
                    f"{top_overperformer['player_name']} ({top_overperformer['club']}) scored "
                    f"{int(top_overperformer['goals'])} goals from an expected xG of {top_overperformer['xg']:.2f}, "
                    f"yielding a positive delta of +{top_overperformer['xg_difference']:.2f} goals."
                ),
            })

        # 2. Creative Anchor (Most Key Passes & xA)
        creative_midfielders = players_df[(players_df["position"] == "Midfielder") & (players_df["minutes_played"] >= 500)]
        if not creative_midfielders.empty:
            top_creator = creative_midfielders.sort_values("key_passes", ascending=False).iloc[0]
            insights.append({
                "category": "Playmaking",
                "tag": "Chance Creation",
                "icon": "compass",
                "title": f"{top_creator['player_name']} Creates the Most Opportunities",
                "description": (
                    f"{top_creator['player_name']} ({top_creator['club']}) leads all midfielders with "
                    f"{int(top_creator['key_passes'])} key passes and {top_creator['xa']:.2f} xA, "
                    f"averaging {top_creator['assists_per_90']:.2f} assists per 90 minutes."
                ),
            })

        # 3. Defensive Outlier
        defenders = players_df[(players_df["position"] == "Defender") & (players_df["minutes_played"] >= 500)]
        if not defenders.empty:
            top_def = defenders.sort_values("defensive_actions", ascending=False).iloc[0]
            insights.append({
                "category": "Defensive Activity",
                "tag": "Disruption",
                "icon": "shield",
                "title": f"{top_def['player_name']} Ranks Highest in Disruptions",
                "description": (
                    f"{top_def['player_name']} ({top_def['club']}) executed {int(top_def['defensive_actions'])} "
                    f"total defensive actions ({int(top_def['tackles'])} tackles and {int(top_def['interceptions'])} interceptions), "
                    f"logging {top_def['defensive_actions_per_90']:.2f} actions per 90."
                ),
            })

        # 4. League Match Scoring Contrast
        if not matches_df.empty and "league" in matches_df.columns:
            league_stats = matches_df.groupby("league").agg(
                avg_goals=("total_goals", "mean"),
                match_count=("match_id", "count")
            ).reset_index()

            if len(league_stats) >= 2:
                top_league = league_stats.sort_values("avg_goals", ascending=False).iloc[0]
                sec_league = league_stats.sort_values("avg_goals", ascending=False).iloc[1]
                insights.append({
                    "category": "League Trends",
                    "tag": "Goal Rates",
                    "icon": "trending-up",
                    "title": f"{top_league['league']} Outpaces in Match Goals",
                    "description": (
                        f"Matches in the {top_league['league']} average {top_league['avg_goals']:.2f} goals per fixture "
                        f"compared to {sec_league['avg_goals']:.2f} in {sec_league['league']} across "
                        f"{int(top_league['match_count'] + sec_league['match_count'])} analyzed fixtures."
                    ),
                })

        # 5. Top Squad Rating
        club_ratings = players_df.groupby("club").agg(
            avg_rating=("rating", "mean"),
            squad_size=("player_id", "count"),
        ).reset_index()

        if not club_ratings.empty:
            best_club = club_ratings.sort_values("avg_rating", ascending=False).iloc[0]
            insights.append({
                "category": "Squad Performance",
                "tag": "Highest Rated Squad",
                "icon": "award",
                "title": f"{best_club['club']} Leads Collective Ratings",
                "description": (
                    f"{best_club['club']} registers the highest mean player performance rating ({best_club['avg_rating']:.2f}★) "
                    f"across {int(best_club['squad_size'])} tracked squad members in the dataset."
                ),
            })

        return insights
