"""Unit tests for PreprocessingPipeline: validation, hourly resampling, and chronological splitting."""

import pytest
import pandas as pd
import numpy as np
from services.preprocessing import PreprocessingPipeline


@pytest.fixture
def sample_raw_10min_df():
    # 3 days of 10-minute intervals = 432 rows
    dt_range = pd.date_range("2024-01-01 00:00:00", periods=432, freq="10min")
    return pd.DataFrame({
        "DateTime": dt_range.strftime("%Y-%m-%d %H:%M:%S"),
        "Zone1Power": 20000 + 5000 * np.sin(np.linspace(0, 10, 432)),
        "Temperature": 18 + 5 * np.cos(np.linspace(0, 10, 432)),
    })


def test_clean_and_resample_hourly(sample_raw_10min_df):
    pipeline = PreprocessingPipeline(target_column="Zone1Power", timestamp_column="DateTime")
    hourly_df, meta = pipeline.clean_and_resample(sample_raw_10min_df)

    assert "DateTime" in hourly_df.columns
    # 432 10-min records should resample to 72 or 73 hourly records
    assert 70 <= len(hourly_df) <= 73
    assert meta["target"] == "Zone1Power"
    assert "Hourly arithmetic mean" in meta["aggregation_rule"]


def test_chronological_partition_no_leakage(sample_raw_10min_df):
    pipeline = PreprocessingPipeline(target_column="Zone1Power", timestamp_column="DateTime")
    hourly_df, _ = pipeline.clean_and_resample(sample_raw_10min_df)

    train_df, val_df, test_df, split_meta = pipeline.partition_chronological(
        hourly_df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15
    )

    # Verify no overlaps and strict chronological ordering
    assert train_df["DateTime"].max() < val_df["DateTime"].min()
    assert val_df["DateTime"].max() < test_df["DateTime"].min()

    # Verify total sum of partitioned rows
    assert len(train_df) + len(val_df) + len(test_df) == len(hourly_df)


def test_missing_and_duplicate_timestamp_handling():
    dt_range = pd.date_range("2024-01-01 00:00:00", periods=60, freq="1h")
    df = pd.DataFrame({
        "DateTime": list(dt_range) + [dt_range[0]],  # duplicate row
        "Zone1Power": [25000] * 61,
    })
    df.loc[5, "Zone1Power"] = np.nan  # NaN value

    pipeline = PreprocessingPipeline(target_column="Zone1Power")
    cleaned_df, meta = pipeline.clean_and_resample(df)

    assert len(cleaned_df) == 60  # Deduplicated
    assert not cleaned_df["Zone1Power"].isna().any()  # Imputed
