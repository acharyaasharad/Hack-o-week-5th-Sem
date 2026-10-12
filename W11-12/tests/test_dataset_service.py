import pytest
import io
import pandas as pd
from services.dataset_service import DatasetService

def test_load_wine_dataset():
    ds = DatasetService()
    assert ds.load_wine_dataset()
    df = ds.get_active_df()
    assert df is not None
    assert len(df) == 178
    summary = ds.get_summary()
    assert summary["total_rows"] == 178
    assert len(summary["selected_features"]) == 13
    assert summary["color_column"] == "wine_class"

def test_load_iris_dataset():
    ds = DatasetService()
    assert ds.load_iris_dataset()
    df = ds.get_active_df()
    assert len(df) == 150
    assert len(ds._feature_columns) == 4

def test_upload_invalid_csv():
    ds = DatasetService()
    success, msg, _ = ds.load_user_csv(io.BytesIO(b""), "empty.csv")
    assert not success
    assert "empty" in msg.lower()

def test_upload_valid_csv():
    ds = DatasetService()
    csv_bytes = b"F1,F2,F3,Label\n1.2,3.4,5.6,ClassA\n2.2,4.4,6.6,ClassB\n3.2,5.4,7.6,ClassA\n"
    success, msg, summary = ds.load_user_csv(io.BytesIO(csv_bytes), "test_data.csv")
    assert success
    assert summary["total_rows"] == 3
    assert len(summary["numeric_columns"]) == 3
