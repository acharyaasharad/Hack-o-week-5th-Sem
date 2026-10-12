"""Configuration module for Customer Segmentation & Intelligence Dashboard.
Manages filesystem paths, upload constraints, model hyperparameters, and defaults.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load optional .env
load_dotenv()

# --------------------------------------------------------------------------
# Filesystem Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SAMPLE_DIR = DATA_DIR / "sample"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
INSTANCE_DIR = BASE_DIR / "instance"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure runtime directories exist
for directory in [
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_SAMPLE_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    INSTANCE_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# File Paths
UCI_RAW_CSV = DATA_RAW_DIR / "wholesale_customers_raw.csv"
SAMPLE_CSV = DATA_SAMPLE_DIR / "sample_customers.csv"
EXPERIMENTS_FILE = INSTANCE_DIR / "experiments_history.json"

# --------------------------------------------------------------------------
# Server & Security Configuration
# --------------------------------------------------------------------------
APP_NAME = "Customer Segmentation & Intelligence Dashboard"
VERSION = "1.0.0"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5004))
DEBUG = os.environ.get("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 20))
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv"}
MAX_DENDROGRAM_ROWS = 1000  # Avoid quadratic memory blowout in browser/scipy
MAX_PREVIEW_ROWS = 100

# --------------------------------------------------------------------------
# Machine Learning Defaults & Safeguards
# --------------------------------------------------------------------------
RANDOM_STATE = int(os.environ.get("RANDOM_STATE", 42))

DEFAULT_FEATURE_COLUMNS = [
    "Fresh",
    "Milk",
    "Grocery",
    "Frozen",
    "Detergents_Paper",
    "Delicassen",
]

DEFAULT_CONTEXT_COLUMNS = ["Channel", "Region"]

# Dataset citation attribution
UCI_ATTRIBUTION = (
    "Cardoso, M. (2013). Wholesale customers. UCI Machine Learning Repository. "
    "https://doi.org/10.24432/C5030X. Licensed under CC BY 4.0."
)

# Supported Algorithms & Parameter bounds
SUPPORTED_ALGORITHMS = {
    "kmeans": {
        "name": "K-Means",
        "description": "Partitioning algorithm that minimizes within-cluster sum of squares (inertia).",
        "default_params": {
            "n_clusters": 4,
            "init": "k-means++",
            "n_init": 10,
            "max_iter": 300,
            "random_state": RANDOM_STATE,
        },
    },
    "hierarchical": {
        "name": "Hierarchical (Agglomerative) Clustering",
        "description": "Bottom-up hierarchical clustering that recursively merges pairs of clusters based on distance linkage.",
        "default_params": {
            "n_clusters": 4,
            "linkage": "ward",
            "metric": "euclidean",
        },
    },
    "dbscan": {
        "name": "DBSCAN (Density-Based Spatial Clustering)",
        "description": "Density-based algorithm grouping core points closely packed together and marking outliers as noise (-1).",
        "default_params": {
            "eps": 0.7,
            "min_samples": 5,
            "metric": "euclidean",
        },
    },
}
