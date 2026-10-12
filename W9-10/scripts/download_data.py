"""Download script for UCI Wholesale Customers Dataset (ID: 292).
Fetches features and targets via ucimlrepo or fallback, and saves raw CSV to data/raw/.
Attribution:
Cardoso, M. (2013). Wholesale customers. UCI Machine Learning Repository.
https://doi.org/10.24432/C5030X. Licensed under CC BY 4.0.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

UCI_DATASET_ID = 292
DIRECT_URL = "https://archive.ics.uci.edu/static/public/292/wholesale+customers.zip"
FALLBACK_CSV_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/wholesale-customers-data.csv"

def download_uci_dataset() -> bool:
    """Attempts downloading via ucimlrepo first, then fallback requests."""
    config.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = config.UCI_RAW_CSV
    
    logger.info("Attempting to fetch dataset ID %d from ucimlrepo...", UCI_DATASET_ID)
    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=UCI_DATASET_ID)
        
        # Combine features and targets by row index
        X = dataset.data.features
        y = dataset.data.targets
        
        if y is not None and not y.empty:
            df = pd.concat([X, y], axis=1)
        else:
            df = X.copy()
            
        logger.info("Retrieved %d rows and %d columns via ucimlrepo.", len(df), len(df.columns))
        df.to_csv(raw_path, index=False)
        logger.info("Successfully saved UCI raw dataset to %s", raw_path)
        return True
    except Exception as e:
        logger.warning("ucimlrepo fetch failed (%s). Attempting fallback download...", e)

    try:
        import requests
        import io
        import zipfile
        
        # Try direct zip download from UCI
        r = requests.get(DIRECT_URL, timeout=15)
        if r.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                # Look for csv
                for filename in z.namelist():
                    if filename.endswith(".csv"):
                        with z.open(filename) as f:
                            df = pd.read_csv(f)
                            df.to_csv(raw_path, index=False)
                            logger.info("Successfully extracted and saved UCI dataset from zip: %d rows", len(df))
                            return True
    except Exception as e:
        logger.warning("UCI zip download failed: %s", e)

    try:
        import requests
        logger.info("Attempting fallback mirror download...")
        r = requests.get(FALLBACK_CSV_URL, timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            df.to_csv(raw_path, index=False)
            logger.info("Successfully fetched dataset from mirror: %d rows", len(df))
            return True
    except Exception as e:
        logger.error("All remote download attempts failed: %s", e)
        return False

    return False

if __name__ == "__main__":
    success = download_uci_dataset()
    if not success:
        logger.warning("Could not download remote dataset. Run prepare_data.py to ensure synthetic fallback is ready.")
        sys.exit(1)
    else:
        logger.info("Dataset download completed successfully.")
