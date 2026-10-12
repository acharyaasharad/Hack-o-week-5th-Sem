"""Prepare sample data script.
Ensures that data/sample/sample_customers.csv is generated deterministically
with a fixed random seed and clearly labeled as synthetic demonstration data,
allowing the dashboard to function fully offline.
"""

import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def generate_sample_dataset(n_samples: int = 440, seed: int = 42) -> pd.DataFrame:
    """Generates synthetic wholesale customer data with realistic lognormal distributions
    mimicking the UCI Wholesale Customers dataset.
    Clearly labeled as synthetic demonstration data.
    """
    np.random.seed(seed)
    
    # 3 latent customer archetypes to produce realistic clusters:
    # 1. Retailers / Groceries: High Milk, Grocery, Detergents_Paper
    # 2. HoReCa (Hotel/Restaurant/Cafe): High Fresh, Frozen, Delicassen
    # 3. Small general buyers: Moderate across all categories
    
    n1 = int(n_samples * 0.35)
    n2 = int(n_samples * 0.35)
    n3 = n_samples - n1 - n2
    
    # Archetype 1: Retail / Supermarket
    fresh_1 = np.random.lognormal(mean=8.2, sigma=0.8, size=n1)
    milk_1 = np.random.lognormal(mean=9.3, sigma=0.7, size=n1)
    grocery_1 = np.random.lognormal(mean=9.8, sigma=0.6, size=n1)
    frozen_1 = np.random.lognormal(mean=7.0, sigma=0.8, size=n1)
    detergents_1 = np.random.lognormal(mean=9.1, sigma=0.7, size=n1)
    delicassen_1 = np.random.lognormal(mean=7.2, sigma=0.8, size=n1)
    channel_1 = np.random.choice([1, 2], p=[0.2, 0.8], size=n1)  # Mostly Channel 2 (Retail)
    region_1 = np.random.choice([1, 2, 3], p=[0.15, 0.1, 0.75], size=n1)
    
    # Archetype 2: HoReCa (Restaurants, Cafes)
    fresh_2 = np.random.lognormal(mean=9.8, sigma=0.7, size=n2)
    milk_2 = np.random.lognormal(mean=7.8, sigma=0.8, size=n2)
    grocery_2 = np.random.lognormal(mean=7.6, sigma=0.7, size=n2)
    frozen_2 = np.random.lognormal(mean=8.8, sigma=0.8, size=n2)
    detergents_2 = np.random.lognormal(mean=6.5, sigma=0.9, size=n2)
    delicassen_2 = np.random.lognormal(mean=7.9, sigma=0.8, size=n2)
    channel_2 = np.random.choice([1, 2], p=[0.85, 0.15], size=n2)  # Mostly Channel 1 (Horeca)
    region_2 = np.random.choice([1, 2, 3], p=[0.2, 0.1, 0.7], size=n2)
    
    # Archetype 3: Small/Boutique/Mixed
    fresh_3 = np.random.lognormal(mean=7.9, sigma=0.7, size=n3)
    milk_3 = np.random.lognormal(mean=7.3, sigma=0.7, size=n3)
    grocery_3 = np.random.lognormal(mean=7.4, sigma=0.7, size=n3)
    frozen_3 = np.random.lognormal(mean=7.1, sigma=0.7, size=n3)
    detergents_3 = np.random.lognormal(mean=6.8, sigma=0.7, size=n3)
    delicassen_3 = np.random.lognormal(mean=6.5, sigma=0.7, size=n3)
    channel_3 = np.random.choice([1, 2], p=[0.6, 0.4], size=n3)
    region_3 = np.random.choice([1, 2, 3], p=[0.18, 0.12, 0.7], size=n3)
    
    df = pd.DataFrame({
        "Channel": np.concatenate([channel_1, channel_2, channel_3]),
        "Region": np.concatenate([region_1, region_2, region_3]),
        "Fresh": np.round(np.concatenate([fresh_1, fresh_2, fresh_3])).astype(int),
        "Milk": np.round(np.concatenate([milk_1, milk_2, milk_3])).astype(int),
        "Grocery": np.round(np.concatenate([grocery_1, grocery_2, grocery_3])).astype(int),
        "Frozen": np.round(np.concatenate([frozen_1, frozen_2, frozen_3])).astype(int),
        "Detergents_Paper": np.round(np.concatenate([detergents_1, detergents_2, detergents_3])).astype(int),
        "Delicassen": np.round(np.concatenate([delicassen_1, delicassen_2, delicassen_3])).astype(int),
    })
    
    # Shuffle dataframe with fixed random state
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df

def prepare_sample_data():
    """Saves sample dataset to data/sample/sample_customers.csv."""
    config.DATA_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    sample_file = config.SAMPLE_CSV
    
    # If raw exists, we can also ensure sample exists
    df_sample = generate_sample_dataset(n_samples=440, seed=42)
    df_sample.to_csv(sample_file, index=False)
    logger.info("Generated deterministic synthetic sample data at %s (%d rows)", sample_file, len(df_sample))

if __name__ == "__main__":
    prepare_sample_data()
