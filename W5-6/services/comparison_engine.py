"""ComparisonEngine service for Touchline Analytics.
Handles multi-player comparisons (2-4 players), per-90 metrics, normalized radar metrics,
statistical leader calculations, and factual comparison verdicts.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

from services.data_manager import DataManager
from utils.metrics import (
    goals_per_90,
    assists_per_90,
    goal_contributions,
    pass_completion_pct,
    shot_accuracy_pct,
    defensive_actions_per_90,
    vectorized_min_max_scale,
)

logger = logging.getLogger(__name__)

# Consistent distinct player colors for comparison charts (NO PURPLE)
PLAYER_COLORS = [
    {"primary": "#10b981", "subtle": "rgba(16, 185, 129, 0.25)", "border": "#10b981"},  # Emerald
    {"primary": "#06b6d4", "subtle": "rgba(6, 182, 212, 0.25)", "border": "#06b6d4"},    # Cyan
    {"primary": "#f59e0b", "subtle": "rgba(245, 158, 11, 0.25)", "border": "#f59e0b"},   # Amber
    {"primary": "#f43f5e", "subtle": "rgba(244, 63, 94, 0.25)", "border": "#f43f5e"},    # Rose
]

RADAR_METRIC_KEYS = [
    ("goals_per_90", "Goals / 90"),
    ("assists_per_90", "Assists / 90"),
    ("xg_per_90", "xG / 90"),
    ("xa_per_90", "xA / 90"),
    ("key_passes_per_90", "Key Passes / 90"),
    ("defensive_actions_per_90", "Def Actions / 90"),
    ("pass_completion_pct", "Pass %"),
]


class ComparisonEngine:
    """Engine responsible for multi-player statistical head-to-heads and radar scaling."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def set_data_manager(self, data_manager: DataManager) -> None:
        """Updates active DataManager."""
        self.data_manager = data_manager

    def compare_players(self, player_ids: List[int]) -> Dict[str, Any]:
        """Compares between 2 and 4 unique players with normalized radar vectors and verdicts."""
        # Validate player_ids
        unique_ids = list(dict.fromkeys(player_ids))
        if len(unique_ids) < 2:
            return {
                "success": False,
                "message": "At least two distinct players must be selected for comparison.",
                "data": None,
            }

        if len(unique_ids) > 4:
            unique_ids = unique_ids[:4]

        players_df = self.data_manager.get_players_df()
        if players_df.empty:
            return {"success": False, "message": "No player dataset currently loaded.", "data": None}

        selected_df = players_df[players_df["player_id"].isin(unique_ids)].copy()
        if len(selected_df) < len(unique_ids):
            missing_ids = set(unique_ids) - set(selected_df["player_id"].tolist())
            return {
                "success": False,
                "message": f"Could not find players with IDs: {list(missing_ids)}",
                "data": None,
            }

        # Maintain exact selection order
        selected_df["order"] = selected_df["player_id"].map(lambda pid: unique_ids.index(pid))
        selected_df = selected_df.sort_values("order").drop(columns=["order"])

        # Compute additional per-90 metrics if needed
        selected_df["xg_per_90"] = selected_df.apply(
            lambda r: round((r["xg"] / r["minutes_played"] * 90.0), 2) if r["minutes_played"] > 0 else 0.0, axis=1
        )
        selected_df["xa_per_90"] = selected_df.apply(
            lambda r: round((r["xa"] / r["minutes_played"] * 90.0), 2) if r["minutes_played"] > 0 else 0.0, axis=1
        )
        selected_df["key_passes_per_90"] = selected_df.apply(
            lambda r: round((r["key_passes"] / r["minutes_played"] * 90.0), 2) if r["minutes_played"] > 0 else 0.0, axis=1
        )

        players_list = []
        for idx, (_, r) in enumerate(selected_df.iterrows()):
            color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
            players_list.append({
                "player_id": int(r["player_id"]),
                "player_name": r["player_name"],
                "club": r["club"],
                "league": r["league"],
                "position": r["position"],
                "age": int(r["age"]),
                "appearances": int(r["appearances"]),
                "minutes_played": int(r["minutes_played"]),
                "goals": int(r["goals"]),
                "assists": int(r["assists"]),
                "goal_contributions": int(r["goal_contributions"]),
                "goals_per_90": None if pd.isna(r["goals_per_90"]) else round(float(r["goals_per_90"]), 2),
                "assists_per_90": None if pd.isna(r["assists_per_90"]) else round(float(r["assists_per_90"]), 2),
                "xg": round(float(r["xg"]), 2),
                "xa": round(float(r["xa"]), 2),
                "xg_difference": round(float(r["xg_difference"]), 2),
                "xa_difference": round(float(r["xa_difference"]), 2),
                "pass_completion_pct": None if pd.isna(r["pass_completion_pct"]) else round(float(r["pass_completion_pct"]), 1),
                "shot_accuracy_pct": None if pd.isna(r["shot_accuracy_pct"]) else round(float(r["shot_accuracy_pct"]), 1),
                "defensive_actions": int(r["defensive_actions"]),
                "defensive_actions_per_90": None if pd.isna(r["defensive_actions_per_90"]) else round(float(r["defensive_actions_per_90"]), 2),
                "rating": round(float(r["rating"]), 2),
                "color": color,
            })

        # Calculate population maxes for min-max normalization
        radar_labels = [label for _, label in RADAR_METRIC_KEYS]
        radar_datasets = []

        # Population references from entire players_df for balanced scaling
        pop_maxes = {}
        pop_mins = {}
        for key, _ in RADAR_METRIC_KEYS:
            # Generate column in players_df if needed
            if key not in players_df.columns:
                if key == "xg_per_90":
                    col_vals = (players_df["xg"] / players_df["minutes_played"] * 90.0).replace([np.inf, -np.inf], 0).fillna(0)
                elif key == "xa_per_90":
                    col_vals = (players_df["xa"] / players_df["minutes_played"] * 90.0).replace([np.inf, -np.inf], 0).fillna(0)
                elif key == "key_passes_per_90":
                    col_vals = (players_df["key_passes"] / players_df["minutes_played"] * 90.0).replace([np.inf, -np.inf], 0).fillna(0)
                else:
                    col_vals = players_df[key].fillna(0)
            else:
                col_vals = players_df[key].fillna(0)

            pop_mins[key] = float(np.nanmin(col_vals)) if len(col_vals) > 0 else 0.0
            pop_maxes[key] = float(np.nanmax(col_vals)) if len(col_vals) > 0 else 1.0

        for p in players_list:
            norm_values = []
            raw_values = []
            for key, _ in RADAR_METRIC_KEYS:
                raw_val = p.get(key)
                if raw_val is None:
                    raw_val = 0.0
                raw_values.append(raw_val)

                p_min = pop_mins[key]
                p_max = pop_maxes[key]
                span = p_max - p_min
                if span > 1e-6:
                    scaled = (float(raw_val) - p_min) / span
                else:
                    scaled = 0.5
                # Percentile score 0 to 100 on radar
                norm_values.append(round(float(np.clip(scaled * 100.0, 5.0, 100.0)), 1))

            radar_datasets.append({
                "label": p["player_name"],
                "data": norm_values,
                "raw_values": raw_values,
                "backgroundColor": p["color"]["subtle"],
                "borderColor": p["color"]["primary"],
                "pointBackgroundColor": p["color"]["primary"],
            })

        # Metric-by-metric leaders
        metric_leaders = self._identify_leaders(players_list)

        # Statistical comparison verdict
        verdict = self._generate_verdict(players_list, metric_leaders)

        return {
            "success": True,
            "players": players_list,
            "radar": {
                "labels": radar_labels,
                "datasets": radar_datasets,
            },
            "leaders": metric_leaders,
            "verdict": verdict,
        }

    def _identify_leaders(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identifies top performer for each comparative metric."""
        leaders = {}
        metrics_to_check = [
            ("goals", "Goals"),
            ("assists", "Assists"),
            ("goals_per_90", "Goals / 90"),
            ("rating", "Rating"),
            ("pass_completion_pct", "Pass Completion %"),
            ("defensive_actions_per_90", "Defensive Actions / 90"),
            ("shot_accuracy_pct", "Shot Accuracy %"),
        ]

        for key, label in metrics_to_check:
            best_val = -1.0
            leader_name = "N/A"
            for p in players:
                val = p.get(key)
                if val is not None and not pd.isna(val):
                    try:
                        fval = float(val)
                        if not np.isnan(fval) and fval > best_val:
                            best_val = fval
                            leader_name = p["player_name"]
                    except (ValueError, TypeError):
                        pass

            leaders[key] = {
                "metric": label,
                "leader": leader_name,
                "value": round(best_val, 2) if best_val >= 0 else None,
            }
        return leaders

    def _generate_verdict(self, players: List[Dict[str, Any]], leaders: Dict[str, Any]) -> Dict[str, Any]:
        """Generates deterministic, factual statistical summary without hyperbole."""
        points = []

        # 1. Attacking output leader
        goals_leader = leaders.get("goals", {})
        if goals_leader.get("leader") != "N/A":
            points.append(
                f"{goals_leader['leader']} leads the selection with {int(goals_leader['value'])} goals."
            )

        # 2. Rating leader
        rating_leader = leaders.get("rating", {})
        if rating_leader.get("leader") != "N/A":
            points.append(
                f"{rating_leader['leader']} holds the highest average performance rating ({rating_leader['value']:.2f}★)."
            )

        # 3. Efficiency leader
        pass_leader = leaders.get("pass_completion_pct", {})
        if pass_leader.get("leader") != "N/A":
            points.append(
                f"{pass_leader['leader']} registers the superior pass completion accuracy ({pass_leader['value']:.1f}%)."
            )

        # 4. Contextual warnings
        minutes = [p["minutes_played"] for p in players]
        positions = set(p["position"] for p in players)

        warnings = []
        if max(minutes) - min(minutes) > 600:
            warnings.append(
                "Sample size caution: Significant difference in playing time exists between selected players. Per-90 rates are normalized but smaller samples carry higher variance."
            )

        if len(positions) > 1:
            warnings.append(
                f"Position variance note: Comparing across different tactical roles ({', '.join(positions)}) reflects differing positional responsibilities rather than overall quality."
            )

        return {
            "summary_points": points,
            "warnings": warnings,
            "disclaimer": "These comparisons are derived strictly from available sample data and do not account for unrecorded tactical or physical factors.",
        }
