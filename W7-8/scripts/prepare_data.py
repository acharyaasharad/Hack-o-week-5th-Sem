"""Data preparation script for Energy Demand Forecasting & Optimization.
Generates verified offline sample dataset and processes raw 10-minute readings into clean hourly datasets.
"""

from pathlib import Path
import sys
import logging
import numpy as np
import pandas as pd

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_synthetic_sample_dataset(output_path: Path, days: int = 60) -> pd.DataFrame:
    """Generates a realistic, calibrated synthetic sample dataset mimicking Tetouan power readings.
    
    Contains 10-minute intervals over the specified duration with:
    - Diurnal cyclical patterns (morning ramps, afternoon dips, evening peaks)
    - Weekday vs weekend load variations
    - Weather correlations (temperature-induced cooling demand)
    - Zone 1, Zone 2, Zone 3 power levels
    """
    logger.info(f"Generating calibrated sample dataset ({days} days @ 10-min resolution)...")
    np.random.seed(42)

    # Generate 10-minute timestamp range starting from 2024-01-01 00:00:00
    date_range = pd.date_range(start="2024-01-01 00:00:00", periods=days * 24 * 6, freq="10min")
    n_points = len(date_range)

    hours = date_range.hour.values + date_range.minute.values / 60.0
    day_of_week = date_range.dayofweek.values
    is_weekend = (day_of_week >= 5).astype(float)

    # Ambient Temperature profile (cool at night, peak around 15:00)
    base_temp = 18.0 + 7.0 * np.sin(2 * np.pi * (hours - 9) / 24) + np.random.normal(0, 1.2, n_points)
    # Humidity (inversely correlated with temp)
    humidity = 65.0 - 20.0 * np.sin(2 * np.pi * (hours - 9) / 24) + np.random.normal(0, 3.0, n_points)
    humidity = np.clip(humidity, 20.0, 95.0)
    # Wind speed
    wind_speed = np.abs(np.random.normal(2.5, 1.2, n_points) + 1.0 * np.sin(2 * np.pi * hours / 24))
    
    # Solar flow
    sun_elevation = np.maximum(0, np.sin(np.pi * (hours - 6) / 14))
    gen_diffuse = sun_elevation * (200.0 + np.random.normal(0, 30.0, n_points))
    gen_diffuse = np.clip(gen_diffuse, 0.0, 500.0)
    diffuse = gen_diffuse * 0.45

    # Power consumption baseline models:
    # Zone 1 (Commercial / Dense residential): High evening peak, lower weekend
    diurnal_z1 = 28000 + 9000 * np.sin(2 * np.pi * (hours - 6) / 24) + 6000 * np.sin(4 * np.pi * (hours - 10) / 24)
    weather_effect_z1 = np.maximum(0, base_temp - 22.0) * 800  # cooling load
    weekend_factor_z1 = 1.0 - 0.12 * is_weekend
    noise_z1 = np.random.normal(0, 1200, n_points)
    zone1_power = (diurnal_z1 + weather_effect_z1) * weekend_factor_z1 + noise_z1

    # Zone 2 (Industrial / Mixed): High daytime flat load, significant weekend drop
    diurnal_z2 = 21000 + 7000 * np.sin(2 * np.pi * (hours - 7) / 24)
    weekend_factor_z2 = 1.0 - 0.25 * is_weekend
    noise_z2 = np.random.normal(0, 900, n_points)
    zone2_power = diurnal_z2 * weekend_factor_z2 + noise_z2

    # Zone 3 (Residential): Evening and morning double peaks
    diurnal_z3 = 18000 + 6000 * np.sin(2 * np.pi * (hours - 5) / 24) + 4000 * np.sin(4 * np.pi * (hours - 11) / 24)
    weekend_factor_z3 = 1.0 + 0.05 * is_weekend  # higher residential load on weekends
    noise_z3 = np.random.normal(0, 800, n_points)
    zone3_power = diurnal_z3 * weekend_factor_z3 + noise_z3

    df = pd.DataFrame({
        "DateTime": date_range.strftime("%Y-%m-%d %H:%M:%S"),
        "Temperature": np.round(base_temp, 2),
        "Humidity": np.round(humidity, 2),
        "WindSpeed": np.round(wind_speed, 2),
        "GeneralDiffuseFlows": np.round(gen_diffuse, 2),
        "DiffuseFlows": np.round(diffuse, 2),
        "Zone1Power": np.round(np.clip(zone1_power, 10000, 55000), 1),
        "Zone2Power": np.round(np.clip(zone2_power, 8000, 42000), 1),
        "Zone3Power": np.round(np.clip(zone3_power, 6000, 38000), 1),
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Sample dataset saved to {output_path} ({len(df):,} rows, {output_path.stat().st_size:,} bytes).")
    return df


def resample_to_hourly(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Resamples 10-minute interval dataset to hourly means."""
    logger.info(f"Resampling {input_path} to hourly aggregations...")
    df = pd.read_csv(input_path)
    
    # Identify datetime column
    dt_col = None
    for candidate in ["DateTime", "datetime", "Date", "timestamp"]:
        if candidate in df.columns:
            dt_col = candidate
            break
    if not dt_col:
        dt_col = df.columns[0]

    df[dt_col] = pd.to_datetime(df[dt_col])
    df = df.sort_values(dt_col).set_index(dt_col)
    
    # Resample numeric columns by mean
    numeric_df = df.select_dtypes(include=[np.number])
    hourly_df = numeric_df.resample("1h").mean().interpolate(method="time")
    hourly_df = hourly_df.reset_index()
    hourly_df.rename(columns={dt_col: "DateTime"}, inplace=True)
    hourly_df["DateTime"] = hourly_df["DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    hourly_df.to_csv(output_path, index=False)
    logger.info(f"Hourly dataset saved to {output_path} ({len(hourly_df):,} rows).")
    return hourly_df


def prepare_all_data():
    """Ensures sample and processed datasets exist."""
    # 1. Ensure sample dataset exists
    if not config.SAMPLE_DATASET_PATH.exists():
        generate_synthetic_sample_dataset(config.SAMPLE_DATASET_PATH, days=60)
    else:
        logger.info(f"Sample dataset already present at {config.SAMPLE_DATASET_PATH}")

    # 2. If raw data exists, process it to hourly; otherwise process sample to hourly
    source_for_hourly = config.RAW_DATASET_PATH if config.RAW_DATASET_PATH.exists() else config.SAMPLE_DATASET_PATH
    resample_to_hourly(source_for_hourly, config.PROCESSED_DATASET_PATH)
    logger.info("Data preparation completed successfully.")


if __name__ == "__main__":
    prepare_all_data()
