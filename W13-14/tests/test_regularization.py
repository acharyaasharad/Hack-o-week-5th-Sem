import pytest
from services.split_service import SplitService
from services.regularization_service import RegularizationService
import pandas as pd

def test_regularization_sweep_simulation():
    # Create simple linear classification dataset
    df = pd.DataFrame({
        "x1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] * 5,
        "x2": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0] * 5,
        "target": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1] * 5
    })
    splits = SplitService.create_splits(df, target_column="target", feature_columns=["x1", "x2"], task="classification")
    
    res = RegularizationService.run_regularization_sweep(
        splits=splits,
        model_id="logistic_l1",
        task="classification",
        strength_param="C",
        strengths=[0.01, 1.0, 100.0]
    )
    
    assert "strengths" in res
    assert "val_scores" in res
    assert len(res["val_scores"]) == 3
    assert "zero_coef_counts" in res
