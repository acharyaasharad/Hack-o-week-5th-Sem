"""Evaluation and diagnostic metrics for energy forecasting models.
Calculates MAE, RMSE, WAPE, MAPE, R2, residual profiles, and peak anomaly screenings.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class ModelEvaluator:
    """Calculates forecasting evaluation metrics and residual distributions."""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculates regression metrics with zero guards."""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        # Handle empty or invalid arrays
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                "mae": 0.0,
                "rmse": 0.0,
                "wape": 0.0,
                "mape": 0.0,
                "r2": 0.0,
                "sample_count": 0,
            }

        # Mask NaNs
        mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
        if mask.sum() == 0:
            return {"mae": 0.0, "rmse": 0.0, "wape": 0.0, "mape": 0.0, "r2": 0.0, "sample_count": 0}

        yt = y_true[mask]
        yp = y_pred[mask]

        mae = float(mean_absolute_error(yt, yp))
        rmse = float(np.sqrt(mean_squared_error(yt, yp)))

        # WAPE (Weighted Absolute Percentage Error)
        sum_actual = float(np.sum(yt))
        if sum_actual > 0:
            wape = float((np.sum(np.abs(yt - yp)) / sum_actual) * 100.0)
        else:
            wape = 0.0

        # MAPE with guard against near-zero actuals
        non_zero = np.abs(yt) > 1e-4
        if non_zero.sum() > 0:
            mape = float(np.mean(np.abs((yt[non_zero] - yp[non_zero]) / yt[non_zero])) * 100.0)
        else:
            mape = 0.0

        r2 = float(r2_score(yt, yp)) if len(yt) > 1 else 0.0

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "wape": round(wape, 2),
            "mape": round(mape, 2),
            "r2": round(r2, 4),
            "sample_count": int(len(yt)),
        }

    @staticmethod
    def calculate_residuals(
        timestamps: List[str],
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:
        """Analyzes residuals (y_true - y_pred) across time and hours of day."""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        residuals = y_true - y_pred
        abs_errors = np.abs(residuals)

        # Parse timestamps for hourly breakdown
        ts_series = pd.to_datetime(timestamps)
        df_res = pd.DataFrame({
            "timestamp": timestamps,
            "hour": ts_series.hour,
            "actual": y_true,
            "predicted": y_pred,
            "residual": residuals,
            "abs_error": abs_errors,
        })

        # Hourly breakdown (0 - 23)
        hourly_summary = []
        for h in range(24):
            sub = df_res[df_res["hour"] == h]
            if not sub.empty:
                hourly_summary.append({
                    "hour": h,
                    "mae": round(float(sub["abs_error"].mean()), 2),
                    "mean_actual": round(float(sub["actual"].mean()), 2),
                    "mean_pred": round(float(sub["predicted"].mean()), 2),
                    "count": int(len(sub)),
                })
            else:
                hourly_summary.append({
                    "hour": h,
                    "mae": 0.0,
                    "mean_actual": 0.0,
                    "mean_pred": 0.0,
                    "count": 0,
                })

        # Histogram of residuals (20 bins)
        hist, bin_edges = np.histogram(residuals, bins=20)
        hist_bins = []
        for i in range(len(hist)):
            hist_bins.append({
                "range_min": round(float(bin_edges[i]), 2),
                "range_max": round(float(bin_edges[i + 1]), 2),
                "count": int(hist[i]),
            })

        std_res = float(np.std(residuals))
        mean_res = float(np.mean(residuals))

        return {
            "mean_residual": round(mean_res, 2),
            "std_residual": round(std_res, 2),
            "max_error": round(float(np.max(abs_errors)), 2) if len(abs_errors) > 0 else 0.0,
            "hourly_mae": hourly_summary,
            "histogram": hist_bins,
            "sample_residuals": [
                {
                    "timestamp": row["timestamp"],
                    "actual": round(float(row["actual"]), 2),
                    "predicted": round(float(row["predicted"]), 2),
                    "residual": round(float(row["residual"]), 2),
                }
                for _, row in df_res.tail(100).iterrows()
            ],
        }

    @staticmethod
    def detect_peaks_and_anomalies(
        timestamps: List[str],
        values: np.ndarray,
        threshold: Optional[float] = None,
        percentile: float = 90.0,
    ) -> Dict[str, Any]:
        """Screens energy load for top demand peaks and anomalous spikes."""
        values = np.asarray(values, dtype=float)
        if len(values) == 0:
            return {"peaks": [], "anomalies": [], "threshold_used": 0.0}

        if threshold is None:
            threshold = float(np.percentile(values, percentile))

        peak_indices = np.where(values >= threshold)[0]
        peaks = [
            {
                "timestamp": timestamps[idx],
                "demand": round(float(values[idx]), 2),
                "excess": round(float(values[idx] - threshold), 2),
            }
            for idx in peak_indices
        ]

        # Statistical anomaly detection via 2.5 * std deviation from rolling or overall mean
        mean_val = float(np.mean(values))
        std_val = float(np.std(values))
        anomaly_threshold = mean_val + 2.5 * std_val
        anomaly_indices = np.where(values > anomaly_threshold)[0]

        anomalies = [
            {
                "timestamp": timestamps[idx],
                "demand": round(float(values[idx]), 2),
                "z_score": round(float((values[idx] - mean_val) / (std_val if std_val > 0 else 1.0)), 2),
            }
            for idx in anomaly_indices
        ]

        return {
            "threshold_used": round(threshold, 2),
            "percentile_used": percentile,
            "peak_count": len(peaks),
            "peaks": sorted(peaks, key=lambda x: x["demand"], reverse=True)[:50],
            "anomaly_count": len(anomalies),
            "anomalies": sorted(anomalies, key=lambda x: x["demand"], reverse=True)[:25],
        }
