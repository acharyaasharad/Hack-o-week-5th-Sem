# Touchline Analytics — Football Analytics & Player Comparison Lab

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-darkblue.svg)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-orange.svg)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8%2B-teal.svg)](https://matplotlib.org/)
[![Seaborn](https://img.shields.io/badge/Seaborn-0.13%2B-emerald.svg)](https://seaborn.pydata.org/)

**Touchline Analytics** is an end-to-end, data-driven football analytics laboratory and player comparison platform. Built using Python, Flask, Pandas, NumPy, Matplotlib, Seaborn, and modern vanilla HTML5/CSS3/JavaScript (with Chart.js), it provides exploratory football data analysis, per-90 metrics normalization, multi-player radar benchmarking, tactical correlation modeling, and pipeline data quality auditing.

---

## Table of Contents
1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Key Features](#key-features)
3. [Interface Sections & Screens](#interface-sections--screens)
4. [Technology Stack](#technology-stack)
5. [Project Architecture & Structure](#project-architecture--structure)
6. [Dataset Schemas & Synthetic Data Design](#dataset-schemas--synthetic-data-design)
7. [Football Analytics & Mathematical Formulas](#football-analytics--mathematical-formulas)
8. [Pandas & NumPy Implementation](#pandas--numpy-implementation)
9. [Matplotlib & Seaborn Visualizations](#matplotlib--seaborn-visualizations)
10. [REST API Documentation](#rest-api-documentation)
11. [Installation & Setup (macOS / Local)](#installation--setup-macos--local)
12. [Running the Application](#running-the-application)
13. [Running Automated Tests](#running-automated-tests)
14. [Troubleshooting & Common Issues](#troubleshooting--common-issues)
15. [Responsible Interpretation of Football Statistics](#responsible-interpretation-of-football-statistics)
16. [Limitations & Future Enhancements](#limitations--future-enhancements)

---

## Project Overview & Problem Statement

### Problem Statement
In modern football analysis, raw counting metrics (such as raw goal totals or tackle counts) often mislead analysts and fans because they fail to account for differing playing time, tactical roles, competition strength, or team possession styles. Furthermore, plotting variables with wildly differing scales (e.g. Pass Completion % alongside Goals per 90) on radar graphics distorts comparisons without proper mathematical normalization.

### Project Objective
Touchline Analytics provides an accessible, fully reproducible football analytics workbench that:
- Normalizes tactical statistics on a **per-90 minute basis** with zero-minute guards.
- Implements **Min-Max percentile scaling** for multi-player radar comparisons (2–4 players).
- Evaluates descriptive metrics such as **xG Overperformance** (`Goals - xG`) and **Defensive Actions per 90**.
- Audits dataset hygiene and referential integrity in real time.
- Operates 100% offline without paid API subscriptions or third-party tracking services.

---

## Key Features

1. **Live Dashboard Overview**:
   - 6 KPI cards: Total Players, Total Clubs, Competitions, Total Goals, Average Rating, and Total Matches.
   - Interactive Chart.js charts: Goals & Assists by Position, Player Rating Distribution, Goals Across Match Dates, and League Scoring Comparison.
   - Top Performers leaderboard ranked by goal output and performance rating subject to a 450-minute threshold.

2. **Player Explorer**:
   - Comprehensive multi-filter toolbar: debounced search (300ms), League, Club, Position, Season, Age bounds, Minimum Minutes slider, Minimum Rating slider, and Ascending/Descending sort controls.
   - Server-side pagination and responsive table view.
   - One-click modal profile inspection with avatar initials, attacking, passing, and defending metrics.

3. **Multi-Player Comparison Lab (2–4 Players)**:
   - Searchable player picker with chip management.
   - **Normalized Metric Radar Chart** plotting Goals/90, Assists/90, xG/90, xA/90, Key Passes/90, Defensive Actions/90, and Pass Completion % on a 0–100 scale.
   - Grouped Bar Chart comparing Goals & Assists.
   - Side-by-side metric table with individual row leaders highlighted.
   - Deterministic, factual statistical verdict highlighting category leaders and sample size warnings.

4. **Performance Analytics Lab**:
   - Positional Analysis: Tactical output and efficiency by Goalkeeper, Defender, Midfielder, and Forward.
   - Age Profile vs. Performance: Interactive scatter curve with dynamic y-metric selector.
   - Club Squad Aggregates: Total goals, shots, xG, and average rating by club.
   - Tactical Metric Correlation Heatmap: Server-side Seaborn correlation matrix highlighting associations across continuous numeric metrics.

5. **Match Insights**:
   - Home vs. Away win ratios and draw distributions.
   - Chronological fixture table with scorelines and standard football result classifications.

6. **Data Quality & Audit Pipeline**:
   - Complete data quality summary calculating row retention, duplicate records, and constraint checks.
   - Exportable data quality audit report (TXT format).

7. **Dataset Upload & Reset**:
   - Secure CSV file validation for custom player and match data (max 10MB, column header checks, constraint enforcement).
   - Instant restore button to revert to the bundled verified demo dataset.

---

## Interface Sections & Screens

- **Overview (`#overview`)**: Executive summary, 6 primary KPIs, 4 interactive Chart.js charts, top performers table.
- **Player Explorer (`#players`)**: Search and multi-filter discovery table with pagination and player detail modals.
- **Compare Players (`#compare`)**: Multi-player selection (2–4 players), normalized radar chart, comparison table, and statistical verdict.
- **Performance Lab (`#analytics`)**: Positional benchmarks, age curves, club output tables, and Seaborn correlation matrix.
- **Match Insights (`#matches`)**: Match KPIs, fixture listings, and home/away breakdown.
- **Data Quality (`#quality`)**: Pipeline integrity metrics and error auditing.
- **Dataset Upload (`#upload`)**: Ingestion interface for user-supplied CSV files.
- **About Project (`#about`)**: Data science documentation, mathematical formulas, and technology attribution.

---

## Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Backend** | Python 3.11+ | Core programming language, OOP service design |
| **Framework** | Flask 3.0+ | REST API routing, JSON serialization, and CSV/PNG file streaming |
| **Data Wrangling**| Pandas 2.0+ | Tabular data cleaning, grouping, aggregation, and filtering |
| **Mathematics** | NumPy 1.24+ | Vectorized per-90 operations, array broadcasting, and min-max scaling |
| **Visualization**| Matplotlib 3.8+ & Seaborn 0.13+ | Server-side headless (`Agg`) figure rendering |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Responsive Single Page Application (SPA) with custom dark pitch theme |
| **Client Charts** | Chart.js 4.4 | Browser-rendered interactive radar, bar, line, and histogram charts |

---

## Project Architecture & Structure

```text
W5-6/
├── app.py                     # Flask application routes, REST API, error handlers
├── config.py                  # Central configuration, file paths, thresholds, and color tokens
├── requirements.txt           # Python dependency specifications
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Version control exclusions
│
├── data/
│   ├── players.csv            # 140 synthetic player records across 16 clubs
│   ├── matches.csv            # 160 synthetic fixture records across 2 leagues
│   └── README.md              # Dataset schemas and synthetic data notice
│
├── services/
│   ├── __init__.py            # Services package initializer
│   ├── data_manager.py        # ETL, CSV parsing, data cleansing, quality auditing
│   ├── analytics_engine.py    # KPIs, aggregations, distributions, and player filtering
│   ├── comparison_engine.py   # Multi-player comparisons, radar normalization, verdicts
│   ├── insights_engine.py     # Deterministic analytical observations from live data
│   └── chart_service.py       # Headless Matplotlib and Seaborn PNG generation
│
├── utils/
│   ├── __init__.py            # Utilities package initializer
│   ├── metrics.py             # Pure football formulas and NumPy vectorization
│   ├── validators.py          # CSV schemas, column checks, and query parameter sanitization
│   └── formatters.py          # Number formatting, avatar initials, and position styling
│
├── templates/
│   └── index.html             # Complete single-page application interface
│
├── static/
│   ├── css/
│   │   └── style.css          # Dark pitch theme (charcoal, emerald, lime), responsive layout
│   ├── js/
│   │   └── script.js          # SPA navigation, Fetch API, Chart.js instances, modal controls
│   └── charts/
│       └── .gitkeep           # Storage directory for server-generated chart PNGs
│
├── tests/
│   ├── __init__.py            # Test package initializer
│   ├── test_data_manager.py   # Unit tests for DataManager ingestion and constraints
│   ├── test_analytics_engine.py# Unit tests for analytics aggregations and KPIs
│   ├── test_comparison_engine.py# Unit tests for comparison bounds and radar scaling
│   └── test_api.py            # Integration tests for Flask REST endpoints
│
├── uploads/
│   └── .gitkeep               # Directory for user-uploaded custom CSVs
│
└── scripts/
    └── generate_sample_data.py # Deterministic synthetic dataset generator
```

---

## Dataset Schemas & Synthetic Data Design

### Notice on Synthetic Data
The bundled datasets (`data/players.csv` and `data/matches.csv`) contain synthetic records generated deterministically with fixed random seeds for demonstration and evaluation. They do not represent real-world players or actual historical fixtures.

### 1. `players.csv` (140 records)
- **Identifiers & Bio**: `player_id`, `player_name`, `club`, `league`, `nationality`, `position`, `age`, `season`.
- **Playing Time**: `appearances`, `minutes_played`.
- **Attacking**: `goals`, `assists`, `shots`, `shots_on_target`, `xg`, `xa`, `key_passes`.
- **Passing & Possession**: `passes_completed`, `passes_attempted`.
- **Defending & Discipline**: `tackles`, `interceptions`, `yellow_cards`, `red_cards`.
- **Performance Rating**: `rating` (0.0 to 10.0 scale).

### 2. `matches.csv` (160 fixtures)
- **Fixture Info**: `match_id`, `match_date`, `season`, `league`.
- **Teams & Scorelines**: `home_team`, `away_team`, `home_goals`, `away_goals`.

---

## Football Analytics & Mathematical Formulas

All formulas are defined in `utils/metrics.py` and applied consistently across the application:

### 1. Goals & Assists per 90 Minutes
$$\text{Goals per 90} = \left(\frac{\text{Goals}}{\text{Minutes Played}}\right) \times 90 \quad (\text{if Minutes} > 0)$$
$$\text{Assists per 90} = \left(\frac{\text{Assists}}{\text{Minutes Played}}\right) \times 90 \quad (\text{if Minutes} > 0)$$

### 2. Goal Contributions per 90
$$\text{G+A per 90} = \left(\frac{\text{Goals} + \text{Assists}}{\text{Minutes Played}}\right) \times 90$$

### 3. Pass Completion Percentage
$$\text{Pass Completion \%} = \left(\frac{\text{Passes Completed}}{\text{Passes Attempted}}\right) \times 100 \quad (\text{if Attempted} > 0)$$

### 4. Shot Accuracy Percentage
$$\text{Shot Accuracy \%} = \left(\frac{\text{Shots on Target}}{\text{Total Shots}}\right) \times 100 \quad (\text{if Shots} > 0)$$

### 5. Expected Goals (xG) Difference
$$\text{xG Difference} = \text{Goals} - \text{xG}$$
*Descriptive metric comparing actual goal volume to statistical expected goal models.*

### 6. Defensive Actions per 90
$$\text{Defensive Actions per 90} = \left(\frac{\text{Tackles} + \text{Interceptions}}{\text{Minutes Played}}\right) \times 90$$

---

## Pandas & NumPy Implementation

- **Pandas**:
  - `groupby(['position'])` and `groupby(['club'])` for aggregating goals, assists, and average ratings.
  - Multi-condition Boolean masking for simultaneous filtering by league, minutes, and rating.
  - `drop_duplicates()` and `clip()` for enforcing dataset integrity constraints.
- **NumPy**:
  - `vectorized_per_90()`: Uses `np.divide` with zero-denominator `where=valid_mask` to prevent `ZeroDivisionError` and `NaN` warnings.
  - `vectorized_min_max_scale()`:
    $$\text{Normalized} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$
    Guarded against uniform series where $x_{\max} == x_{\min}$ by mapping uniform vectors to a neutral $0.5$ baseline.

---

## Matplotlib & Seaborn Visualizations

Configured in `services/chart_service.py`:
- Configured with headless non-interactive backend (`matplotlib.use('Agg')`) for thread safety on web servers.
- `plt.close(fig)` is invoked on every render call to eliminate memory leaks.
- Visual charts generated:
  1. **Correlation Heatmap**: Seaborn correlation matrix between Age, Minutes, Goals, Assists, xG, xA, Key Passes, and Rating.
  2. **Position Output**: Grouped bar chart comparing Goals and Assists by position.
  3. **Rating Distribution**: Histogram with Seaborn KDE curve.
  4. **Age Profile Curve**: Scatter plot with linear regression trendline.

---

## REST API Documentation

| Endpoint | Method | Query Parameters | Description |
|---|---|---|---|
| `/api/health` | `GET` | None | Reports application status and dataset row counts |
| `/api/filters` | `GET` | None | Returns distinct seasons, leagues, clubs, and positions |
| `/api/dashboard` | `GET` | `season`, `league` | Returns 6 KPI cards, chart datasets, and top performers |
| `/api/players` | `GET` | `search`, `position`, `league`, `club`, `min_minutes`, `min_rating`, `sort_by`, `sort_order`, `page`, `page_size` | Returns filterable, paginated players |
| `/api/players/<id>` | `GET` | `id` (int) | Returns single player profile and derived metrics |
| `/api/compare` | `GET` | `ids` (comma-separated ints) | Head-to-head comparison for 2–4 players with radar data |
| `/api/analytics/positions`| `GET` | None | Aggregate statistics by tactical position |
| `/api/analytics/clubs` | `GET` | None | Club squad output and average ratings |
| `/api/analytics/leagues` | `GET` | None | League-level scoring comparisons |
| `/api/analytics/correlation`| `GET`| None | Correlation matrix of numeric metrics |
| `/api/analytics/age` | `GET` | `metric` | Age vs. selected metric scatter plot dataset |
| `/api/analytics/matches` | `GET` | `season`, `league` | Match fixtures, results, and scoring summaries |
| `/api/insights` | `GET` | None | Deterministic analytical observations |
| `/api/data-quality` | `GET` | None | Data quality audit report |
| `/api/export/players.csv`| `GET` | Filters | Downloads filtered player records as CSV |
| `/api/export/matches.csv`| `GET` | None | Downloads match records as CSV |
| `/api/export/data-quality`| `GET`| None | Downloads formatted text audit report |
| `/api/charts/<name>` | `GET` | `name` in `[correlation, positions, ratings, age]` | Serves server-side generated high-DPI PNG chart |
| `/api/upload/players` | `POST` | `file` (multipart CSV) | Validates and activates custom player CSV |
| `/api/upload/matches` | `POST` | `file` (multipart CSV) | Validates and activates custom match CSV |
| `/api/dataset/reset` | `POST` | None | Reverts to bundled verified demo dataset |

---

## Installation & Setup (macOS / Local)

### Prerequisites
- macOS (or Linux / Windows) with **Python 3.11+** installed.
- Terminal or VS Code integrated terminal.

### 1. Navigate to Project Directory
```bash
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W5-6
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate on macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

## Running the Application

### 1. Start Flask Web Server
```bash
python3 app.py
```
*Expected terminal output:*
```
[INFO] DataManager successfully loaded: 140 players, 160 matches (Demo Dataset · Synthetic sample statistics)
[INFO] Starting Touchline Analytics on http://127.0.0.1:5002
 * Running on http://127.0.0.1:5002 (Press CTRL+C to quit)
```

### 2. Open in Your Browser
Open your browser and navigate to:
**[http://127.0.0.1:5002](http://127.0.0.1:5002)**

*(Note: If port 5002 is occupied, Touchline automatically binds to the next available port without crashing).*

---

## Running Automated Tests

Run the complete test suite using Python's standard `unittest` runner:
```bash
python3 -m unittest discover -s tests -v
```
*(All 23 unit and integration tests run deterministically in ~0.17 seconds).*

---

## Troubleshooting & Common Issues

### 1. `Port 5000 / 5001 Address already in use`
On modern macOS releases, Apple's AirPlay Receiver occupies port 5000. Touchline Analytics defaults to **Port 5002** and automatically scans for the lowest available port, eliminating port conflicts.

### 2. `python: command not found`
macOS bundles Python 3 under the `python3` command. Use `python3 app.py` or ensure your activated `.venv` is in your `$PATH`.

### 3. Matplotlib GUI Errors on macOS Cocoa
Touchline sets `matplotlib.use('Agg')` at the module level in `services/chart_service.py` before importing `pyplot`, preventing GUI thread conflicts.

---

## Responsible Interpretation of Football Statistics

1. **Correlation vs. Causation**: Statistical association between age and rating does not imply age causes higher performance.
2. **Positional Context**: Defenders naturally score fewer goals than Forwards; radar profiles should prioritize position-specific responsibilities.
3. **Small Sample Sizes**: Per-90 metrics carry higher variance for players with limited minutes (< 450 minutes). Touchline highlights small sample sizes with explicit warnings.

---

## Limitations & Future Enhancements

- **Current Limitations**: Event-level spatial coordinates (heatmaps, pass networks) and progressive carry distances are not modeled in the current aggregate schema.
- **Future Enhancements**:
  - Pitch pass maps and event-level xT (Expected Threat) calculations.
  - Integration with Wyscout / StatsBomb open event data.

---

*Touchline Analytics — Built with Python, Flask, Pandas, NumPy, Matplotlib, and Seaborn.*
