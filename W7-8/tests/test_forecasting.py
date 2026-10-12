"""Unit tests for ForecastingEngine, feature engineering, and recursive prediction."""

import pytest
import pandas as pd
import numpy as np
from services.feature_engineering import FeatureEngineering
from services.forecasting import ForecastingEngine, SeasonalNaiveModel


@pytest.fixture
def hourly_time_series():
    dt_range = pd.date_range("2024-01-01 00:00:00", periods=240, freq="1h")
    hours = dt_range.hour.values
    return pd.DataFrame({
        "DateTime": dt_range,
        "Zone1Power": 25000 + 8000 * np.sin(2 * np.pi * (hours - 6) / 24) + np.random.normal(0, 500, len(dt_range)),
        "Temperature": 18 + 7 * np.cos(2 * np.pi * hours / 24),
    })


def test_feature_engineering_lags_and_rolling(hourly_time_series):
    fe = FeatureEngineering(target_column="Zone1Power", lags=[1, 2, 24], rolling_windows=[6, 24])
    X, y, features = fe.create_features(hourly_time_series, drop_na_rows=True)

    assert "Zone1Power_lag_1" in features
    assert "Zone1Power_lag_24" in features
    assert "Zone1Power_roll_mean_6" in features
    assert "hour_sin" in features
    assert len(X) == len(y)
    assert not X.isna().any().any()


def test_seasonal_naive_baseline(hourly_time_series):
    model = SeasonalNaiveModel(lag_hours=24)
    fe = FeatureEngineering(target_column="Zone1Power", lags=[1, 2, 24])
    X, y, _ = fe.create_features(hourly_time_series)
    model.fit(X, y)

    preds = model.predict(X)
    assert len(preds) == len(X)
    assert not np.isnan(preds).any()


def test_forecasting_engine_train_and_compare(hourly_time_series):
    engine = ForecastingEngine(target_column="Zone1Power")
    res = engine.train_and_compare(hourly_time_series, model_keys=["seasonal_naive", "ridge"])

    assert res["success"] is True
    assert "seasonal_naive" in res["arena_results"]
    assert "ridge" in res["arena_results"]
    assert res["test_metrics"]["mae"] > 0
    assert res["best_model"] in ["seasonal_naive", "ridge"]


def test_recursive_forecast_24h(hourly_time_series):
    engine = ForecastingEngine(target_column="Zone1Power")
    engine.train_and_compare(hourly_time_series, model_keys=["seasonal_naive", "ridge"])

    fc = engine.generate_recursive_forecast(hourly_time_series, horizon=24)
    assert fc["success"] is True
    assert len(fc["forecast_series"]) == 24
    assert fc["peak_demand"] > 0
    # Verify chronological continuity of steps
    for idx, pt in enumerate(fc["forecast_series"]):
        assert pt["step"] == idx + 1
