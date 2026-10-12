import pytest
import io
import pandas as pd
from services.data_service import DataService

def test_load_default_and_sample():
    ds = DataService()
    assert ds.get_active_df() is not None
    assert len(ds.get_active_df()) == 440
    summary = ds.get_summary()
    assert summary["total_rows"] == 440
    assert len(summary["selected_features"]) == 6

def test_upload_invalid_csv():
    ds = DataService()
    # Empty stream
    empty_stream = io.BytesIO(b"")
    success, msg, _ = ds.load_user_csv(empty_stream, "empty.csv")
    assert not success
    assert "empty" in msg.lower()

    # Non-csv extension
    success, msg, _ = ds.load_user_csv(io.BytesIO(b"a,b\n1,2"), "data.txt")
    assert not success

def test_upload_valid_csv():
    ds = DataService()
    csv_bytes = b"Fresh,Milk,Grocery,Other\n1000,2000,3000,400\n500,600,700,800\n"
    success, msg, summary = ds.load_user_csv(io.BytesIO(csv_bytes), "test_custom.csv")
    assert success
    assert summary["total_rows"] == 2
    assert summary["total_columns"] == 4

def test_validate_configuration():
    ds = DataService()
    # At least 2 features required
    res = ds.validate_configuration(numeric_features=["Fresh"], categorical_features=[])
    assert not res["valid"]

    # Valid selection
    res2 = ds.validate_configuration(numeric_features=["Fresh", "Milk"], categorical_features=[])
    assert res2["valid"]
