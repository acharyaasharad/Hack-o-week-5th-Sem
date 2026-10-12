"""Generates a synthetic high-dimensional sample dataset for offline demonstration.
Clearly labeled as synthetic demonstration data.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

def generate_sample_data(n_samples: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic multi-cluster 8-feature data with clear class separation."""
    np.random.seed(seed)
    
    n_per_class = n_samples // 3
    n_rem = n_samples - (2 * n_per_class)
    
    # Class A
    A = np.random.normal(loc=[10, 5, 20, 1.5, 50, 12, 0.8, 100], scale=[1.5, 0.8, 2.5, 0.3, 5.0, 1.2, 0.1, 8.0], size=(n_per_class, 8))
    # Class B
    B = np.random.normal(loc=[14, 2, 10, 3.0, 30, 8, 1.6, 50], scale=[1.2, 0.5, 1.8, 0.4, 4.0, 0.9, 0.15, 5.0], size=(n_per_class, 8))
    # Class C
    C = np.random.normal(loc=[12, 8, 30, 2.2, 70, 15, 1.2, 120], scale=[1.4, 0.9, 3.0, 0.35, 6.0, 1.5, 0.12, 9.0], size=(n_rem, 8))
    
    X = np.vstack([A, B, C])
    labels = ["Cluster_Alpha"] * n_per_class + ["Cluster_Beta"] * n_per_class + ["Cluster_Gamma"] * n_rem
    
    feature_cols = [
        "Feature_1_Density",
        "Feature_2_Acidity",
        "Feature_3_Viscosity",
        "Feature_4_Intensity",
        "Feature_5_Conductivity",
        "Feature_6_Absorbance",
        "Feature_7_Refraction",
        "Feature_8_Luminance",
    ]
    
    df = pd.DataFrame(np.round(X, 3), columns=feature_cols)
    df["Synthetic_Class"] = labels
    
    # Shuffle deterministically
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df

def save_sample_data():
    config.DATA_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_sample_data()
    df.to_csv(config.SAMPLE_CSV, index=False)
    print(f"Generated synthetic sample data at {config.SAMPLE_CSV} ({len(df)} rows)")

if __name__ == "__main__":
    save_sample_data()
