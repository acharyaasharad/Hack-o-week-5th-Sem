import pytest
import pandas as pd
from services.split_service import SplitService

def test_split_ratios_and_no_overlap():
    df = pd.DataFrame({
        "feat": range(100),
        "target": [0, 1] * 50
    })
    
    splits = SplitService.create_splits(
        df=df,
        target_column="target",
        feature_columns=["feat"],
        task="classification",
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42
    )
    
    # Verify two-stage split produces expected partition sizes within 1 sample (e.g. 69 or 70)
    assert abs(len(splits["X_train"]) - 70) <= 1
    assert abs(len(splits["X_val"]) - 15) <= 1
    assert len(splits["X_test"]) == 15
    assert len(splits["X_train"]) + len(splits["X_val"]) + len(splits["X_test"]) == 100
    
    # Check strictly disjoint indices
    train_idx = set(splits["X_train"].index)
    val_idx = set(splits["X_val"].index)
    test_idx = set(splits["X_test"].index)
    
    assert len(train_idx.intersection(val_idx)) == 0
    assert len(train_idx.intersection(test_idx)) == 0
    assert len(val_idx.intersection(test_idx)) == 0
