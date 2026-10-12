"""Machine learning and time-series forecasting engine.
Implements Seasonal Naive, Ridge Regression, Random Forest, and HistGradientBoosting
with chronological evaluation and recursive 24-hour future generation.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import time
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

import config
from services.preprocessing import PreprocessingPipeline
from services.feature_engineering import FeatureEngineering
from services.evaluation import ModelEvaluator

logger = logging.getLogger(__name__)


class SeasonalNaiveModel:
    """Baseline model predicting tomorrow's same-hour load based on 24 hours prior."""

    def __init__(self, lag_hours: int = 24):
        self.lag_hours = lag_hours
        self.last_history_: Optional[np.ndarray] = None
        self.feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.feature_names_ = list(X.columns)
        self.last_history_ = y.values[-168:] if len(y) >= 168 else y.values
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        # Check if 24-hour lag feature exists in X
        lag_col = None
        for col in X.columns:
            if "lag_24" in col:
                lag_col = col
                break

        if lag_col is not None and lag_col in X.columns:
            preds = X[lag_col].values.copy()
            # Fallback if any NaNs exist
            if np.isnan(preds).any():
                fill_val = np.nanmean(preds) if not np.isnan(preds).all() else 25000.0
                preds = np.nan_to_num(preds, nan=fill_val)
            return preds

        # Fallback to mean of training history
        fill_val = float(np.mean(self.last_history_)) if self.last_history_ is not None else 25000.0
        return np.full(shape=(len(X),), fill_value=fill_val)


class ForecastingEngine:
    """Orchestrates model training, evaluation, comparison arena, and recursive forecasting."""

    def __init__(self, target_column: str = config.DEFAULT_TARGET_COLUMN):
        self.target_column = target_column
        self.models: Dict[str, Any] = {}
        self.model_results: Dict[str, Any] = {}
        self.best_model_key: Optional[str] = None
        self.feature_engineer: Optional[FeatureEngineering] = None
        self.last_train_meta: Dict[str, Any] = {}

    def _build_model_instance(self, model_key: str):
        """Instantiates supported model pipelines."""
        if model_key == "seasonal_naive":
            return SeasonalNaiveModel(lag_hours=24)
        elif model_key == "ridge":
            return Pipeline([
                ("scaler", StandardScaler()),
                ("regressor", Ridge(alpha=10.0, random_state=42)),
            ])
        elif model_key == "random_forest":
            return RandomForestRegressor(
                n_estimators=80,
                max_depth=12,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1,
            )
        elif model_key == "hist_gradient_boosting":
            return HistGradientBoostingRegressor(
                max_iter=100,
                learning_rate=0.08,
                max_depth=8,
                random_state=42,
            )
        else:
            raise ValueError(f"Unsupported model key '{model_key}'.")

    def train_and_compare(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        model_keys: Optional[List[str]] = None,
        include_weather: bool = True,
    ) -> Dict[str, Any]:
        """Runs chronological training and evaluation across specified models."""
        target = target_col or self.target_column
        self.target_column = target

        selected_keys = model_keys if model_keys else list(config.SUPPORTED_MODELS.keys())
        # Ensure Seasonal Naive is included for honest baseline comparison
        if "seasonal_naive" not in selected_keys:
            selected_keys = ["seasonal_naive"] + selected_keys

        # 1. Clean and hourly resample
        preprocessor = PreprocessingPipeline(target_column=target)
        hourly_df, clean_meta = preprocessor.clean_and_resample(df, target_col=target)

        # 2. Chronological partition: 70% Train, 15% Validation, 15% Test
        train_df, val_df, test_df, split_meta = preprocessor.partition_chronological(hourly_df)

        # 3. Feature engineering
        fe = FeatureEngineering(target_column=target, include_weather=include_weather)
        self.feature_engineer = fe

        # Build features across full series to preserve chronological lag continuity
        X_full, y_full, feature_names = fe.create_features(hourly_df, drop_na_rows=False)
        # Impute warm-up lag NaNs so initial train samples are not dropped
        X_full = X_full.bfill().ffill()

        X_train, y_train = X_full.loc[train_df.index], y_full.loc[train_df.index]
        X_val, y_val = X_full.loc[val_df.index], y_full.loc[val_df.index]
        X_test, y_test = X_full.loc[test_df.index], y_full.loc[test_df.index]

        val_timestamps = hourly_df.loc[val_df.index, "DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        test_timestamps = hourly_df.loc[test_df.index, "DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()

        arena_results = {}
        best_val_mae = float("inf")
        best_key = "seasonal_naive"

        for key in selected_keys:
            model = self._build_model_instance(key)
            start_t = time.perf_counter()
            model.fit(X_train, y_train)
            train_duration = round(time.perf_counter() - start_t, 3)

            # Validation prediction
            val_preds = model.predict(X_val)
            val_metrics = ModelEvaluator.calculate_metrics(y_val.values, val_preds)

            # Record model
            self.models[key] = model
            arena_results[key] = {
                "model_key": key,
                "display_name": config.SUPPORTED_MODELS.get(key, key),
                "train_duration_sec": train_duration,
                "val_metrics": val_metrics,
                "val_predictions": [round(float(p), 1) for p in val_preds[-48:]],
                "val_actuals": [round(float(a), 1) for a in y_val.values[-48:]],
                "val_timestamps": val_timestamps[-48:],
            }

            # Select best model based on validation MAE (never on test metrics!)
            if val_metrics["mae"] < best_val_mae:
                best_val_mae = val_metrics["mae"]
                best_key = key

        self.best_model_key = best_key

        # Evaluate best model on untouched held-out test set
        best_model = self.models[best_key]
        test_preds = best_model.predict(X_test)
        test_metrics = ModelEvaluator.calculate_metrics(y_test.values, test_preds)

        # Residual diagnostics on validation set for best model
        best_val_preds = best_model.predict(X_val)
        residuals_diag = ModelEvaluator.calculate_residuals(val_timestamps, y_val.values, best_val_preds)

        # Save artifacts to models/ directory
        artifact_path = config.MODELS_DIR / f"{best_key}_{target}.joblib"
        joblib.dump({
            "model": best_model,
            "feature_names": feature_names,
            "target": target,
            "best_key": best_key,
            "val_metrics": arena_results[best_key]["val_metrics"],
            "test_metrics": test_metrics,
        }, artifact_path)

        self.last_train_meta = {
            "target_column": target,
            "features_used": feature_names,
            "split_info": split_meta,
            "best_model": best_key,
            "best_model_name": config.SUPPORTED_MODELS.get(best_key, best_key),
            "test_metrics": test_metrics,
            "total_samples": len(hourly_df),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
        }

        self.model_results = arena_results

        # Check if ML outperformed baseline
        naive_mae = arena_results.get("seasonal_naive", {}).get("val_metrics", {}).get("mae", 0.0)
        ml_beat_baseline = best_val_mae < naive_mae if best_key != "seasonal_naive" else False

        return {
            "success": True,
            "best_model": best_key,
            "best_model_name": config.SUPPORTED_MODELS.get(best_key, best_key),
            "ml_beat_baseline": ml_beat_baseline,
            "arena_results": arena_results,
            "test_metrics": test_metrics,
            "residuals_diagnostic": residuals_diag,
            "features_count": len(feature_names),
            "features_list": feature_names,
            "split_info": split_meta,
            "artifact_saved": str(artifact_path.name),
        }

    def generate_recursive_forecast(
        self,
        df: pd.DataFrame,
        horizon: int = config.DEFAULT_FORECAST_HORIZON,
        model_key: Optional[str] = None,
        target_col: Optional[str] = None,
        future_weather: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generates genuine recursive 24-hour ahead forecast without lookahead leakage."""
        target = target_col or self.target_column
        selected_key = model_key or self.best_model_key or "seasonal_naive"

        # Ensure model is trained or load from disk
        if selected_key not in self.models:
            artifact_path = config.MODELS_DIR / f"{selected_key}_{target}.joblib"
            if artifact_path.exists():
                saved = joblib.load(artifact_path)
                self.models[selected_key] = saved["model"]
                self.feature_engineer = FeatureEngineering(target_column=target)
                self.feature_engineer.feature_names = saved["feature_names"]
            else:
                # Auto-train
                logger.info(f"Model {selected_key} not in memory; auto-training...")
                self.train_and_compare(df, target_col=target, model_keys=[selected_key, "seasonal_naive"])

        model = self.models.get(selected_key)
        if model is None:
            raise RuntimeError(f"Could not initialize model '{selected_key}'.")

        # Clean hourly series to obtain latest known points
        preprocessor = PreprocessingPipeline(target_column=target)
        hourly_df, _ = preprocessor.clean_and_resample(df, target_col=target)

        # Prepare rolling history (at least 168 hours = 1 week if possible)
        history_window = 168
        recent_df = hourly_df.tail(history_window).copy()
        rolling_series = recent_df.set_index("DateTime")[target].copy()

        last_known_dt = pd.to_datetime(hourly_df["DateTime"].iloc[-1])

        # Map future weather if available
        weather_lookup = {}
        if future_weather:
            for w in future_weather:
                dt_str = w.get("DateTime")
                if dt_str:
                    weather_lookup[pd.to_datetime(dt_str)] = w

        forecast_points = []
        fe = self.feature_engineer or FeatureEngineering(target_column=target)

        # Calculate estimated prediction interval from validation residual std
        val_rmse = self.model_results.get(selected_key, {}).get("val_metrics", {}).get("rmse", 1500.0)
        z_multiplier = 1.96  # 95% interval

        # Recursive generation loop
        for step in range(1, horizon + 1):
            future_dt = last_known_dt + pd.Timedelta(hours=step)
            w_dict = weather_lookup.get(future_dt)

            # Build single-step features using rolling history up to t-1
            feat_df = fe.create_single_step_features(
                historical_series=rolling_series,
                target_timestamp=future_dt,
                weather_dict=w_dict,
            )

            # Predict next step
            pred_val = float(model.predict(feat_df)[0])
            pred_val = max(0.0, pred_val)  # Energy load is non-negative

            # Add to rolling history so future lags (t+1, t+2) use internal prediction!
            rolling_series.loc[future_dt] = pred_val

            # Expanding uncertainty bounds over horizon
            horizon_spread = z_multiplier * val_rmse * (1.0 + 0.02 * (step - 1))
            lower_bound = max(0.0, pred_val - horizon_spread)
            upper_bound = pred_val + horizon_spread

            forecast_points.append({
                "step": step,
                "timestamp": future_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "predicted_demand": round(pred_val, 1),
                "lower_bound": round(lower_bound, 1),
                "upper_bound": round(upper_bound, 1),
            })

        # Summary of forecast
        preds_array = np.array([p["predicted_demand"] for p in forecast_points])
        peak_idx = int(np.argmax(preds_array))
        min_idx = int(np.argmin(preds_array))

        return {
            "success": True,
            "model_used": selected_key,
            "model_name": config.SUPPORTED_MODELS.get(selected_key, selected_key),
            "target_column": target,
            "horizon_hours": horizon,
            "forecast_start": forecast_points[0]["timestamp"],
            "forecast_end": forecast_points[-1]["timestamp"],
            "peak_hour": forecast_points[peak_idx]["timestamp"],
            "peak_demand": forecast_points[peak_idx]["predicted_demand"],
            "min_hour": forecast_points[min_idx]["timestamp"],
            "min_demand": forecast_points[min_idx]["predicted_demand"],
            "mean_demand": round(float(np.mean(preds_array)), 1),
            "forecast_series": forecast_points,
            "recent_historical_series": [
                {
                    "timestamp": row["DateTime"].strftime("%Y-%m-%d %H:%M:%S"),
                    "actual_demand": round(float(row[target]), 1),
                }
                for _, row in hourly_df.tail(48).iterrows()
            ],
            "units": "kW" if "power" in target.lower() else "Units",
        }
