"""Preprocessing service for scikit-learn Pipelines.
Constructs modular ColumnTransformers with SimpleImputer, StandardScaler/RobustScaler,
optional numpy.log1p FunctionTransformer, and OneHotEncoder.
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
        scaling_method: str = "standard",  # 'standard' or 'robust' or 'none'
        log_transform: bool = False,
        numeric_impute_strategy: str = "median",
        categorical_impute_strategy: str = "most_frequent",
    ) -> Tuple[ColumnTransformer, List[Dict[str, Any]]]:
        """Builds a scikit-learn ColumnTransformer encapsulating all preprocessing steps."""
        transformers = []
        pipeline_description = []

        categorical_features = categorical_features or []

        # 1. Numeric pipeline
        numeric_steps = []
        # Imputation
        numeric_steps.append(("imputer", SimpleImputer(strategy=numeric_impute_strategy)))
        pipeline_description.append({
            "step": "Numeric Imputation",
            "transformer": f"SimpleImputer(strategy='{numeric_impute_strategy}')",
            "features": numeric_features,
            "purpose": "Handle missing values using median (or specified strategy) to avoid bias."
        })

        # Optional Log1p transform
        if log_transform:
            numeric_steps.append(("log1p", FunctionTransformer(np.log1p, validate=True, feature_names_out="one-to-one")))
            pipeline_description.append({
                "step": "Log Transformation",
                "transformer": "FunctionTransformer(np.log1p)",
                "features": numeric_features,
                "purpose": "Compress right-skewed spending distributions and stabilize variance."
            })

        # Scaling
        if scaling_method == "standard":
            numeric_steps.append(("scaler", StandardScaler()))
            pipeline_description.append({
                "step": "Feature Scaling",
                "transformer": "StandardScaler()",
                "features": numeric_features,
                "purpose": "Normalize features to zero mean and unit variance for distance calculations."
            })
        elif scaling_method == "robust":
            numeric_steps.append(("scaler", RobustScaler()))
            pipeline_description.append({
                "step": "Feature Scaling",
                "transformer": "RobustScaler()",
                "features": numeric_features,
                "purpose": "Scale features using median and IQR, robust to extreme spend outliers."
            })
        elif scaling_method == "none":
            pipeline_description.append({
                "step": "Feature Scaling",
                "transformer": "None",
                "features": numeric_features,
                "purpose": "No scaling applied. Features maintain raw relative magnitudes."
            })

        numeric_pipe = Pipeline(numeric_steps)
        transformers.append(("numeric", numeric_pipe, numeric_features))

        # 2. Categorical pipeline
        if categorical_features:
            cat_steps = [
                ("imputer", SimpleImputer(strategy=categorical_impute_strategy)),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
            cat_pipe = Pipeline(cat_steps)
            transformers.append(("categorical", cat_pipe, categorical_features))
            pipeline_description.append({
                "step": "Categorical Encoding",
                "transformer": "OneHotEncoder(handle_unknown='ignore')",
                "features": categorical_features,
                "purpose": "Convert categorical dimensions into dummy indicators for metric distance."
            })

        preprocessor = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            verbose_feature_names_out=False
        )

        return preprocessor, pipeline_description

    @staticmethod
    def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
        """Extracts output feature names after ColumnTransformer is fitted."""
        try:
            return list(preprocessor.get_feature_names_out())
        except Exception:
            # Fallback
            names = []
            for name, trans, cols in preprocessor.transformers_:
                if name == "remainder":
                    continue
                if hasattr(trans, "get_feature_names_out"):
                    names.extend(list(trans.get_feature_names_out(cols)))
                else:
                    names.extend(cols)
            return names
