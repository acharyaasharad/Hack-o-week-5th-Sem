"""Configuration module for Energy Demand Forecasting & Optimization.
Manages file paths, model configurations, API defaults, and optimization parameters.
"""

from pathlib import Path
import os

# --------------------------------------------------------------------------
# File System Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SAMPLE_DIR = DATA_DIR / "sample"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
INSTANCE_DIR = BASE_DIR / "instance"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

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

# --------------------------------------------------------------------------
# Default Datasets
# --------------------------------------------------------------------------
UCI_DATASET_ID = 849
RAW_TETOUAN_FILENAME = "tetouan_power.csv"
SAMPLE_DATASET_FILENAME = "sample_energy.csv"
SAMPLE_DATASET_PATH = DATA_SAMPLE_DIR / SAMPLE_DATASET_FILENAME
RAW_DATASET_PATH = DATA_RAW_DIR / RAW_TETOUAN_FILENAME
PROCESSED_DATASET_PATH = DATA_PROCESSED_DIR / "tetouan_hourly.csv"

# --------------------------------------------------------------------------
# Server & Upload Constraints
# --------------------------------------------------------------------------
PORT = int(os.environ.get("PORT", 5003))
HOST = os.environ.get("HOST", "127.0.0.1")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.environ.get("SECRET_KEY", "energy-demand-optimizer-secret-key-2026")
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB max file upload
ALLOWED_EXTENSIONS = {".csv"}

# --------------------------------------------------------------------------
# Default Tetouan Location & Weather API
# --------------------------------------------------------------------------
DEFAULT_LATITUDE = 35.5889
DEFAULT_LONGITUDE = -5.3626
DEFAULT_TIMEZONE = "Africa/Casablanca"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE_TTL_SECONDS = 3600  # 1 hour in-memory cache

# --------------------------------------------------------------------------
# Machine Learning & Feature Engineering
# --------------------------------------------------------------------------
DEFAULT_TARGET_COLUMN = "Zone1Power"
DEFAULT_TIMESTAMP_COLUMN = "DateTime"
DEFAULT_WEATHER_COLUMNS = ["Temperature", "Humidity", "WindSpeed"]
AVAILABLE_TARGET_COLUMNS = ["Zone1Power", "Zone2Power", "Zone3Power"]

DEFAULT_FORECAST_HORIZON = 24  # 24-hour ahead recursive forecasting
DEFAULT_LAGS = [1, 2, 24, 48, 168]  # 1h, 2h, 1d, 2d, 1w
DEFAULT_ROLLING_WINDOWS = [6, 24]  # 6-hour and 24-hour rolling averages

# Train / Validation / Test Chronological Splits
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Supported Models
SUPPORTED_MODELS = {
    "seasonal_naive": "Seasonal Naive (24h Baseline)",
    "ridge": "Ridge Regression",
    "random_forest": "Random Forest Regressor",
    "hist_gradient_boosting": "HistGradientBoosting Regressor",
}

# --------------------------------------------------------------------------
# Load Shifting & Optimization Engine Defaults
# --------------------------------------------------------------------------
# Default hourly Time-Of-Use (TOU) tariff in $/kWh or MAD/kWh
# Off-peak (00-06): 0.08, Mid-peak (07-16, 22-23): 0.14, On-peak (17-21): 0.28
DEFAULT_TOU_TARIFF = [
    0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08,  # 00:00 - 06:00
    0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14,  # 07:00 - 13:00
    0.14, 0.14, 0.14,                          # 14:00 - 16:00
    0.28, 0.28, 0.28, 0.28, 0.28,              # 17:00 - 21:00
    0.14, 0.14                                 # 22:00 - 23:00
]

OPTIMIZATION_DEFAULTS = {
    "required_energy": 60.0,      # kWh of flexible demand required
    "max_power": 12.0,            # Max kW deliverable per hour
    "start_hour": 0,              # Window start
    "end_hour": 23,               # Window end
    "unavailable_hours": [18, 19, 20],  # Example peak hours where load cannot be scheduled
    "peak_penalty_weight": 0.5,   # Weight for maximum demand in balanced objective
    "demand_unit": "kW",
    "energy_unit": "kWh",
    "currency_symbol": "$",
}

# --------------------------------------------------------------------------
# Visual Palette Tokens (Light Theme + Dark Charcoal Sidebar + Emerald Accents)
# STRICTLY NO PURPLE GRADIENTS
# --------------------------------------------------------------------------
THEME = {
    "sidebar_bg": "#0f172a",       # Slate 900
    "sidebar_surface": "#1e293b",  # Slate 800
    "workspace_bg": "#f8fafc",     # Slate 50
    "card_bg": "#ffffff",          # Pure white
    "border": "#e2e8f0",           # Slate 200
    "text_primary": "#0f172a",     # Slate 900
    "text_secondary": "#475569",   # Slate 600
    "accent_primary": "#0d9488",   # Teal 600
    "accent_hover": "#0f766e",     # Teal 700
    "accent_secondary": "#059669", # Emerald 600
    "accent_highlight": "#0284c7", # Sky 600
    "warning": "#d97706",          # Amber 600
    "danger": "#e11d48",           # Rose 600
}
