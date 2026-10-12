"""Generates deterministic synthetic demonstration datasets for classification and regression.
Allows the application to run completely offline without downloading external sources.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

def generate_sample_classification(n_samples: int = 400, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic client loan qualification dataset (Binary Classification)."""
    np.random.seed(seed)
    
    age = np.random.randint(20, 65, size=n_samples)
    balance = np.random.normal(loc=1500, scale=800, size=n_samples).round(2)
    job = np.random.choice(["admin", "technician", "services", "management", "blue-collar"], size=n_samples)
    marital = np.random.choice(["married", "single", "divorced"], size=n_samples)
    education = np.random.choice(["primary", "secondary", "tertiary"], size=n_samples)
    campaign = np.random.randint(1, 6, size=n_samples)
    pdays = np.random.choice([-1, 99, 180, 250], size=n_samples)
    
    # Non-linear probability of subscription
    log_odds = (
        0.03 * (age - 35)
        + 0.0008 * (balance - 1000)
        - 0.25 * campaign
        + (1.0 if pdays.any() and pdays[0] > 0 else 0.0)
        + np.random.normal(0, 0.8, size=n_samples)
    )
    prob = 1 / (1 + np.exp(-log_odds))
    y = np.where(prob > 0.5, "yes", "no")
    
    df = pd.DataFrame({
        "age": age,
        "job": job,
        "marital": marital,
        "education": education,
        "balance": balance,
        "campaign": campaign,
        "pdays": pdays,
        "deposit_subscribed": y,
    })
    return df

def generate_sample_regression(n_samples: int = 400, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic hourly rental demand dataset (Regression)."""
    np.random.seed(seed)
    
    temp = np.random.uniform(0.1, 0.9, size=n_samples).round(3)
    humidity = np.random.uniform(0.2, 0.9, size=n_samples).round(3)
    windspeed = np.random.uniform(0.05, 0.6, size=n_samples).round(3)
    season = np.random.choice(["Spring", "Summer", "Fall", "Winter"], size=n_samples)
    workingday = np.random.choice([0, 1], size=n_samples)
    hour = np.random.randint(0, 24, size=n_samples)
    
    # Non-linear continuous demand
    peak_hour_effect = np.exp(-((hour - 17) ** 2) / 12) * 250 + np.exp(-((hour - 8) ** 2) / 8) * 180
    base_demand = (
        40
        + 300 * temp
        - 120 * humidity
        - 60 * windspeed
        + peak_hour_effect
        + np.random.normal(0, 25, size=n_samples)
    )
    rentals = np.maximum(5, base_demand.round()).astype(int)
    
    df = pd.DataFrame({
        "hour": hour,
        "season": season,
        "workingday": workingday,
        "temp": temp,
        "humidity": humidity,
        "windspeed": windspeed,
        "rental_count": rentals,
    })
    return df

def generate_all_samples():
    config.DATA_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    
    df_cls = generate_sample_classification()
    df_cls.to_csv(config.SAMPLE_CLASSIFICATION_CSV, index=False)
    print(f"Generated sample classification data: {config.SAMPLE_CLASSIFICATION_CSV} ({len(df_cls)} rows)")
    
    df_reg = generate_sample_regression()
    df_reg.to_csv(config.SAMPLE_REGRESSION_CSV, index=False)
    print(f"Generated sample regression data: {config.SAMPLE_REGRESSION_CSV} ({len(df_reg)} rows)")

if __name__ == "__main__":
    generate_all_samples()
