"""Preprocessing service for scikit-learn Pipelines.
Constructs ColumnTransformers for missing-value imputation, feature scaling,
optional log1p transformation, and optional categorical one-hot encoding.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, RobustScaler, OneHotEncoder, FunctionTransformer
from sklearn.impute import SimpleImputer
import logging

logger = logging.getLogger(__name__)

class PreprocessingService:
    @staticmethod
    def create_preprocessor(
        numeric_features: List[str],
        categorical_features: Optional[List[str]] = None,
        scaler: str = "standard",  # 'standard', 'robust', or 'none'
        log_transform: bool = False,
        numeric_impute_strategy: str = "median",
    ) -> Tuple[ColumnTransformer, List[Dict[str, Any]]]:
        """Builds a scikit-learn ColumnTransformer encapsulating preprocessing steps."""
        transformers = []
        steps_info = []

        categorical_features = categorical_features or []

        # 1. Numeric pipeline
        numeric_steps = []
        numeric_steps.append(("imputer", SimpleImputer(strategy=numeric_impute_strategy)))
        steps_info.append({
            "name": "Imputation",
            "transformer": f"SimpleImputer(strategy='{numeric_impute_strategy}')",
            "features": numeric_features,
            "description": "Fills missing values with feature median."
        })

        if log_transform:
            numeric_steps.append(("log1p", FunctionTransformer(np.log1p, validate=True, feature_names_out="one-to-one")))
            steps_info.append({
                "name": "Log Transformation",
                "transformer": "FunctionTransformer(np.log1p)",
                "features": numeric_features,
                "description": "Applies log(1 + x) to stabilize variance across skewed variables."
            })

        if scaler == "standard":
            numeric_steps.append(("scaler", StandardScaler()))
            steps_info.append({
                "name": "Standardization",
                "transformer": "StandardScaler()",
                "features": numeric_features,
                "description": "Transforms features to zero mean and unit variance."
            })
        elif scaler == "robust":
            numeric_steps.append(("scaler", RobustScaler()))
            steps_info.append({
                "name": "Robust Scaling",
                "transformer": "RobustScaler()",
                "features": numeric_features,
                "description": "Scales using median and interquartile range (resistant to outliers)."
            })
        elif scaler == "none":
            steps_info.append({
                "name": "No Scaling",
                "transformer": "None",
                "features": numeric_features,
                "description": "Raw unscaled features retained."
            })

        numeric_pipe = Pipeline(numeric_steps)
        transformers.append(("numeric", numeric_pipe, numeric_features))

        # 2. Categorical pipeline
        if categorical_features:
            cat_steps = [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
            cat_pipe = Pipeline(cat_steps)
            transformers.append(("categorical", cat_pipe, categorical_features))
            steps_info.append({
                "name": "Categorical Encoding",
                "transformer": "OneHotEncoder(handle_unknown='ignore')",
                "features": categorical_features,
                "description": "Encodes categories as indicator dummy columns."
            })

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            verbose_feature_names_out=False
        )

        return preprocessor, steps_info

    @staticmethod
    def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
        """Extracts output feature names after ColumnTransformer is fitted."""
        try:
            return list(preprocessor.get_feature_names_out())
        except Exception:
            names = []
            for name, trans, cols in preprocessor.transformers_:
                if name == "remainder":
                    continue
                if hasattr(trans, "get_feature_names_out"):
                    names.extend(list(trans.get_feature_names_out(cols)))
                else:
                    names.extend(cols)
            return names
