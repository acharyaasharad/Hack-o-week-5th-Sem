"""Dataset service module for loading, uploading, and validating datasets.
Supports built-in Wine, Iris, synthetic sample, and user CSV files.
Maintains stable row references (_row_id) aligned with raw observations.
"""

from pathlib import Path
import io
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.datasets import load_wine, load_iris

import config

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self):
        self._active_df: Optional[pd.DataFrame] = None
        self._dataset_name: str = "Wine Recognition Dataset"
        self._dataset_source: str = config.WINE_ATTRIBUTION
        self._dataset_id: str = "wine"
        self._feature_columns: List[str] = []
        self._color_column: Optional[str] = None
        self._id_column: Optional[str] = None
        
        # Load default Wine dataset
        self.load_wine_dataset()

    def load_wine_dataset(self) -> bool:
        """Loads the official scikit-learn Wine recognition dataset (178 rows, 13 features, 3 classes)."""
        try:
            wine_data = load_wine(as_frame=True)
            df = wine_data.data.copy()
            
            # Map target integer classes to descriptive wine categories
            target_names = wine_data.target_names
            df["wine_class"] = wine_data.target.map(lambda x: f"Class_{target_names[x]}")
            
            # Create stable row reference
            df.insert(0, "_row_id", [f"WINE-{i+1:03d}" for i in range(len(df))])

            self._active_df = df
            self._dataset_name = "Wine Recognition Dataset"
            self._dataset_source = config.WINE_ATTRIBUTION
            self._dataset_id = "wine"
            self._color_column = "wine_class"
            self._id_column = "_row_id"
            self._feature_columns = list(wine_data.feature_names)
            return True
        except Exception as e:
            logger.error("Failed loading Wine dataset: %s", e)
            return self.load_sample_dataset()

    def load_iris_dataset(self) -> bool:
        """Loads the built-in scikit-learn Iris dataset (150 rows, 4 features, 3 species)."""
        try:
            iris_data = load_iris(as_frame=True)
            df = iris_data.data.copy()
            target_names = iris_data.target_names
            df["species"] = iris_data.target.map(lambda x: str(target_names[x]))
            df.insert(0, "_row_id", [f"IRIS-{i+1:03d}" for i in range(len(df))])

            self._active_df = df
            self._dataset_name = "Iris Flower Dataset"
            self._dataset_source = config.IRIS_ATTRIBUTION
            self._dataset_id = "iris"
            self._color_column = "species"
            self._id_column = "_row_id"
            self._feature_columns = list(iris_data.feature_names)
            return True
        except Exception as e:
            logger.error("Failed loading Iris dataset: %s", e)
            return False

    def load_sample_dataset(self) -> bool:
        """Loads the deterministic synthetic sample dataset."""
        try:
            if not config.SAMPLE_CSV.exists():
                from scripts.generate_sample_data import save_sample_data
                save_sample_data()

            df = pd.read_csv(config.SAMPLE_CSV)
            if "_row_id" not in df.columns:
                df.insert(0, "_row_id", [f"SYNTH-{i+1:03d}" for i in range(len(df))])

            self._active_df = df
            self._dataset_name = "Synthetic Demonstration Dataset"
            self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"
            self._dataset_id = "sample"
            self._color_column = "Synthetic_Class"
            self._id_column = "_row_id"
            self._feature_columns = [c for c in df.columns if c not in ["_row_id", "Synthetic_Class"]]
            return True
        except Exception as e:
            logger.error("Failed loading sample dataset: %s", e)
            return False

    def load_user_csv(self, file_storage, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates and ingests user-uploaded CSV file."""
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
                return False, "Dataset must contain at least 2 columns.", {}

            # Handle duplicate column names
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                dup_idx = cols[cols == dup].index.values
                for rank, idx in enumerate(dup_idx[1:], start=1):
                    cols.iloc[idx] = f"{dup}_{rank}"
            df.columns = cols

            # Check numeric columns
            numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
            if len(numeric_cols) < 2:
                return False, "Dataset must have at least 2 numeric features for dimensionality reduction.", {}

            # Create stable row reference
            if "_row_id" not in df.columns:
                df.insert(0, "_row_id", [f"ROW-{i+1:04d}" for i in range(len(df))])

            self._active_df = df
            self._dataset_name = Path(filename).stem
            self._dataset_source = f"User Upload: {filename}"
            self._dataset_id = "user_upload"
            self._id_column = "_row_id"
            self._feature_columns = numeric_cols

            # Guess categorical color column if any
            cat_cols = [c for c in df.columns if c not in numeric_cols and c != "_row_id"]
            self._color_column = cat_cols[0] if cat_cols else None

            summary = self.get_summary()
            return True, f"Successfully uploaded {filename} with {len(df)} rows and {len(df.columns)-1} features.", summary
        except Exception as e:
            logger.error("CSV upload processing failed: %s", e)
            return False, f"Failed to parse CSV file: {str(e)}", {}

    def get_active_df(self) -> Optional[pd.DataFrame]:
        return self._active_df

    def get_summary(self) -> Dict[str, Any]:
        """Provides metadata, column metrics, and quality warnings."""
        if self._active_df is None:
            return {"error": "No active dataset loaded"}

        df = self._active_df
        n_rows, n_cols = df.shape
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = [c for c in df.columns if c not in numeric_cols and c != "_row_id"]

        missing_total = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated(subset=[c for c in df.columns if c != "_row_id"]).sum())

        warnings = []
        if duplicate_rows > 0:
            warnings.append(f"Detected {duplicate_rows} duplicate rows.")
        if missing_total > 0:
            warnings.append(f"Dataset contains {missing_total} missing values.")

        constant_cols = [c for c in numeric_cols if df[c].nunique(dropna=False) <= 1]
        if constant_cols:
            warnings.append(f"Constant features detected (zero variance): {', '.join(constant_cols)}.")

        # Class distribution if color column is present
        class_dist = {}
        if self._color_column and self._color_column in df.columns:
            counts = df[self._color_column].value_counts().head(10).to_dict()
            class_dist = {str(k): int(v) for k, v in counts.items()}

        col_stats = {}
        for col in df.columns:
            if col == "_row_id":
                continue
            dtype_str = str(df[col].dtype)
            is_num = col in numeric_cols
            entry = {
                "dtype": dtype_str,
                "is_numeric": is_num,
                "missing": int(df[col].isnull().sum()),
                "unique": int(df[col].nunique()),
            }
            if is_num:
                s = df[col].dropna()
                if len(s) > 0:
                    entry["min"] = float(round(s.min(), 3))
                    entry["max"] = float(round(s.max(), 3))
                    entry["mean"] = float(round(s.mean(), 3))
                    entry["std"] = float(round(s.std(), 3)) if len(s) > 1 else 0.0
                    entry["has_negative"] = bool((s < 0).any())
            col_stats[col] = entry

        return {
            "dataset_id": self._dataset_id,
            "dataset_name": self._dataset_name,
            "dataset_source": self._dataset_source,
            "total_rows": n_rows,
            "total_columns": n_cols - 1, # Exclude internal _row_id
            "numeric_columns_count": len(numeric_cols),
            "categorical_columns_count": len(categorical_cols),
            "missing_values_count": missing_total,
            "duplicate_rows_count": duplicate_rows,
            "constant_columns": constant_cols,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "selected_features": self._feature_columns,
            "color_column": self._color_column,
            "class_distribution": class_dist,
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
