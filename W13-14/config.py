"""Configuration module for Ensemble Learning & Generalization Lab.
Manages dataset paths, parameter bounds, upload limits, and attributions.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Filesystem Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SAMPLE_DIR = DATA_DIR / "sample"
REPORTS_DIR = BASE_DIR / "reports"
INSTANCE_DIR = BASE_DIR / "instance"
MODELS_DIR = BASE_DIR / "models"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SAMPLE_DIR, REPORTS_DIR, INSTANCE_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SAMPLE_CLASSIFICATION_CSV = DATA_SAMPLE_DIR / "sample_classification.csv"
SAMPLE_REGRESSION_CSV = DATA_SAMPLE_DIR / "sample_regression.csv"
EXPERIMENTS_FILE = INSTANCE_DIR / "experiments.json"

# --------------------------------------------------------------------------
# Server & Security Configuration
# --------------------------------------------------------------------------
APP_NAME = "Ensemble Learning & Generalization Lab"
VERSION = "1.0.0"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5006))
DEBUG = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 20))
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
MAX_DATASET_ROWS = int(os.environ.get("MAX_DATASET_ROWS", 50000))
MAX_PARAMETER_SWEEP_RUNS = int(os.environ.get("MAX_PARAMETER_SWEEP_RUNS", 30))
RANDOM_STATE = int(os.environ.get("RANDOM_STATE", 42))

# --------------------------------------------------------------------------
# Dataset Attributions
# --------------------------------------------------------------------------
BANK_ATTRIBUTION = (
    "Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing. "
    "UCI Machine Learning Repository. https://doi.org/10.24432/C5K306. Licensed under CC BY 4.0."
)

BIKE_ATTRIBUTION = (
    "Fanaee-T, H. (2013). Bike Sharing. "
    "UCI Machine Learning Repository. https://doi.org/10.24432/C5W894. Licensed under CC BY 4.0."
)
