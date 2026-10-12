"""Preprocessing service constructing scikit-learn Pipelines with strict leakage safeguards.
Imputes and scales only on training fold data.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, RobustScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import logging

logger = logging.getLogger(__name__)

class PreprocessingService:
    @staticmethod
    def build_preprocessor(
        numeric_features: List[str],
        categorical_features: List[str],
        scaler: str = "standard", # 'standard', 'robust', or 'none'
    ) -> ColumnTransformer:
        """Constructs a ColumnTransformer fitted strictly on training data."""
        transformers = []

        # 1. Numeric pipeline
        if numeric_features:
            num_steps = [("imputer", SimpleImputer(strategy="median"))]
            if scaler == "standard":
                num_steps.append(("scaler", StandardScaler()))
            elif scaler == "robust":
                num_steps.append(("scaler", RobustScaler()))
            transformers.append(("numeric", Pipeline(num_steps), numeric_features))

        # 2. Categorical pipeline
        if categorical_features:
            cat_steps = [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
            transformers.append(("categorical", Pipeline(cat_steps), categorical_features))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    @staticmethod
    def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
        """Extracts transformed output feature names after preprocessor is fitted."""
        try:
            return list(preprocessor.get_feature_names_out())
        except Exception:
            return []
