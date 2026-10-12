import pytest
import numpy as np
from services.metrics_service import MetricsService

def test_classification_metrics():
    y_true = np.array([0, 1, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 0, 1])
    
    metrics = MetricsService.evaluate_classification(y_true, y_pred)
    assert "accuracy" in metrics
    assert "f1" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["accuracy"] == 0.8

def test_regression_metrics():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 31.0])
    
    metrics = MetricsService.evaluate_regression(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] > 0
