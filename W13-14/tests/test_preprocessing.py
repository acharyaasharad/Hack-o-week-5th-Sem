import pytest
import pandas as pd
import numpy as np
from services.preprocessing_service import PreprocessingService

def test_preprocessing_pipeline_fit_transform():
    ps = PreprocessingService()
    df = pd.DataFrame({
        "num1": [1.0, 2.0, np.nan, 4.0],
        "cat1": ["a", "b", "a", None]
    })
    
    transformer = ps.build_preprocessor(numeric_features=["num1"], categorical_features=["cat1"], scaler="standard")
    transformed = transformer.fit_transform(df)
    
    assert transformed.shape[0] == 4
    assert transformed.shape[1] >= 2

def test_prevent_preprocessing_leakage():
    ps = PreprocessingService()
    train_df = pd.DataFrame({"num": [10.0, 20.0, 30.0]})
    test_df = pd.DataFrame({"num": [40.0, 50.0]})
    
    transformer = ps.build_preprocessor(numeric_features=["num"], categorical_features=[], scaler="standard")
    # Fitting on train only
    transformer.fit(train_df)
    
    # Mean of train is 20.0. Transforming 20.0 should yield 0.0
    val_transformed = transformer.transform(pd.DataFrame({"num": [20.0]}))
    assert np.isclose(val_transformed[0][0], 0.0)
