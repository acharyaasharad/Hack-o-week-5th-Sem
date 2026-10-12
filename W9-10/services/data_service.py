"""Data service module for dataset ingestion, validation, preview, and summary.
Handles both built-in UCI dataset, synthetic sample dataset, and uploaded CSV files.
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
        self._dataset_name: str = "UCI Wholesale Customers"
        self._dataset_source: str = "Built-in UCI ML Repository (ID 292)"
        self._id_column: Optional[str] = None
        self._feature_columns: List[str] = list(config.DEFAULT_FEATURE_COLUMNS)
        self._categorical_columns: List[str] = []
        self._context_columns: List[str] = list(config.DEFAULT_CONTEXT_COLUMNS)
        
        # Load default dataset upon initialization
        self.load_default_dataset()

    def load_default_dataset(self) -> bool:
        """Loads raw UCI dataset if available, otherwise synthetic sample."""
        if config.UCI_RAW_CSV.exists():
            try:
                self._active_df = pd.read_csv(config.UCI_RAW_CSV)
                self._dataset_name = "Wholesale Customers (UCI ID 292)"
                self._dataset_source = config.UCI_ATTRIBUTION
                self._reset_columns_for_active_df()
                logger.info("Loaded UCI Wholesale Customers dataset: %d rows", len(self._active_df))
                return True
            except Exception as e:
                logger.error("Failed loading UCI raw CSV: %s", e)

        return self.load_sample_dataset()

    def load_sample_dataset(self) -> bool:
        """Loads deterministic synthetic sample dataset."""
        if not config.SAMPLE_CSV.exists():
            from scripts.prepare_data import prepare_sample_data
            prepare_sample_data()

        try:
            self._active_df = pd.read_csv(config.SAMPLE_CSV)
            self._dataset_name = "Synthetic Demonstration Customers"
            self._dataset_source = "Synthetic Demonstration Data (Fixed Seed 42)"
            self._reset_columns_for_active_df()
            logger.info("Loaded synthetic sample dataset: %d rows", len(self._active_df))
            return True
        except Exception as e:
            logger.error("Failed to load sample dataset: %s", e)
            return False

    def load_user_csv(self, file_storage, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Validates and loads a user-uploaded CSV file."""
        if not filename or not filename.lower().endswith(".csv"):
            return False, "File must be a valid CSV file (.csv extension).", {}

        try:
            content = file_storage.read()
            if len(content) == 0:
                return False, "The uploaded CSV file is empty.", {}
            if len(content) > config.MAX_CONTENT_LENGTH:
                return False, f"File exceeds maximum allowed upload size of {config.MAX_UPLOAD_MB} MB.", {}

            # Read into pandas
            df = pd.read_csv(io.BytesIO(content))
            
            if df.empty:
                return False, "The uploaded CSV contains no data rows.", {}

            if len(df.columns) < 2:
                return False, "The uploaded CSV must have at least 2 columns.", {}

            # Clean column names (strip whitespace)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Check for empty column names or duplicate column names
            if any(c == "" or "Unnamed" in c for c in df.columns):
                # Auto-rename or clean
                df.columns = [c if c and "Unnamed" not in c else f"Column_{i}" for i, c in enumerate(df.columns)]
                
            # If duplicated columns exist, rename deduplicate
            cols = pd.Series(df.columns)
            for dup in cols[cols.duplicated()].unique():
                dup_idx = cols[cols == dup].index.values
                for rank, idx in enumerate(dup_idx[1:], start=1):
                    cols.iloc[idx] = f"{dup}_{rank}"
            df.columns = cols

            self._active_df = df
            self._dataset_name = Path(filename).stem
            self._dataset_source = f"User Upload: {filename}"
            self._reset_columns_for_active_df()
            
            summary = self.get_summary()
            return True, f"Successfully uploaded {filename} with {len(df)} rows and {len(df.columns)} columns.", summary
        except Exception as e:
            logger.error("Error processing CSV upload: %s", e)
            return False, f"Failed to parse CSV file: {str(e)}", {}

    def _reset_columns_for_active_df(self):
        """Sets sensible initial defaults for features and context columns."""
        if self._active_df is None:
            return

        cols = list(self._active_df.columns)
        numeric_cols = list(self._active_df.select_dtypes(include=[np.number]).columns)
        categorical_cols = [c for c in cols if c not in numeric_cols]

        # Reset ID column
        self._id_column = None
        for cand in ["id", "customer_id", "customerid", "client_id", "id_customer"]:
            for col in cols:
                if col.lower() == cand:
                    self._id_column = col
                    break
            if self._id_column:
                break

        # Check if Channel and Region exist (UCI schema)
        self._context_columns = [c for c in ["Channel", "Region"] if c in cols]
        
        # Default features: numeric columns excluding ID and context columns
        self._feature_columns = [
            c for c in numeric_cols 
            if c != self._id_column and c not in self._context_columns
        ]
        self._categorical_columns = []

    def get_active_df(self) -> Optional[pd.DataFrame]:
        return self._active_df

    def get_summary(self) -> Dict[str, Any]:
        """Calculates comprehensive dataset statistics and quality warnings."""
        if self._active_df is None:
            return {"error": "No active dataset loaded"}

        df = self._active_df
        n_rows, n_cols = df.shape
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = [c for c in df.columns if c not in numeric_cols]
        
        # Missing values & duplicates
        missing_total = int(df.isnull().sum().sum())
        missing_per_col = {col: int(df[col].isnull().sum()) for col in df.columns}
        duplicate_rows = int(df.duplicated().sum())

        # Quality warnings
        warnings = []
        if duplicate_rows > 0:
            warnings.append(f"Dataset contains {duplicate_rows} duplicate rows.")
        if missing_total > 0:
            warnings.append(f"Dataset contains {missing_total} missing values across columns.")
        
        # Check for constant columns
        constant_cols = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]
        if constant_cols:
            warnings.append(f"Constant columns detected (no variance): {', '.join(constant_cols)}.")

        # Check infinite values in numeric columns
        inf_cols = []
        for col in numeric_cols:
            if np.isinf(df[col]).any():
                inf_cols.append(col)
        if inf_cols:
            warnings.append(f"Infinite values detected in numeric columns: {', '.join(inf_cols)}.")

        # Column stats
        col_stats = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            is_num = col in numeric_cols
            entry = {
                "dtype": dtype_str,
                "is_numeric": is_num,
                "missing": int(df[col].isnull().sum()),
                "unique_values": int(df[col].nunique()),
            }
            if is_num:
                s = df[col].dropna()
                if len(s) > 0:
                    entry["min"] = float(round(s.min(), 2))
                    entry["max"] = float(round(s.max(), 2))
                    entry["mean"] = float(round(s.mean(), 2))
                    entry["median"] = float(round(s.median(), 2))
                    entry["std"] = float(round(s.std(), 2)) if len(s) > 1 else 0.0
                    entry["has_negative"] = bool((s < 0).any())
            else:
                top_counts = df[col].value_counts().head(5).to_dict()
                entry["top_categories"] = {str(k): int(v) for k, v in top_counts.items()}
            col_stats[col] = entry

        return {
            "dataset_name": self._dataset_name,
            "dataset_source": self._dataset_source,
            "total_rows": n_rows,
            "total_columns": n_cols,
            "numeric_columns_count": len(numeric_cols),
            "categorical_columns_count": len(categorical_cols),
            "missing_values_count": missing_total,
            "duplicate_rows_count": duplicate_rows,
            "all_columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "selected_features": self._feature_columns,
            "selected_categorical": self._categorical_columns,
            "context_columns": self._context_columns,
            "id_column": self._id_column,
            "column_stats": col_stats,
            "warnings": warnings,
        }

    def get_preview(self, page: int = 1, page_size: int = 15, search: str = "") -> Dict[str, Any]:
        """Provides paginated and searchable table preview."""
        if self._active_df is None:
            return {"error": "No dataset loaded"}

        df = self._active_df.copy()
        
        # Add index reference column if ID column is not present
        if "_record_id" not in df.columns:
            df.insert(0, "_record_id", [f"CUST-{i+1:04d}" for i in range(len(df))])

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

    def validate_configuration(
        self,
        numeric_features: List[str],
        categorical_features: List[str],
        id_column: Optional[str] = None,
        context_columns: Optional[List[str]] = None,
        log_transform: bool = False,
    ) -> Dict[str, Any]:
        """Validates feature choices before fitting models."""
        if self._active_df is None:
            return {"valid": False, "errors": ["No active dataset is loaded."]}

        errors = []
        warnings = []
        df = self._active_df

        # Check total feature count
        total_features = len(numeric_features) + len(categorical_features)
        if total_features < 2:
            errors.append("At least 2 features are required for multi-dimensional clustering.")

        # Check numeric features exist and are numeric
        for col in numeric_features:
            if col not in df.columns:
                errors.append(f"Numeric feature '{col}' does not exist in dataset.")
            elif not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Feature '{col}' is not numeric.")
            else:
                if df[col].nunique() <= 1:
                    warnings.append(f"Feature '{col}' has zero variance (constant). It will not contribute to clustering.")
                if log_transform and (df[col] < 0).any():
                    errors.append(f"Log transformation (log1p) is invalid for '{col}' because it contains negative values.")

        # Check categorical features
        for col in categorical_features:
            if col not in df.columns:
                errors.append(f"Categorical feature '{col}' does not exist.")
            else:
                n_uniq = df[col].nunique()
                if n_uniq > 50:
                    warnings.append(f"Categorical feature '{col}' has high cardinality ({n_uniq} unique values). One-hot encoding will inflate dimensionality.")
                warnings.append(f"Categorical column '{col}' will be one-hot encoded; note that binary distance changes metric interpretations.")

        # Guard against using ID column in clustering
        if id_column:
            if id_column in numeric_features or id_column in categorical_features:
                errors.append(f"Identifier column '{id_column}' must not be used as a clustering feature.")

        # Update service selections if valid
        if not errors:
            self._feature_columns = numeric_features
            self._categorical_columns = categorical_features
            self._id_column = id_column
            self._context_columns = context_columns or []

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "selected_numeric": numeric_features,
            "selected_categorical": categorical_features,
        }
