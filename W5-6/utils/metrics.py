"""Reusable football metrics and numerical calculation formulas using Python and NumPy.
"""

from typing import Optional, Union, Dict, Any
import numpy as np


def goals_per_90(goals: Union[int, float], minutes_played: Union[int, float]) -> Optional[float]:
    """Calculates goals scored per 90 minutes with zero-minute guard."""
    if minutes_played is None or minutes_played <= 0 or goals is None:
        return None
    return round(float((goals / minutes_played) * 90.0), 2)


def assists_per_90(assists: Union[int, float], minutes_played: Union[int, float]) -> Optional[float]:
    """Calculates assists made per 90 minutes with zero-minute guard."""
    if minutes_played is None or minutes_played <= 0 or assists is None:
        return None
    return round(float((assists / minutes_played) * 90.0), 2)


def goal_contributions(goals: Union[int, float], assists: Union[int, float]) -> int:
    """Calculates total goal contributions (goals + assists)."""
    g = 0 if goals is None else int(goals)
    a = 0 if assists is None else int(assists)
    return g + a


def goal_contributions_per_90(
    goals: Union[int, float], assists: Union[int, float], minutes_played: Union[int, float]
) -> Optional[float]:
    """Calculates goal contributions (G+A) per 90 minutes."""
    if minutes_played is None or minutes_played <= 0:
        return None
    g = 0 if goals is None else float(goals)
    a = 0 if assists is None else float(assists)
    return round(float(((g + a) / minutes_played) * 90.0), 2)


def pass_completion_pct(completed: Union[int, float], attempted: Union[int, float]) -> Optional[float]:
    """Calculates pass completion percentage with zero-attempt guard."""
    if attempted is None or attempted <= 0 or completed is None:
        return None
    pct = (completed / attempted) * 100.0
    return round(float(min(pct, 100.0)), 1)


def shot_accuracy_pct(shots_on_target: Union[int, float], shots: Union[int, float]) -> Optional[float]:
    """Calculates shot accuracy percentage with zero-shot guard."""
    if shots is None or shots <= 0 or shots_on_target is None:
        return None
    pct = (shots_on_target / shots) * 100.0
    return round(float(min(pct, 100.0)), 1)


def xg_difference(goals: Union[int, float], xg: Union[int, float]) -> Optional[float]:
    """Calculates xG difference (goals - xG). Descriptive metric."""
    if goals is None or xg is None:
        return None
    return round(float(goals - xg), 2)


def xa_difference(assists: Union[int, float], xa: Union[int, float]) -> Optional[float]:
    """Calculates xA difference (assists - xA). Descriptive metric."""
    if assists is None or xa is None:
        return None
    return round(float(assists - xa), 2)


def defensive_actions(tackles: Union[int, float], interceptions: Union[int, float]) -> int:
    """Calculates total defensive actions (tackles + interceptions)."""
    t = 0 if tackles is None else int(tackles)
    i = 0 if interceptions is None else int(interceptions)
    return t + i


def defensive_actions_per_90(
    tackles: Union[int, float], interceptions: Union[int, float], minutes_played: Union[int, float]
) -> Optional[float]:
    """Calculates tackles + interceptions per 90 minutes."""
    if minutes_played is None or minutes_played <= 0:
        return None
    t = 0 if tackles is None else float(tackles)
    i = 0 if interceptions is None else float(interceptions)
    return round(float(((t + i) / minutes_played) * 90.0), 2)


def goals_per_appearance(goals: Union[int, float], appearances: Union[int, float]) -> Optional[float]:
    """Calculates average goals per appearance."""
    if appearances is None or appearances <= 0 or goals is None:
        return None
    return round(float(goals / appearances), 2)


def assists_per_appearance(assists: Union[int, float], appearances: Union[int, float]) -> Optional[float]:
    """Calculates average assists per appearance."""
    if appearances is None or appearances <= 0 or assists is None:
        return None
    return round(float(assists / appearances), 2)


def minutes_per_appearance(minutes_played: Union[int, float], appearances: Union[int, float]) -> Optional[float]:
    """Calculates average minutes per appearance."""
    if appearances is None or appearances <= 0 or minutes_played is None:
        return None
    return round(float(minutes_played / appearances), 1)


def determine_match_result(home_goals: int, away_goals: int) -> str:
    """Determines standard football match result."""
    if home_goals > away_goals:
        return "Home Win"
    elif away_goals > home_goals:
        return "Away Win"
    return "Draw"


# --------------------------------------------------------------------------
# NumPy Vectorized Calculations
# --------------------------------------------------------------------------

def vectorized_per_90(metric_array: np.ndarray, minutes_array: np.ndarray) -> np.ndarray:
    """Vectorized calculation of per-90 metrics across NumPy arrays."""
    metric_arr = np.asarray(metric_array, dtype=float)
    minutes_arr = np.asarray(minutes_array, dtype=float)
    valid_mask = minutes_arr > 0
    result = np.zeros_like(metric_arr)
    np.divide(metric_arr * 90.0, minutes_arr, out=result, where=valid_mask)
    return np.round(result, 2)


def vectorized_min_max_scale(
    values: np.ndarray, min_val: Optional[float] = None, max_val: Optional[float] = None
) -> np.ndarray:
    """Normalizes an array of values into [0.0, 1.0] scale using NumPy.
    Safely handles uniform arrays and identical min/max values.
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return np.array([], dtype=float)

    actual_min = float(np.nanmin(arr)) if min_val is None else float(min_val)
    actual_max = float(np.nanmax(arr)) if max_val is None else float(max_val)

    span = actual_max - actual_min
    if span <= 1e-9:
        # Uniform values map to neutral 0.5
        return np.full_like(arr, 0.5, dtype=float)

    normalized = (arr - actual_min) / span
    return np.clip(np.round(normalized, 3), 0.0, 1.0)
