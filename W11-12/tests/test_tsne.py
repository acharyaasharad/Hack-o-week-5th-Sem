import pytest
import pandas as pd
from services.dimensionality_service import DimensionalityService

@pytest.fixture
def small_sample():
    from sklearn.datasets import load_wine
    data = load_wine(as_frame=True)
    df = data.data.head(40).copy()
    df["wine_class"] = data.target.head(40).astype(str)
    df["_row_id"] = [f"ROW-{i+1}" for i in range(len(df))]
    return df

def test_tsne_execution(small_sample):
    ds = DimensionalityService()
    features = list(small_sample.columns[:5])
    res = ds.run_tsne(
        df=small_sample,
        features=features,
        perplexity=10.0,
        max_iter=300,
        scaler="standard",
    )
    assert res["status"] == "success"
    assert len(res["coordinates"]) == len(small_sample)
    assert res["trustworthiness"] is not None

def test_tsne_perplexity_guard(small_sample):
    ds = DimensionalityService()
    features = list(small_sample.columns[:5])
    # Pass perplexity >= n_samples (40)
    res = ds.run_tsne(
        df=small_sample,
        features=features,
        perplexity=50.0,
        max_iter=300,
    )
    assert res["status"] == "success"
    assert res["perplexity"] < 40.0
    assert len(res["warnings"]) > 0
