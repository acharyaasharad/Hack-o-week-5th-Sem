import pytest
import io
import pandas as pd
from services.data_service import DataService
import config

def test_load_sample_classification():
    ds = DataService()
    assert ds.load_bank_marketing() is True
    df = ds.get_active_df()
    assert df is not None
    assert len(df) > 50
    assert ds._task == "classification"
    assert ds._target_column in df.columns

def test_load_sample_regression():
    ds = DataService()
    assert ds.load_bike_sharing() is True
    df = ds.get_active_df()
    assert df is not None
    assert len(df) > 50
    assert ds._task == "regression"
    assert ds._target_column in df.columns

def test_leakage_safeguards():
    ds = DataService()
    ds.load_bank_marketing()
    # In realistic credit/loan scoring, call duration is not known before call
    if "duration" in ds.get_active_df().columns:
        assert "duration" in ds._excluded_columns

    ds.load_bike_sharing()
    # Casual and registered ride counts sum up directly to cnt (circular target leakage)
    df = ds.get_active_df()
    for leak_col in ["casual", "registered"]:
        if leak_col in df.columns:
            assert leak_col in ds._excluded_columns

def test_csv_upload_validation():
    ds = DataService()
    # Valid CSV
    valid_content = io.BytesIO(b"feat1,feat2,target\n1,10,0\n2,20,1\n3,30,0")
    success, msg, summary = ds.load_user_csv(valid_content, "test.csv")
    assert success is True
    assert summary["row_count"] == 3

    # Empty CSV
    empty_content = io.BytesIO(b"")
    success, msg, summary = ds.load_user_csv(empty_content, "empty.csv")
    assert success is False
