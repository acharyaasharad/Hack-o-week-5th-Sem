"""Display formatters, unit helpers, and presentation helpers for Touchline Analytics.
"""

from typing import Union, Optional, Dict, Any


def format_number(val: Optional[Union[int, float]], decimals: int = 2, default: str = "N/A") -> str:
    """Formats numeric values to fixed decimal precision, gracefully handling None/NaN."""
    if val is None:
        return default
    try:
        f = float(val)
        if f != f:  # NaN check
            return default
        return f"{f:,.{decimals}f}" if decimals > 0 else f"{int(round(f)):,}"
    except (ValueError, TypeError):
        return default


def format_percent(val: Optional[Union[int, float]], default: str = "N/A") -> str:
    """Formats percentage values with a % symbol."""
    if val is None:
        return default
    try:
        f = float(val)
        if f != f:
            return default
        return f"{f:.1f}%"
    except (ValueError, TypeError):
        return default


def format_rating(val: Optional[Union[int, float]], default: str = "—") -> str:
    """Formats match or player rating on 0-10 scale."""
    if val is None:
        return default
    try:
        f = float(val)
        if f != f:
            return default
        return f"{f:.2f}"
    except (ValueError, TypeError):
        return default


def get_player_initials(name: str) -> str:
    """Generates 2-character uppercase avatar initials from player name."""
    if not name:
        return "PL"
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][:2].upper() if len(parts[0]) >= 2 else parts[0].upper()


def get_position_theme(position: str) -> Dict[str, str]:
    """Returns CSS class and accent color for position badges."""
    pos_map = {
        "Goalkeeper": {"class": "pos-gk", "color": "#f59e0b", "abbr": "GK"},
        "Defender": {"class": "pos-df", "color": "#06b6d4", "abbr": "DF"},
        "Midfielder": {"class": "pos-mf", "color": "#10b981", "abbr": "MF"},
        "Forward": {"class": "pos-fw", "color": "#f43f5e", "abbr": "FW"},
    }
    return pos_map.get(position, {"class": "pos-unknown", "color": "#94a3b8", "abbr": "POS"})
