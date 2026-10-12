"""Data service module managing dataset ingestion, validation, preview, and leakage guards.
Supports UCI Bank Marketing, UCI Bike Sharing, synthetic demonstration fallbacks, and custom CSV uploads.
"""

from pathlib import Path
import io
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self._active_df: Optional[pd.DataFrame] = None
        self._dataset_id: str = "bank_marketing"
        self._dataset_name: str = "UCI Bank Marketing"
        self._dataset_source: str = config.BANK_ATTRIBUTION
        self._task: str = "classification"  # 'classification' or 'regression'
        self._target_column: str = "deposit_subscribed"
        self._feature_columns: List[str] = []
        self._excluded_columns: List[str] = []
        
        # Load default classification dataset
        self.load_bank_marketing()

    def load_bank_marketing(self) -> bool:
        """Loads Bank Marketing classification dataset with data leakage exclusion safeguards."""
        raw_path = config.DATA_RAW_DIR / "bank_marketing_raw.csv"
        if raw_path.exists():
            try:
                df = pd.read_csv(raw_path)
                self._dataset_name = "UCI Bank Marketing (UCI ID 222)"
                self._dataset_source = config.BANK_ATTRIBUTION
            except Exception:
                df = pd.read_csv(config.SAMPLE_CLASSIFICATION_CSV)
                self._dataset_name = "Synthetic Bank Marketing (Sample)"
                self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"
        else:
            df = pd.read_csv(config.SAMPLE_CLASSIFICATION_CSV)
            self._dataset_name = "Synthetic Bank Marketing (Sample)"
            self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"

        # Target detection
        target = "deposit_subscribed" if "deposit_subscribed" in df.columns else ("y" if "y" in df.columns else df.columns[-1])
        
        # Default features: Exclude target and call 'duration' to prevent real-world predictive leakage
        excluded = [target]
        if "duration" in df.columns:
            excluded.append("duration")

        self._active_df = df
        self._dataset_id = "bank_marketing"
        self._task = "classification"
        self._target_column = target
        self._excluded_columns = [c for c in ["duration"] if c in df.columns]
        self._feature_columns = [c for c in df.columns if c not in excluded]
        return True

    def load_bike_sharing(self) -> bool:
        """Loads Bike Sharing regression dataset with ride-type leakage exclusion safeguards."""
        raw_path = config.DATA_RAW_DIR / "bike_sharing_raw.csv"
        if raw_path.exists():
            try:
                df = pd.read_csv(raw_path)
                self._dataset_name = "UCI Bike Sharing (UCI ID 275)"
                self._dataset_source = config.BIKE_ATTRIBUTION
            except Exception:
                df = pd.read_csv(config.SAMPLE_REGRESSION_CSV)
                self._dataset_name = "Synthetic Bike Sharing (Sample)"
                self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"
        else:
            df = pd.read_csv(config.SAMPLE_REGRESSION_CSV)
            self._dataset_name = "Synthetic Bike Sharing (Sample)"
            self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"

        target = "rental_count" if "rental_count" in df.columns else ("cnt" if "cnt" in df.columns else df.columns[-1])
        
        # Exclude casual, registered, and instant identifiers
        leakage_cols = [c for c in ["casual", "registered", "instant", "dteday"] if c in df.columns]
        excluded = [target] + leakage_cols

        self._active_df = df
        self._dataset_id = "bike_sharing"
        self._task = "regression"
        self._target_column = target
        self._excluded_columns = leakage_cols
        self._feature_columns = [c for c in df.columns if c not in excluded]
        return True

    def load_user_csv(self, file_storage, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates and loads a custom user-uploaded CSV dataset."""
        if not filename or not filename.lower().endswith(".csv"):
            return False, "File must be a valid CSV file (.csv extension).", {}

        try:
            content = file_storage.read()
            if len(content) == 0:
                return False, "The uploaded CSV file is empty.", {}
            if len(content) > config.MAX_CONTENT_LENGTH:
                return False, f"File exceeds maximum allowed upload size of {config.MAX_UPLOAD_MB} MB.", {}

            df = pd.read_csv(io.BytesIO(content))
            if df.empty:
                return False, "The uploaded CSV contains no data rows.", {}

            if len(df) > config.MAX_DATASET_ROWS:
                return False, f"Dataset exceeds maximum row limit of {config.MAX_DATASET_ROWS} records.", {}

            # Clean headers
            df.columns = [str(c).strip() for c in df.columns]
            if len(df.columns) < 2:
                return False, "Dataset must contain at least 2 columns (features + target).", {}

            # Default target is the last column
            target = df.columns[-1]
            
            # Infer task type as a suggestion
            unique_targets = df[target].nunique()
            if pd.api.types.is_numeric_dtype(df[target]) and unique_targets > 15:
                inferred_task = "regression"
            else:
                inferred_task = "classification"

            self._active_df = df
            self._dataset_id = "user_upload"
            self._dataset_name = Path(filename).stem
            self._dataset_source = f"User Upload: {filename}"
            self._task = inferred_task
            self._target_column = target
            self._excluded_columns = []
            self._feature_columns = [c for c in df.columns if c != target]

            summary = self.get_summary()
            return True, f"Successfully uploaded {filename} with {len(df)} rows and {len(df.columns)} columns.", summary
        except Exception as e:
            logger.error("Error processing CSV upload: %s", e)
            return False, f"Failed to parse CSV file: {str(e)}", {}

    def get_active_df(self) -> Optional[pd.DataFrame]:
        return self._active_df

    def get_summary(self) -> Dict[str, Any]:
        """Provides full dataset summary, data quality metrics, and leakage warnings."""
        if self._active_df is None:
            return {"error": "No active dataset loaded"}

        df = self._active_df
        n_rows, n_cols = df.shape

        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = [c for c in df.columns if c not in numeric_cols]

        missing_total = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        warnings = []
        if duplicate_rows > 0:
            warnings.append(f"Detected {duplicate_rows} duplicate rows in dataset.")
        if missing_total > 0:
            warnings.append(f"Detected {missing_total} missing values across features.")

        # Leakage warnings
        if self._dataset_id == "bank_marketing" and "duration" in self._feature_columns:
            warnings.append(
                "CRITICAL LEAKAGE WARNING: 'duration' feature is included. In real banking workflows, "
                "call duration is unknown prior to dialing. Including it causes optimistic bias."
            )
        if self._dataset_id == "bike_sharing":
            for lk in ["casual", "registered"]:
                if lk in self._feature_columns:
                    warnings.append(
                        f"CRITICAL LEAKAGE WARNING: '{lk}' ride count is included. "
                        "Sum of casual + registered directly constitutes total rental count cnt."
                    )

        # Target distribution / stats
        target_info = {}
        if self._target_column in df.columns:
            t_series = df[self._target_column]
            target_info["name"] = self._target_column
            target_info["is_numeric"] = bool(pd.api.types.is_numeric_dtype(t_series))
            target_info["unique_count"] = int(t_series.nunique())
            if self._task == "classification":
                counts = t_series.value_counts().head(10).to_dict()
                target_info["class_distribution"] = {str(k): int(v) for k, v in counts.items()}
            else:
                target_info["mean"] = float(round(t_series.mean(), 2))
                target_info["min"] = float(round(t_series.min(), 2))
                target_info["max"] = float(round(t_series.max(), 2))

        col_stats = {}
        for col in df.columns:
            is_num = col in numeric_cols
            entry = {
                "dtype": str(df[col].dtype),
                "is_numeric": is_num,
                "missing": int(df[col].isnull().sum()),
                "unique": int(df[col].nunique()),
            }
            if is_num:
                s = df[col].dropna()
                if len(s) > 0:
                    entry["mean"] = float(round(s.mean(), 3))
                    entry["std"] = float(round(s.std(), 3)) if len(s) > 1 else 0.0
                    entry["min"] = float(round(s.min(), 3))
                    entry["max"] = float(round(s.max(), 3))
            col_stats[col] = entry

        return {
            "dataset_id": self._dataset_id,
            "dataset_name": self._dataset_name,
            "dataset_source": self._dataset_source,
            "task": self._task,
            "target_column": self._target_column,
            "total_rows": n_rows,
            "row_count": n_rows,
            "total_columns": n_cols,
            "column_count": n_cols,
            "numeric_columns_count": len(numeric_cols),
            "categorical_columns_count": len(categorical_cols),
            "missing_values_count": missing_total,
            "duplicate_rows_count": duplicate_rows,
            "selected_features": self._feature_columns,
            "excluded_columns": self._excluded_columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "target_info": target_info,
            "column_stats": col_stats,
            "warnings": warnings,
        }

    def get_preview(self, page: int = 1, page_size: int = 15, search: str = "") -> Dict[str, Any]:
        """Provides paginated, searchable preview of observations."""
        if self._active_df is None:
            return {"error": "No dataset loaded"}

        df = self._active_df.copy()
        if search:
            mask = df.astype(str).apply(lambda row: row.str.contains(search, case=False, na=False).any(), axis=1)
            df = df[mask]

        total_records = len(df)
        total_pages = max(1, math.ceil(total_records / page_size))
        page = max(1, min(page, total_pages))

        start = (page - 1) * page_size
        end = start + page_size
        page_df = df.iloc[start:end]

        return {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_records": total_records,
            "columns": list(df.columns),
            "data": page_df.to_dict(orient="records"),
        }
