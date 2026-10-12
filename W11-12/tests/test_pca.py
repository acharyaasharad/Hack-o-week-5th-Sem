import pytest
import pandas as pd
from services.dimensionality_service import DimensionalityService

@pytest.fixture
def wine_sample():
    from sklearn.datasets import load_wine
    data = load_wine(as_frame=True)
    df = data.data.copy()
    df["wine_class"] = data.target.astype(str)
    df["_row_id"] = [f"ROW-{i+1}" for i in range(len(df))]
    return df

def test_pca_execution_and_variance(wine_sample):
    ds = DimensionalityService()
    features = list(wine_sample.columns[:6])
    res = ds.run_pca(
        df=wine_sample,
        features=features,
        n_components=2,
        scaler="standard",
        color_by="wine_class",
    )
    assert res["status"] == "success"
    assert len(res["coordinates"]) == len(wine_sample)
    assert res["pc1_variance"] > 0
    assert res["total_2d_variance"] > 0
    assert len(res["loadings"]) > 0
    assert res["trustworthiness"] is not None

def test_pca_3d_mode(wine_sample):
    ds = DimensionalityService()
    features = list(wine_sample.columns[:6])
    res = ds.run_pca(df=wine_sample, features=features, n_components=3)
    assert res["status"] == "success"
    assert "z" in res["coordinates"][0]
