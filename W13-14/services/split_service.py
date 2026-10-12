"""Split service module managing fair train, validation, and held-out test partitioning.
Guarantees consistent splits across all competing models and prevents data leakage.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import logging

import config

logger = logging.getLogger(__name__)

class SplitService:
    @staticmethod
    def create_splits(
        df: pd.DataFrame,
        target_column: str,
        feature_columns: list,
        task: str = "classification",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = config.RANDOM_STATE,
    ) -> Dict[str, Any]:
        """Splits the raw dataframe into train, validation, and test subsets.
        Applies stratification for classification when target classes permit.
        """
        # Clean target dropna
        clean_df = df.dropna(subset=[target_column]).copy()
        X = clean_df[feature_columns]
        y = clean_df[target_column]

        # First split off test set: size = test_ratio
        stratify_1 = y if (task == "classification" and y.value_counts().min() >= 2) else None

        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=test_ratio,
            random_state=random_state,
            stratify=stratify_1
        )

        # Second split: train vs val from temp
        # Relative val ratio in temp
        rel_val_ratio = val_ratio / (train_ratio + val_ratio)
        stratify_2 = y_temp if (task == "classification" and y_temp.value_counts().min() >= 2) else None

        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=rel_val_ratio,
            random_state=random_state,
            stratify=stratify_2
        )

        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "sizes": {
                "train_count": len(X_train),
                "val_count": len(X_val),
                "test_count": len(X_test),
                "total_count": len(clean_df),
                "train_pct": round((len(X_train) / len(clean_df)) * 100, 1),
                "val_pct": round((len(X_val) / len(clean_df)) * 100, 1),
                "test_pct": round((len(X_test) / len(clean_df)) * 100, 1),
            }
        }
