"""Feature engineering for time-series energy forecasting.
Builds calendar variables, cyclical encodings, lag features, and rolling statistics
strictly without future-data leakage.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd

import config


class FeatureEngineering:
    """Builds time-series features strictly avoiding forward-looking data leakage."""

    def __init__(
        self,
        target_column: str = config.DEFAULT_TARGET_COLUMN,
        lags: Optional[List[int]] = None,
        rolling_windows: Optional[List[int]] = None,
        include_weather: bool = True,
    ):
        self.target_column = target_column
        self.lags = lags if lags is not None else config.DEFAULT_LAGS
        self.rolling_windows = rolling_windows if rolling_windows is not None else config.DEFAULT_ROLLING_WINDOWS
        self.include_weather = include_weather
        self.feature_names: List[str] = []

    def create_features(
        self,
        df: pd.DataFrame,
        drop_na_rows: bool = True,
    ) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Transforms a DataFrame containing 'DateTime' and the target into an ML-ready feature matrix X and target y."""
        work_df = df.copy()

        if "DateTime" not in work_df.columns:
            raise ValueError("DataFrame must contain a 'DateTime' column.")

        if self.target_column not in work_df.columns:
            raise ValueError(f"Target column '{self.target_column}' missing from DataFrame.")

        dt = pd.to_datetime(work_df["DateTime"])

        # 1. Calendar Features
        work_df["hour"] = dt.dt.hour
        work_df["dayofweek"] = dt.dt.dayofweek
        work_df["month"] = dt.dt.month
        work_df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(float)

        # 2. Cyclical Sine/Cosine Encodings (smooth circular boundary: 23:00 -> 00:00)
        work_df["hour_sin"] = np.sin(2 * np.pi * work_df["hour"] / 24.0)
        work_df["hour_cos"] = np.cos(2 * np.pi * work_df["hour"] / 24.0)
        work_df["day_sin"] = np.sin(2 * np.pi * work_df["dayofweek"] / 7.0)
        work_df["day_cos"] = np.cos(2 * np.pi * work_df["dayofweek"] / 7.0)
        work_df["month_sin"] = np.sin(2 * np.pi * (work_df["month"] - 1) / 12.0)
        work_df["month_cos"] = np.cos(2 * np.pi * (work_df["month"] - 1) / 12.0)

        # Base calendar feature names
        features = [
            "hour",
            "dayofweek",
            "is_weekend",
            "hour_sin",
            "hour_cos",
            "day_sin",
            "day_cos",
            "month_sin",
            "month_cos",
        ]

        # 3. Weather Features (if present and configured)
        if self.include_weather:
            for wcol in config.DEFAULT_WEATHER_COLUMNS:
                if wcol in work_df.columns and pd.api.types.is_numeric_dtype(work_df[wcol]):
                    features.append(wcol)

        # 4. Lag Features (strictly from past time steps)
        # Check available history length before adding lags (max lag capped at 40% of rows)
        n_rows = len(work_df)
        max_allowable_lag = max(1, int(n_rows * 0.40))
        applicable_lags = [lag for lag in self.lags if lag <= max_allowable_lag]
        if not applicable_lags and n_rows > 1:
            applicable_lags = [1]

        for lag in applicable_lags:
            lag_name = f"{self.target_column}_lag_{lag}"
            work_df[lag_name] = work_df[self.target_column].shift(lag)
            features.append(lag_name)

        # 5. Rolling Statistics (shifted by 1 to prevent leak of current row t)
        shifted_target = work_df[self.target_column].shift(1)
        for w in self.rolling_windows:
            if w < n_rows:
                roll_mean_name = f"{self.target_column}_roll_mean_{w}"
                roll_std_name = f"{self.target_column}_roll_std_{w}"
                work_df[roll_mean_name] = shifted_target.rolling(window=w, min_periods=1).mean()
                work_df[roll_std_name] = shifted_target.rolling(window=w, min_periods=1).std().fillna(0)
                features.extend([roll_mean_name, roll_std_name])

        self.feature_names = features

        if drop_na_rows:
            # Drop rows with NaNs in feature columns or target (usually the initial lag warm-up period)
            work_df = work_df.dropna(subset=features + [self.target_column])

        X = work_df[features].copy()
        y = work_df[self.target_column].copy()

        return X, y, features

    def create_single_step_features(
        self,
        historical_series: pd.Series,
        target_timestamp: pd.Timestamp,
        weather_dict: Optional[Dict[str, float]] = None,
    ) -> pd.DataFrame:
        """Constructs a 1-row feature vector for forecasting a single future timestamp.
        
        Args:
            historical_series: Series of known and recursively forecasted target values up to t-1.
            target_timestamp: Timestamp for which the prediction is being generated (t).
            weather_dict: Optional dictionary of predicted or observed weather at t.
        """
        dt = target_timestamp
        hour = dt.hour
        dayofweek = dt.dayofweek
        month = dt.month

        row = {
            "hour": hour,
            "dayofweek": dayofweek,
            "is_weekend": float(dayofweek >= 5),
            "hour_sin": np.sin(2 * np.pi * hour / 24.0),
            "hour_cos": np.cos(2 * np.pi * hour / 24.0),
            "day_sin": np.sin(2 * np.pi * dayofweek / 7.0),
            "day_cos": np.cos(2 * np.pi * dayofweek / 7.0),
            "month_sin": np.sin(2 * np.pi * (month - 1) / 12.0),
            "month_cos": np.cos(2 * np.pi * (month - 1) / 12.0),
        }

        # Weather values
        if self.include_weather and weather_dict:
            for wcol in config.DEFAULT_WEATHER_COLUMNS:
                if wcol in self.feature_names:
                    row[wcol] = weather_dict.get(wcol, 20.0)

        # Lags from historical_series (index -1 is t-1, -2 is t-2, -24 is t-24, etc.)
        n_hist = len(historical_series)
        for lag in self.lags:
            lag_name = f"{self.target_column}_lag_{lag}"
            if lag_name in self.feature_names:
                if n_hist >= lag:
                    row[lag_name] = float(historical_series.iloc[-lag])
                else:
                    # Fallback to earliest available historical value
                    row[lag_name] = float(historical_series.iloc[0])

        # Rolling statistics
        for w in self.rolling_windows:
            mean_name = f"{self.target_column}_roll_mean_{w}"
            std_name = f"{self.target_column}_roll_std_{w}"
            if mean_name in self.feature_names:
                sub_series = historical_series.iloc[-w:] if n_hist >= w else historical_series
                row[mean_name] = float(sub_series.mean())
            if std_name in self.feature_names:
                sub_series = historical_series.iloc[-w:] if n_hist >= w else historical_series
                row[std_name] = float(sub_series.std()) if len(sub_series) > 1 else 0.0

        # Create DataFrame aligned exactly with self.feature_names
        feat_df = pd.DataFrame([row])
        # Ensure all required features are present
        for f in self.feature_names:
            if f not in feat_df.columns:
                feat_df[f] = 0.0

        return feat_df[self.feature_names]
