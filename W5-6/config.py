"""Configuration module for Touchline Analytics — Football Analytics & Player Comparison Lab.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
CHARTS_DIR = STATIC_DIR / "charts"
UPLOADS_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

PLAYERS_CSV = DATA_DIR / "players.csv"
MATCHES_CSV = DATA_DIR / "matches.csv"

# Upload and Security Configuration
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {"csv"}

# Application Settings
APP_NAME = "Touchline Analytics"
VERSION = "1.0.0"
DEFAULT_PORT = int(os.environ.get("PORT", 5002))
DEBUG = False

# Supported Positions & Leagues
SUPPORTED_POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
SUPPORTED_LEAGUES = ["Premier League", "La Liga"]
SUPPORTED_SEASONS = ["2023-2024", "2024-2025"]

# Minimum thresholds
MIN_MINUTES_THRESHOLD = 90
DEFAULT_PAGE_SIZE = 15
MAX_PAGE_SIZE = 100

# Theme Palette (Clean White UI + Pitch Emerald, Cyan, Lime & Amber Accents, NO Purple Gradient)
THEME = {
    "bg": "#ffffff",              # Clean White
    "card_bg": "#f8fafc",         # Slate 50
    "surface": "#f1f5f9",         # Slate 100
    "accent_emerald": "#059669",  # Pitch Emerald Green
    "accent_lime": "#65a30d",     # Pitch Lime
    "accent_cyan": "#0284c7",     # Pitch Blue/Cyan
    "accent_amber": "#d97706",    # Pitch Amber
    "accent_rose": "#e11d48",     # Pitch Rose
    "text": "#0f172a",            # Slate 900
    "text_muted": "#64748b",      # Slate 500
    "grid": "#e2e8f0",            # Slate 200
    "border": "#cbd5e1",          # Slate 300
}
