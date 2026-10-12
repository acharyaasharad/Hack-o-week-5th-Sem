import pytest
from services.generalization_service import GeneralizationService

def test_synthetic_polynomial_demo():
    demo = GeneralizationService.run_synthetic_demo()
    
    assert "x_train" in demo
    assert "models" in demo
    assert len(demo["models"]) == 3
    
    degrees = [m["degree"] for m in demo["models"]]
    assert 1 in degrees
    assert 4 in degrees
    assert 12 in degrees
    
    for m in demo["models"]:
        assert m["train_rmse"] >= 0
        assert m["val_rmse"] >= 0
