import pytest
import pandas as pd
import numpy as np
from services.profiling_service import ProfilingService

def test_profiling_and_original_units():
    df = pd.DataFrame({
        "Fresh": [10000, 20000, 3000, 4000],
        "Milk": [5000, 6000, 1000, 2000],
        "Channel": [1, 2, 1, 2],
    })
    labels = np.array([0, 0, 1, 1])
    profiles = ProfilingService.generate_cluster_profiles(
        df=df,
        labels=labels,
        numeric_features=["Fresh", "Milk"],
        context_columns=["Channel"],
    )
    assert profiles["total_customers"] == 4
    c0 = profiles["clusters"]["Cluster 0"]
    assert c0["customer_count"] == 2
    assert c0["means"]["Fresh"] == 15000.0  # Exact arithmetic mean in original units
    assert c0["means"]["Milk"] == 5500.0
    assert "derived_description" in c0
    assert len(c0["suggested_actions"]) > 0
