"""Data preprocessing pipeline for time-series energy forecasting.
Handles chronological validation, hourly resampling, missing-value imputation,
and chronological train/val/test partitioning.
"""

from typing import Tuple, Dict, Any, Optional, List
import logging
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """Prepares and validates time-series data for chronological machine learning."""

    def __init__(self, target_column: str = config.DEFAULT_TARGET_COLUMN, timestamp_column: str = config.DEFAULT_TIMESTAMP_COLUMN):
        self.target_column = target_column
        self.timestamp_column = timestamp_column
        self.aggregation_rule = "Hourly arithmetic mean (mean)"
        self.warnings: List[str] = []

    def clean_and_resample(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        timestamp_col: Optional[str] = None,
        force_hourly: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Cleans, sorts, checks frequency, and resamples sub-hourly readings to hourly."""
        self.warnings = []
        target = target_col or self.target_column
        ts_col = timestamp_col or self.timestamp_column

        if ts_col not in df.columns:
            # Fallback search
            for c in ["DateTime", "datetime", "timestamp", "Date"]:
                if c in df.columns:
                    ts_col = c
                    break
            else:
                raise ValueError(f"Timestamp column '{ts_col}' not found in dataframe.")

        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found in dataframe.")

        work_df = df.copy()

        # 1. Parse timestamps
        work_df[ts_col] = pd.to_datetime(work_df[ts_col], errors="coerce")
        invalid_ts_count = int(work_df[ts_col].isna().sum())
        if invalid_ts_count > 0:
            self.warnings.append(f"Dropped {invalid_ts_count} rows with invalid/unparseable timestamps.")
            work_df = work_df.dropna(subset=[ts_col])

        if len(work_df) < 48:
            self.warnings.append("Dataset has fewer than 48 records. Time-series modeling may have limited accuracy.")

        # 2. Sort chronologically
        work_df = work_df.sort_values(ts_col)

        # 3. Deduplicate timestamps (keep first)
        dup_count = int(work_df[ts_col].duplicated().sum())
        if dup_count > 0:
            self.warnings.append(f"Encountered and deduplicated {dup_count} duplicate timestamps.")
            work_df = work_df.drop_duplicates(subset=[ts_col], keep="first")

        # 4. Set datetime index
        work_df = work_df.set_index(ts_col)

        # 5. Check if numeric target has NaNs
        if work_df[target].isna().sum() > 0:
            nan_cnt = int(work_df[target].isna().sum())
            self.warnings.append(f"Interpolated {nan_cnt} missing values in target '{target}'.")
            work_df[target] = work_df[target].interpolate(method="time").bfill().ffill()

        # 6. Check interval and resample to hourly if sub-hourly
        diffs = work_df.index.to_series().diff().dropna()
        median_sec = diffs.dt.total_seconds().median() if not diffs.empty else 3600

        is_sub_hourly = median_sec < 3000  # Less than 50 minutes (e.g. 10 minutes)
        if force_hourly and is_sub_hourly:
            numeric_cols = work_df.select_dtypes(include=[np.number]).columns
            resampled = work_df[numeric_cols].resample("1h").mean()
            # Linear interpolation for any hourly gap
            resampled = resampled.interpolate(method="time").bfill().ffill()
            work_df = resampled
            self.warnings.append(f"Aggregated sub-hourly data ({int(median_sec/60)} min resolution) to 1-hour means using '{self.aggregation_rule}'.")

        # 7. Check for large gaps in hourly data
        hourly_diffs = work_df.index.to_series().diff().dropna()
        large_gaps = hourly_diffs[hourly_diffs > pd.Timedelta(hours=3)]
        if not large_gaps.empty:
            self.warnings.append(f"Detected {len(large_gaps)} time intervals with gaps greater than 3 hours.")

        # Reset index to have standard 'DateTime' column
        work_df = work_df.reset_index()
        work_df.rename(columns={ts_col: "DateTime"}, inplace=True)
        work_df["DateTime"] = pd.to_datetime(work_df["DateTime"])

        meta = {
            "target": target,
            "row_count": len(work_df),
            "start_time": str(work_df["DateTime"].min()),
            "end_time": str(work_df["DateTime"].max()),
            "warnings": self.warnings,
            "aggregation_rule": self.aggregation_rule if is_sub_hourly else "Native hourly intervals",
        }

        return work_df, meta

    @staticmethod
    def partition_chronological(
        df: pd.DataFrame,
        train_ratio: float = config.TRAIN_RATIO,
        val_ratio: float = config.VAL_RATIO,
        test_ratio: float = config.TEST_RATIO,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Strictly chronological train / validation / test partition.
        
        CRITICAL: Never randomly shuffles time series data to prevent future lookahead leakage!
        """
        n = len(df)
        if n < 50:
            raise ValueError(f"Insufficient data for 3-way chronological split ({n} rows).")

        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        n_test = n - n_train - n_val

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train : n_train + n_val].copy()
        test_df = df.iloc[n_train + n_val :].copy()

        split_meta = {
            "train_size": len(train_df),
            "val_size": len(val_df),
            "test_size": len(test_df),
            "train_start": str(train_df["DateTime"].min()),
            "train_end": str(train_df["DateTime"].max()),
            "val_start": str(val_df["DateTime"].min()),
            "val_end": str(val_df["DateTime"].max()),
            "test_start": str(test_df["DateTime"].min()),
            "test_end": str(test_df["DateTime"].max()),
        }

        return train_df, val_df, test_df, split_meta
