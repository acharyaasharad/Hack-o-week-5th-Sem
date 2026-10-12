"""DataManager service for Touchline Analytics.
Handles CSV ingestion, data cleansing, integrity validation, derived column generation,
and comprehensive data quality auditing.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import logging

from utils.validators import validate_player_columns, validate_match_columns
from utils.metrics import (
    goals_per_90,
    assists_per_90,
    goal_contributions,
    goal_contributions_per_90,
    pass_completion_pct,
    shot_accuracy_pct,
    xg_difference,
    xa_difference,
    defensive_actions,
    defensive_actions_per_90,
    determine_match_result,
)
import config

logger = logging.getLogger(__name__)


class DataManager:
    """Central data manager responsible for football dataset ETL, validation, and in-memory storage."""

    def __init__(self, players_path: Optional[Path] = None, matches_path: Optional[Path] = None):
        self.default_players_path = players_path or config.PLAYERS_CSV
        self.default_matches_path = matches_path or config.MATCHES_CSV

        self.players_df: pd.DataFrame = pd.DataFrame()
        self.matches_df: pd.DataFrame = pd.DataFrame()

        self.raw_players_count: int = 0
        self.raw_matches_count: int = 0
        self.source_name: str = "Demo Dataset · Synthetic sample statistics"
        self.is_custom: bool = False

        self.quality_report: Dict[str, Any] = {}

        # Automatically load default data on creation if available
        if self.default_players_path.exists() and self.default_matches_path.exists():
            self.load_data(self.default_players_path, self.default_matches_path)

    def load_data(
        self,
        players_path: Path,
        matches_path: Optional[Path] = None,
        source_name: Optional[str] = None,
        is_custom: bool = False,
    ) -> None:
        """Loads and cleans player and match datasets from CSV files."""
        if not players_path.exists():
            raise FileNotFoundError(f"Player data file not found: {players_path}")

        # Ingest Players
        raw_players = pd.read_csv(players_path)
        self.raw_players_count = len(raw_players)

        valid_cols, missing_cols = validate_player_columns(list(raw_players.columns))
        if not valid_cols:
            raise ValueError(f"Player CSV missing required columns: {', '.join(missing_cols)}")

        # Ingest Matches if provided
        raw_matches = pd.DataFrame()
        if matches_path and matches_path.exists():
            raw_matches = pd.read_csv(matches_path)
            self.raw_matches_count = len(raw_matches)
            valid_mcols, missing_mcols = validate_match_columns(list(raw_matches.columns))
            if not valid_mcols:
                raise ValueError(f"Match CSV missing required columns: {', '.join(missing_mcols)}")

        # Process and clean
        cleaned_players, player_audit = self._clean_players(raw_players)
        cleaned_matches, match_audit = self._clean_matches(raw_matches)

        self.players_df = cleaned_players
        self.matches_df = cleaned_matches
        self.source_name = source_name or ("User Uploaded Dataset" if is_custom else "Demo Dataset · Synthetic sample statistics")
        self.is_custom = is_custom

        # Compile Quality Report
        self.quality_report = {
            "source_name": self.source_name,
            "is_custom": self.is_custom,
            "players": {
                "raw_rows": self.raw_players_count,
                "valid_rows": len(cleaned_players),
                "dropped_rows": self.raw_players_count - len(cleaned_players),
                "issues": player_audit,
            },
            "matches": {
                "raw_rows": self.raw_matches_count,
                "valid_rows": len(cleaned_matches),
                "dropped_rows": self.raw_matches_count - len(cleaned_matches),
                "issues": match_audit,
            },
            "completeness_score": round(
                (len(cleaned_players) / max(self.raw_players_count, 1)) * 100.0, 1
            ),
        }

        logger.info(
            "DataManager successfully loaded: %d players, %d matches (%s)",
            len(self.players_df),
            len(self.matches_df),
            self.source_name,
        )

    def _clean_players(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Performs rigorous cleaning and derived metric calculation on players DataFrame."""
        audit_issues = []
        cleaned = df.copy()

        # 1. Exact Duplicate rows check
        dup_count = int(cleaned.duplicated().sum())
        if dup_count > 0:
            audit_issues.append({
                "column": "all",
                "issue_type": "Exact Duplicate Rows",
                "count": dup_count,
                "action": "Removed duplicate rows",
            })
            cleaned = cleaned.drop_duplicates()

        # 2. Duplicate player_id check
        dup_id_count = int(cleaned.duplicated(subset=["player_id"]).sum())
        if dup_id_count > 0:
            audit_issues.append({
                "column": "player_id",
                "issue_type": "Duplicate Player IDs",
                "count": dup_id_count,
                "action": "Retained first instance of each player_id",
            })
            cleaned = cleaned.drop_duplicates(subset=["player_id"], keep="first")

        # 3. Numeric Conversions
        numeric_cols = [
            "player_id", "age", "appearances", "minutes_played", "goals", "assists",
            "shots", "shots_on_target", "xg", "xa", "key_passes", "passes_completed",
            "passes_attempted", "tackles", "interceptions", "yellow_cards", "red_cards", "rating"
        ]

        for col in numeric_cols:
            if col in cleaned.columns:
                non_num_count = int(pd.to_numeric(cleaned[col], errors="coerce").isna().sum())
                if non_num_count > 0:
                    audit_issues.append({
                        "column": col,
                        "issue_type": "Invalid or Non-numeric Values",
                        "count": non_num_count,
                        "action": "Coerced to numeric / zero-filled",
                    })
                cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce").fillna(0)

        # 4. Logical Constraints Enforcement
        # shots_on_target <= shots
        sot_invalid = cleaned["shots_on_target"] > cleaned["shots"]
        if sot_invalid.sum() > 0:
            audit_issues.append({
                "column": "shots_on_target",
                "issue_type": "Shots on Target > Total Shots",
                "count": int(sot_invalid.sum()),
                "action": "Capped shots_on_target to shots",
            })
            cleaned.loc[sot_invalid, "shots_on_target"] = cleaned.loc[sot_invalid, "shots"]

        # passes_completed <= passes_attempted
        passes_invalid = cleaned["passes_completed"] > cleaned["passes_attempted"]
        if passes_invalid.sum() > 0:
            audit_issues.append({
                "column": "passes_completed",
                "issue_type": "Passes Completed > Attempted",
                "count": int(passes_invalid.sum()),
                "action": "Capped passes_completed to passes_attempted",
            })
            cleaned.loc[passes_invalid, "passes_completed"] = cleaned.loc[passes_invalid, "passes_attempted"]

        # Rating bounded between 0.0 and 10.0
        cleaned["rating"] = cleaned["rating"].clip(0.0, 10.0)

        # 5. Enrich with Derived Metrics (Vectorized or Row-wise where guarded)
        cleaned["goals_per_90"] = cleaned.apply(
            lambda r: goals_per_90(r["goals"], r["minutes_played"]), axis=1
        )
        cleaned["assists_per_90"] = cleaned.apply(
            lambda r: assists_per_90(r["assists"], r["minutes_played"]), axis=1
        )
        cleaned["goal_contributions"] = cleaned["goals"] + cleaned["assists"]
        cleaned["goal_contributions_per_90"] = cleaned.apply(
            lambda r: goal_contributions_per_90(r["goals"], r["assists"], r["minutes_played"]), axis=1
        )
        cleaned["pass_completion_pct"] = cleaned.apply(
            lambda r: pass_completion_pct(r["passes_completed"], r["passes_attempted"]), axis=1
        )
        cleaned["shot_accuracy_pct"] = cleaned.apply(
            lambda r: shot_accuracy_pct(r["shots_on_target"], r["shots"]), axis=1
        )
        cleaned["xg_difference"] = cleaned["goals"] - cleaned["xg"]
        cleaned["xa_difference"] = cleaned["assists"] - cleaned["xa"]
        cleaned["defensive_actions"] = cleaned["tackles"] + cleaned["interceptions"]
        cleaned["defensive_actions_per_90"] = cleaned.apply(
            lambda r: defensive_actions_per_90(r["tackles"], r["interceptions"], r["minutes_played"]), axis=1
        )

        return cleaned, audit_issues

    def _clean_matches(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Performs validation and cleansing on matches DataFrame."""
        if df.empty:
            return pd.DataFrame(), []

        audit_issues = []
        cleaned = df.copy()

        # Deduplication
        dup_count = int(cleaned.duplicated().sum())
        if dup_count > 0:
            audit_issues.append({
                "column": "all",
                "issue_type": "Exact Duplicate Matches",
                "count": dup_count,
                "action": "Removed duplicates",
            })
            cleaned = cleaned.drop_duplicates()

        # Date parsing
        cleaned["match_date"] = pd.to_datetime(cleaned["match_date"], errors="coerce")
        invalid_dates = cleaned["match_date"].isna().sum()
        if invalid_dates > 0:
            audit_issues.append({
                "column": "match_date",
                "issue_type": "Invalid Date Formats",
                "count": int(invalid_dates),
                "action": "Dropped invalid dates",
            })
            cleaned = cleaned.dropna(subset=["match_date"])

        # Numeric goals
        cleaned["home_goals"] = pd.to_numeric(cleaned["home_goals"], errors="coerce").fillna(0).astype(int).clip(lower=0)
        cleaned["away_goals"] = pd.to_numeric(cleaned["away_goals"], errors="coerce").fillna(0).astype(int).clip(lower=0)

        # Derived match metrics
        cleaned["total_goals"] = cleaned["home_goals"] + cleaned["away_goals"]
        cleaned["result"] = cleaned.apply(
            lambda r: determine_match_result(r["home_goals"], r["away_goals"]), axis=1
        )
        cleaned["date_str"] = cleaned["match_date"].dt.strftime("%Y-%m-%d")

        return cleaned, audit_issues

    def get_players_df(self) -> pd.DataFrame:
        """Returns the in-memory cleaned players DataFrame."""
        return self.players_df.copy()

    def get_matches_df(self) -> pd.DataFrame:
        """Returns the in-memory cleaned matches DataFrame."""
        return self.matches_df.copy()

    @staticmethod
    def clean_record(d: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitizes DataFrame row dictionary converting NaN/inf to None for valid JSON serialization."""
        cleaned = {}
        for k, v in d.items():
            if pd.isna(v) or v is None:
                cleaned[k] = None
            elif isinstance(v, (np.floating, float)):
                if np.isnan(v) or np.isinf(v):
                    cleaned[k] = None
                else:
                    cleaned[k] = round(float(v), 2)
            elif isinstance(v, (np.integer, int)):
                cleaned[k] = int(v)
            else:
                cleaned[k] = v
        return cleaned

    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single player dictionary by player_id."""
        if self.players_df.empty:
            return None
        match = self.players_df[self.players_df["player_id"] == player_id]
        if match.empty:
            return None
        return self.clean_record(match.iloc[0].to_dict())

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Returns structured data-quality summary report."""
        return self.quality_report

    def reset_to_default(self) -> None:
        """Restores the bundled synthetic demo dataset."""
        self.load_data(self.default_players_path, self.default_matches_path, is_custom=False)
