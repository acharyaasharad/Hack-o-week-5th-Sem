import pytest
import numpy as np
import pandas as pd
from services.preprocessing_service import PreprocessingService

def test_preprocessing_pipeline_standard():
    features = ["Alcohol", "Ash", "Magnesium"]
    preprocessor, steps = PreprocessingService.create_preprocessor(
        numeric_features=features,
        scaler="standard",
        log_transform=False,
    )
    df = pd.DataFrame({
        "Alcohol": [12.0, np.nan, 14.0],
        "Ash": [2.1, 2.3, 2.5],
        "Magnesium": [100.0, 110.0, 120.0],
    })
    X_trans = preprocessor.fit_transform(df)
    assert X_trans.shape == (3, 3)
    assert not np.isnan(X_trans).any()

def test_preprocessing_robust_and_log():
    features = ["Alcohol", "Ash"]
    preprocessor, _ = PreprocessingService.create_preprocessor(
        numeric_features=features,
        scaler="robust",
        log_transform=True,
    )
    df = pd.DataFrame({"Alcohol": [10.0, 12.0, 14.0], "Ash": [1.0, 2.0, 3.0]})
    X_trans = preprocessor.fit_transform(df)
    assert X_trans.shape == (3, 2)
