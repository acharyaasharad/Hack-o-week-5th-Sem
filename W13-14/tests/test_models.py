import pytest
from services.model_registry import ModelRegistry

def test_model_registry_classification_models():
    clf_models = ModelRegistry.get_supported_models("classification")
    ids = [m["id"] for m in clf_models]
    
    assert "dummy" in ids
    assert "decision_tree" in ids
    assert "bagging" in ids
    assert "random_forest" in ids
    assert "gradient_boosting" in ids

def test_model_registry_regression_models():
    reg_models = ModelRegistry.get_supported_models("regression")
    ids = [m["id"] for m in reg_models]
    
    assert "dummy" in ids
    assert "decision_tree" in ids
    assert "bagging" in ids
    assert "random_forest" in ids
    assert "ridge" in ids
    assert "lasso" in ids
