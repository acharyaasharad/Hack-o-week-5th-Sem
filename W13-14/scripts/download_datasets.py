"""Download script for UCI Bank Marketing (ID 222) and Bike Sharing (ID 275) datasets.
Uses ucimlrepo or fallback to save raw CSVs in data/raw/.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def download_datasets():
    config.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Bank Marketing (ID 222)
    bank_path = config.DATA_RAW_DIR / "bank_marketing_raw.csv"
    logger.info("Attempting to fetch UCI Bank Marketing (ID 222)...")
    try:
        from ucimlrepo import fetch_ucirepo
        bank = fetch_ucirepo(id=222)
        X = bank.data.features
        y = bank.data.targets
        df = pd.concat([X, y], axis=1) if y is not None and not y.empty else X.copy()
        df.to_csv(bank_path, index=False)
        logger.info("Successfully saved Bank Marketing dataset: %d rows", len(df))
    except Exception as e:
        logger.warning("Bank marketing ucimlrepo fetch failed: %s. Using sample fallback.", e)

    # 2. Bike Sharing (ID 275)
    bike_path = config.DATA_RAW_DIR / "bike_sharing_raw.csv"
    logger.info("Attempting to fetch UCI Bike Sharing (ID 275)...")
    try:
        from ucimlrepo import fetch_ucirepo
        bike = fetch_ucirepo(id=275)
        X = bike.data.features
        y = bike.data.targets
        df = pd.concat([X, y], axis=1) if y is not None and not y.empty else X.copy()
        df.to_csv(bike_path, index=False)
        logger.info("Successfully saved Bike Sharing dataset: %d rows", len(df))
    except Exception as e:
        logger.warning("Bike sharing ucimlrepo fetch failed: %s. Using sample fallback.", e)

if __name__ == "__main__":
    download_datasets()
