"""Data management and dataset service.
Handles dataset loading, validation, summary statistics, preview generation, and uploads.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import io
import logging
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)


class DataService:
    """Manages raw, sample, processed, and uploaded datasets with in-memory caching."""

    def __init__(self):
        self._active_df: Optional[pd.DataFrame] = None
        self._active_source_name: str = "sample"
        self._active_target_col: str = config.DEFAULT_TARGET_COLUMN
        self._active_timestamp_col: str = config.DEFAULT_TIMESTAMP_COLUMN
        self._load_initial_dataset()

    def _load_initial_dataset(self) -> None:
        """Loads sample or processed dataset on startup."""
        if config.PROCESSED_DATASET_PATH.exists():
            try:
                self._active_df = pd.read_csv(config.PROCESSED_DATASET_PATH)
                self._active_source_name = "processed_tetouan"
                logger.info(f"Loaded processed dataset from {config.PROCESSED_DATASET_PATH}")
                return
            except Exception as exc:
                logger.warning(f"Failed loading processed dataset: {exc}")

        if config.SAMPLE_DATASET_PATH.exists():
            try:
                self._active_df = pd.read_csv(config.SAMPLE_DATASET_PATH)
                self._active_source_name = "sample_energy"
                logger.info(f"Loaded sample dataset from {config.SAMPLE_DATASET_PATH}")
                return
            except Exception as exc:
                logger.warning(f"Failed loading sample dataset: {exc}")

        logger.warning("No default dataset could be loaded on startup.")

    def get_active_dataframe(self) -> Optional[pd.DataFrame]:
        """Returns a copy of the currently active DataFrame."""
        if self._active_df is None:
            self._load_initial_dataset()
        return self._active_df.copy() if self._active_df is not None else None

    def set_active_dataframe(self, df: pd.DataFrame, source_name: str, target_col: Optional[str] = None, timestamp_col: Optional[str] = None) -> None:
        """Updates the active in-memory DataFrame."""
        self._active_df = df.copy()
        self._active_source_name = source_name
        if target_col:
            self._active_target_col = target_col
        if timestamp_col:
            self._active_timestamp_col = timestamp_col

    def get_active_meta(self) -> Dict[str, Any]:
        """Returns metadata about the active dataset."""
        return {
            "source_name": self._active_source_name,
            "target_column": self._active_target_col,
            "timestamp_column": self._active_timestamp_col,
            "is_loaded": self._active_df is not None,
            "row_count": len(self._active_df) if self._active_df is not None else 0,
        }

    def load_dataset_by_name(self, name: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """Loads one of the predefined datasets: 'sample', 'processed', or 'raw'."""
        path_map = {
            "sample": config.SAMPLE_DATASET_PATH,
            "processed": config.PROCESSED_DATASET_PATH,
            "raw": config.RAW_DATASET_PATH,
        }
        target_path = path_map.get(name)
        if not target_path or not target_path.exists():
            # If processed does not exist but sample does, fallback
            if name == "processed" and config.SAMPLE_DATASET_PATH.exists():
                target_path = config.SAMPLE_DATASET_PATH
            else:
                return False, f"Dataset '{name}' does not exist on disk.", None

        try:
            df = pd.read_csv(target_path)
            self._active_df = df
            self._active_source_name = name
            return True, f"Successfully loaded {name} dataset ({len(df):,} records).", df
        except Exception as exc:
            return False, f"Failed loading dataset {name}: {str(exc)}", None

    def get_summary(self, df: Optional[pd.DataFrame] = None, target_col: Optional[str] = None, timestamp_col: Optional[str] = None) -> Dict[str, Any]:
        """Calculates comprehensive summary statistics and quality diagnostics."""
        target_df = df if df is not None else self._active_df
        if target_df is None or target_df.empty:
            return {
                "success": False,
                "error": "No dataset currently loaded.",
            }

        target = target_col or self._active_target_col
        ts_col = timestamp_col or self._active_timestamp_col

        # Find valid timestamp column if configured one is missing
        if ts_col not in target_df.columns:
            for c in ["DateTime", "datetime", "Date", "timestamp", "time"]:
                if c in target_df.columns:
                    ts_col = c
                    break
            else:
                ts_col = target_df.columns[0]

        # Find valid target column if configured one is missing
        numeric_cols = target_df.select_dtypes(include=[np.number]).columns.tolist()
        if target not in target_df.columns:
            for c in config.AVAILABLE_TARGET_COLUMNS:
                if c in target_df.columns:
                    target = c
                    break
            else:
                target = numeric_cols[0] if numeric_cols else target_df.columns[-1]

        # Timestamp parsing and frequency analysis
        date_series = pd.to_datetime(target_df[ts_col], errors="coerce")
        valid_dates = date_series.dropna()
        
        freq_detected = "Unknown"
        missing_intervals = 0
        duplicate_timestamps = int(target_df[ts_col].duplicated().sum())

        if len(valid_dates) > 1:
            diffs = valid_dates.sort_values().diff().dropna()
            median_seconds = diffs.dt.total_seconds().median() if not diffs.empty else 0
            if 500 <= median_seconds <= 700:
                freq_detected = "10 Minutes"
            elif 3400 <= median_seconds <= 3800:
                freq_detected = "Hourly (1 Hour)"
            elif 85000 <= median_seconds <= 87000:
                freq_detected = "Daily (24 Hours)"
            else:
                freq_detected = f"~{int(median_seconds)} seconds"

        # Quality metrics
        missing_counts = target_df.isnull().sum().to_dict()
        total_missing = int(target_df.isnull().sum().sum())
        total_cells = int(target_df.shape[0] * target_df.shape[1])
        completeness_pct = round((1.0 - (total_missing / total_cells if total_cells > 0 else 0)) * 100, 2)

        # Target statistics
        target_stats = {}
        if target in target_df.columns and pd.api.types.is_numeric_dtype(target_df[target]):
            s = target_df[target].dropna()
            target_stats = {
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2),
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
                "median": round(float(s.median()), 2),
                "q25": round(float(s.quantile(0.25)), 2),
                "q75": round(float(s.quantile(0.75)), 2),
            }

        # Available target columns in current dataset
        available_targets = [c for c in config.AVAILABLE_TARGET_COLUMNS if c in target_df.columns]
        if not available_targets:
            available_targets = numeric_cols[:5]

        # Weather columns present
        weather_cols = [c for c in config.DEFAULT_WEATHER_COLUMNS if c in target_df.columns]

        return {
            "success": True,
            "source_name": self._active_source_name,
            "row_count": int(len(target_df)),
            "column_count": int(len(target_df.columns)),
            "columns": list(target_df.columns),
            "numeric_columns": numeric_cols,
            "timestamp_column": ts_col,
            "target_column": target,
            "available_targets": available_targets,
            "weather_columns": weather_cols,
            "frequency": freq_detected,
            "start_time": str(valid_dates.min()) if not valid_dates.empty else None,
            "end_time": str(valid_dates.max()) if not valid_dates.empty else None,
            "completeness_score": completeness_pct,
            "duplicate_timestamps": duplicate_timestamps,
            "total_missing_values": total_missing,
            "missing_per_column": missing_counts,
            "target_stats": target_stats,
            "demand_unit": "kW" if "power" in target.lower() else "Units",
        }

    def get_preview(self, df: Optional[pd.DataFrame] = None, n: int = 15) -> Dict[str, Any]:
        """Returns JSON-serializable preview records and column descriptors."""
        target_df = df if df is not None else self._active_df
        if target_df is None or target_df.empty:
            return {"columns": [], "rows": [], "total_rows": 0}

        head_df = target_df.head(n).copy()
        
        # Format floating-point values for cleaner display
        for col in head_df.select_dtypes(include=[np.number]).columns:
            head_df[col] = head_df[col].apply(lambda x: round(float(x), 2) if pd.notnull(x) else None)

        return {
            "columns": list(head_df.columns),
            "rows": head_df.to_dict(orient="records"),
            "total_rows": len(target_df),
        }

    def process_uploaded_csv(self, file_content: bytes, filename: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validates and ingests an uploaded CSV file."""
        if len(file_content) > config.MAX_CONTENT_LENGTH:
            return False, f"File exceeds maximum allowed size of {config.MAX_CONTENT_LENGTH // (1024*1024)}MB.", None

        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception as exc:
            return False, f"Failed to parse CSV file: {str(exc)}", None

        if df.empty or len(df.columns) < 2:
            return False, "CSV must contain at least 2 columns and at least 1 record.", None

        # Clean column names
        df.columns = [c.strip() for c in df.columns]

        # Determine timestamp and target candidates
        ts_candidates = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "timestamp"])]
        ts_col = ts_candidates[0] if ts_candidates else df.columns[0]

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            return False, "CSV must contain at least one numeric power/energy column.", None

        target_col = num_cols[0]
        for candidate in ["zone1power", "power", "demand", "consumption", "load", "kwh", "kw"]:
            matching = [c for c in num_cols if candidate in c.lower()]
            if matching:
                target_col = matching[0]
                break

        # Save to raw folder as user upload
        safe_filename = f"upload_{Path(filename).name}"
        upload_path = config.DATA_RAW_DIR / safe_filename
        df.to_csv(upload_path, index=False)

        # Set active dataframe
        self.set_active_dataframe(df, source_name=safe_filename, target_col=target_col, timestamp_col=ts_col)
        summary = self.get_summary(df, target_col=target_col, timestamp_col=ts_col)

        return True, f"Successfully uploaded and activated {safe_filename} ({len(df):,} rows).", summary
