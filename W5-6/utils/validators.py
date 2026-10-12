"""Validation utilities for Touchline Analytics.
Handles input validation, CSV schema integrity, and query sanitization.
"""

from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import re

REQUIRED_PLAYER_COLUMNS = [
    "player_id",
    "player_name",
    "club",
    "league",
    "nationality",
    "position",
    "age",
    "season",
    "appearances",
    "minutes_played",
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "xg",
    "xa",
    "key_passes",
    "passes_completed",
    "passes_attempted",
    "tackles",
    "interceptions",
    "yellow_cards",
    "red_cards",
    "rating",
]

REQUIRED_MATCH_COLUMNS = [
    "match_id",
    "match_date",
    "season",
    "league",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
]

ALLOWED_SORT_COLUMNS = {
    "player_name",
    "club",
    "position",
    "age",
    "appearances",
    "minutes_played",
    "goals",
    "assists",
    "xg",
    "xa",
    "rating",
    "goals_per_90",
    "assists_per_90",
    "pass_completion_pct",
}


def sanitize_filename(filename: str) -> str:
    """Sanitizes user uploaded filenames to prevent directory traversal."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\.-]", "_", Path(filename).name)
    return cleaned if cleaned else "dataset.csv"


def validate_player_columns(columns: List[str]) -> Tuple[bool, List[str]]:
    """Checks whether all required player columns are present."""
    missing = [col for col in REQUIRED_PLAYER_COLUMNS if col not in columns]
    return len(missing) == 0, missing


def validate_match_columns(columns: List[str]) -> Tuple[bool, List[str]]:
    """Checks whether all required match columns are present."""
    missing = [col for col in REQUIRED_MATCH_COLUMNS if col not in columns]
    return len(missing) == 0, missing


def validate_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes and bounds API query parameters for pagination and filtering."""
    sanitized = {}

    # Search query
    search = params.get("search", "")
    sanitized["search"] = str(search).strip()[:100] if search else ""

    # Categorical filters
    sanitized["league"] = str(params.get("league", "")).strip()[:50]
    sanitized["club"] = str(params.get("club", "")).strip()[:50]
    sanitized["position"] = str(params.get("position", "")).strip()[:50]
    sanitized["season"] = str(params.get("season", "")).strip()[:20]

    # Numeric range filters
    def safe_num(val, default=None, min_v=None, max_v=None):
        if val is None or val == "":
            return default
        try:
            num = float(val)
            if min_v is not None:
                num = max(min_v, num)
            if max_v is not None:
                num = min(max_v, num)
            return num
        except (ValueError, TypeError):
            return default

    sanitized["min_age"] = safe_num(params.get("min_age"), None, 15, 50)
    sanitized["max_age"] = safe_num(params.get("max_age"), None, 15, 50)
    sanitized["min_minutes"] = safe_num(params.get("min_minutes"), None, 0, 10000)
    sanitized["min_appearances"] = safe_num(params.get("min_appearances"), None, 0, 100)
    sanitized["min_rating"] = safe_num(params.get("min_rating"), None, 0.0, 10.0)
    sanitized["max_rating"] = safe_num(params.get("max_rating"), None, 0.0, 10.0)

    # Sorting
    sort_by = params.get("sort_by", "goals")
    sanitized["sort_by"] = sort_by if sort_by in ALLOWED_SORT_COLUMNS else "goals"

    sort_order = str(params.get("sort_order", "desc")).lower()
    sanitized["sort_order"] = "asc" if sort_order == "asc" else "desc"

    # Pagination
    try:
        page = int(params.get("page", 1))
        sanitized["page"] = max(1, page)
    except (ValueError, TypeError):
        sanitized["page"] = 1

    try:
        page_size = int(params.get("page_size", 15))
        sanitized["page_size"] = max(1, min(page_size, 100))
    except (ValueError, TypeError):
        sanitized["page_size"] = 15

    return sanitized
