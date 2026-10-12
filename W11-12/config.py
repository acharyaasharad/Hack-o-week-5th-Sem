"""Configuration module for Dimensionality Reduction Visualizer — PCA & t-SNE Studio.
Manages file paths, upload constraints, algorithm parameters, and dataset defaults.
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
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SAMPLE_DIR, REPORTS_DIR, INSTANCE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

SAMPLE_CSV = DATA_SAMPLE_DIR / "sample_data.csv"
EXPERIMENTS_FILE = INSTANCE_DIR / "experiments.json"

# --------------------------------------------------------------------------
# Server & Security Configuration
# --------------------------------------------------------------------------
APP_NAME = "Dimensionality Reduction Visualizer — PCA & t-SNE Studio"
VERSION = "1.0.0"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5005))
DEBUG = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 20))
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
MAX_DATASET_ROWS = int(os.environ.get("MAX_DATASET_ROWS", 50000))
MAX_TSNE_SAMPLES = int(os.environ.get("MAX_TSNE_SAMPLES", 3000))
RANDOM_STATE = int(os.environ.get("RANDOM_STATE", 42))

# --------------------------------------------------------------------------
# Dataset Attributions
# --------------------------------------------------------------------------
WINE_ATTRIBUTION = (
    "Aeberhard, S. & Forina, M. (1991). Wine Recognition Dataset. "
    "UCI Machine Learning Repository. https://doi.org/10.24432/C5PC7J. Licensed under CC BY 4.0."
)

IRIS_ATTRIBUTION = (
    "Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. "
    "Annual Eugenics, 7, Part II, 179-188."
)
