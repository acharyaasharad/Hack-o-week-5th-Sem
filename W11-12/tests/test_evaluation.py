import pytest
import numpy as np
from services.evaluation_service import EvaluationService

def test_trustworthiness_calculation():
    X_high = np.array([
        [1.0, 2.0, 3.0], [1.1, 2.1, 3.1], [1.2, 2.2, 3.2],
        [8.0, 8.0, 8.0], [8.1, 8.1, 8.1], [8.2, 8.2, 8.2],
        [15.0, 15.0, 15.0], [15.1, 15.1, 15.1], [15.2, 15.2, 15.2],
        [20.0, 20.0, 20.0], [20.1, 20.1, 20.1], [20.2, 20.2, 20.2],
    ])
    X_low = X_high[:, :2] # 2D slice
    score = EvaluationService.compute_trustworthiness(X_high, X_low, n_neighbors=3)
    assert score is not None
    assert score > 0.8

def test_reconstruction_error():
    orig = np.array([[1.0, 2.0], [3.0, 4.0]])
    recon = np.array([[1.1, 2.0], [2.9, 4.0]])
    err = EvaluationService.compute_reconstruction_error(orig, recon)
    assert err > 0
