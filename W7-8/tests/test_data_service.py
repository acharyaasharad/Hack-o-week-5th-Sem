"""Unit tests for DataService: loading, summaries, and validation."""

import pytest
import pandas as pd
import numpy as np
from services.data_service import DataService
import config


def test_data_service_initial_load():
    service = DataService()
    df = service.get_active_dataframe()
    assert df is not None
    assert not df.empty
    assert len(df) > 50


def test_data_service_summary():
    service = DataService()
    summary = service.get_summary()
    assert summary["success"] is True
    assert summary["row_count"] > 0
    assert "DateTime" in summary["timestamp_column"] or "time" in summary["timestamp_column"].lower()
    assert "completeness_score" in summary
    assert "target_stats" in summary


def test_data_service_preview():
    service = DataService()
    preview = service.get_preview(n=5)
    assert "columns" in preview
    assert len(preview["rows"]) <= 5


def test_data_service_upload_validation():
    service = DataService()
    # Test invalid CSV
    success, msg, _ = service.process_uploaded_csv(b"not,a,valid\n", "test.csv")
    assert success is False

    # Test valid small CSV
    valid_csv = (
        "DateTime,Zone1Power,Temperature\n"
        "2024-01-01 00:00:00,25000,15.2\n"
        "2024-01-01 01:00:00,24000,14.8\n"
    ).encode("utf-8")
    success, msg, summary = service.process_uploaded_csv(valid_csv, "custom.csv")
    assert success is True
    assert summary["row_count"] == 2
