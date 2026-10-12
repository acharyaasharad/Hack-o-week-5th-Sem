import pytest
import numpy as np
import pandas as pd
from services.preprocessing import PreprocessingService

def test_preprocessing_pipeline_creation():
    numeric = ["Fresh", "Milk", "Grocery"]
    preprocessor, steps = PreprocessingService.create_preprocessor(
        numeric_features=numeric,
        scaling_method="standard",
        log_transform=True,
    )
    assert len(steps) == 3
    df = pd.DataFrame({
        "Fresh": [100.0, np.nan, 300.0],
        "Milk": [50.0, 70.0, 90.0],
        "Grocery": [20.0, 30.0, 40.0],
    })
    X_trans = preprocessor.fit_transform(df)
    assert X_trans.shape == (3, 3)
    # Check no NaNs after imputation
    assert not np.isnan(X_trans).any()

def test_preprocessing_robust_scaling():
    numeric = ["Fresh", "Milk"]
    preprocessor, _ = PreprocessingService.create_preprocessor(
        numeric_features=numeric,
        scaling_method="robust",
        log_transform=False,
    )
    df = pd.DataFrame({"Fresh": [10, 20, 300], "Milk": [5, 10, 15]})
    X_trans = preprocessor.fit_transform(df)
    assert X_trans.shape == (3, 2)
