"""Data acquisition script for UCI Dataset ID 849: Power Consumption of Tetouan City.
Downloads the raw dataset using ucimlrepo and saves it to data/raw/tetouan_power.csv.
Provides graceful fallbacks if network access is unavailable.
"""

from pathlib import Path
import sys
import logging

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ATTRIBUTION_METADATA = """# UCI Machine Learning Repository: Power Consumption of Tetouan City
# Dataset ID: 849
# Creators: Abdulwahed Salam, Abdellah El Hibaoui, Abdelouahid Lyhyaoui (2018)
# Institution: Abdelmalek Essaadi University, Tetouan, Morocco
# License: Creative Commons Attribution 4.0 International (CC BY 4.0)
# URL: https://archive.ics.uci.edu/dataset/849/power+consumption+of+tetouan+city
# Description: Power consumption readings of Tetouan city distributed across three distribution zones (Zone 1, Zone 2, Zone 3)
# recorded every 10 minutes throughout 2017 with accompanying weather readings.
"""

def download_uci_dataset(force: bool = False) -> bool:
    """Downloads dataset 849 from UCI ML repository or verifies existence."""
    raw_path = config.RAW_DATASET_PATH
    if raw_path.exists() and not force:
        logger.info(f"Raw dataset already exists at {raw_path} ({raw_path.stat().st_size:,} bytes). Skipping download.")
        return True

    logger.info(f"Connecting to UCI Repository for Dataset ID {config.UCI_DATASET_ID} (Power Consumption of Tetouan City)...")

    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=config.UCI_DATASET_ID)
        
        # Extract features and targets into a single DataFrame
        features = dataset.data.features
        targets = dataset.data.targets
        
        import pandas as pd
        if targets is not None and not targets.empty:
            df = pd.concat([features, targets], axis=1)
        else:
            df = features

        # Standardize column naming if needed
        # Typical Tetouan columns: DateTime, Temperature, Humidity, WindSpeed, GeneralDiffuseFlows, DiffuseFlows, Zone1Power, Zone2Power, Zone3Power
        # Ensure column names match expected casing
        rename_map = {}
        for col in df.columns:
            cleaned = col.replace(" ", "").replace("_", "").replace("-", "")
            if cleaned.lower() == "datetime":
                rename_map[col] = "DateTime"
            elif cleaned.lower() == "temperature":
                rename_map[col] = "Temperature"
            elif cleaned.lower() == "humidity":
                rename_map[col] = "Humidity"
            elif cleaned.lower() == "windspeed":
                rename_map[col] = "WindSpeed"
            elif cleaned.lower() == "generaldiffuseflows":
                rename_map[col] = "GeneralDiffuseFlows"
            elif cleaned.lower() == "diffuseflows":
                rename_map[col] = "DiffuseFlows"
            elif "zone1" in cleaned.lower():
                rename_map[col] = "Zone1Power"
            elif "zone2" in cleaned.lower():
                rename_map[col] = "Zone2Power"
            elif "zone3" in cleaned.lower():
                rename_map[col] = "Zone3Power"
        
        df = df.rename(columns=rename_map)

        # Save to data/raw/
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_path, index=False)
        
        # Save attribution notes
        meta_path = raw_path.parent / "ATTRIBUTION.txt"
        meta_path.write_text(ATTRIBUTION_METADATA)

        logger.info(f"Successfully downloaded UCI Dataset 849: {len(df):,} rows, {len(df.columns)} columns saved to {raw_path}")
        return True

    except Exception as exc:
        logger.warning(f"Could not download UCI dataset over network: {exc}")
        logger.info("The application will fallback to the bundled data/sample/sample_energy.csv.")
        return False


if __name__ == "__main__":
    force_download = "--force" in sys.argv
    success = download_uci_dataset(force=force_download)
    sys.exit(0 if success else 1)
