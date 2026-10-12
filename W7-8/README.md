# Energy Demand Forecasting & Optimization (Energy Intelligence)

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.0-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/pytest-23%20passed-success.svg)](https://docs.pytest.org/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An end-to-end, production-ready full-stack machine learning and optimization web application that forecasts electricity demand, benchmarks regressors against seasonal baselines, visualizes demand patterns, detects peak events, and optimizes simulated flexible electricity loads (such as EV charging and industrial storage) via constrained linear programming.

Built with **Python**, **Flask**, **scikit-learn**, **SciPy `linprog`**, **Pandas**, **NumPy**, and **Plotly.js**.

---

## 1. Project Overview & Features

- **24-Hour Recursive Machine Learning Forecasting**:
  - Implements genuine recursive hourly forecasting where each predicted value feeds into the rolling lag history for subsequent intervals without forward-looking data leakage.
- **Cross-Algorithm Model Arena**:
  - Compares **Seasonal Naive (24h baseline)**, **Ridge Regression**, **Random Forest Regressor**, and **HistGradientBoostingRegressor**.
  - Evaluates models on strictly chronological train (70%), validation (15%), and held-out test (15%) partitions. Never randomly shuffles time series data.
- **Constrained Flexible Load Optimization**:
  - Formulates and solves linear programming models using SciPy's `linprog` (HiGHS interior-point / simplex solver).
  - Simulates demand-side management (load shifting) under Time-Of-Use (TOU) tariffs and forbidden peak grid intervals.
  - Compares Unmanaged Baseline vs Cost-Focused vs Balanced Cost & Peak-Shaving scenarios while strictly conserving required energy ($\sum x_t = E_{req}$).
- **Resilient Weather Integration**:
  - Integrates with Open-Meteo Forecast API with request caching (1-hour TTL) and calibrated microclimate offline fallbacks.
- **Executive Audit & Reporting**:
  - Generates downloadable standalone HTML analytical audit reports and exports forecast predictions as CSV.
- **Modern Clean UI**:
  - High-contrast light workspace, dark charcoal sidebar, vibrant emerald/teal accents, responsive drawer navigation, and Plotly.js charts. Strictly zero purple gradients.

---

## 2. Architecture & Folder Structure

```
W7-8/
├── app.py                      # Flask Application Server & REST API endpoints
├── config.py                   # Central configuration, file paths, tariffs, and theme
├── requirements.txt            # Python dependencies
├── conftest.py                 # Pytest path resolution configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules for virtualenvs, caches, artifacts
├── README.md                   # Complete documentation and setup manual
│
├── data/
│   ├── raw/                    # Raw downloaded or uploaded CSVs
│   ├── processed/              # Aggregated 1-hour mean datasets
│   └── sample/                 # Bundled offline sample dataset (sample_energy.csv)
│
├── models/                     # Saved joblib model artifacts
├── reports/                    # Generated audit reports
├── instance/                   # Runtime experiment tracking JSON logs
│
├── scripts/
│   ├── download_data.py        # UCI dataset 849 fetcher via ucimlrepo
│   └── prepare_data.py         # Sample data generator and hourly resampler
│
├── services/
│   ├── __init__.py             # Services package initializer
│   ├── data_service.py         # Dataset ingestion, previews, summaries, upload validation
│   ├── preprocessing.py        # Deduplication, interpolation, hourly resampling, chronological splitting
│   ├── feature_engineering.py  # Calendar features, cyclical encodings, rolling statistics, lag features
│   ├── forecasting.py          # Seasonal Naive, Ridge, RF, HistGB, and recursive 24h prediction
│   ├── evaluation.py           # MAE, RMSE, WAPE, MAPE, R2, residual profiles, peak screening
│   ├── weather_service.py      # Open-Meteo API client with caching and offline fallback
│   ├── optimization.py         # SciPy linprog flexible load optimizer
│   └── report_service.py       # Standalone HTML report and CSV export generator
│
├── static/
│   ├── css/
│   │   └── style.css           # Clean modern design system (Light workspace, charcoal sidebar, teal accents)
│   └── js/
│       ├── app.js              # State controller, routing, toasts, report exporter
│       ├── charts.js           # Plotly.js chart creation suite
│       ├── dataset.js          # CSV upload, sample selection, preview table
│       ├── forecast.js         # Model training, arena leaderboard, forecast controls
│       └── optimization.js     # Load sliders, tariff schedules, optimization solver
│
├── templates/
│   └── index.html              # Responsive single-page dashboard UI (10 navigation sections)
│
└── tests/
    ├── test_data_service.py    # Tests dataset loading, summaries, and uploads
    ├── test_preprocessing.py   # Tests hourly resampling and chronological splits
    ├── test_forecasting.py     # Tests lag construction, baseline, ML models, and recursive forecasting
    ├── test_optimization.py    # Tests energy conservation, power limits, and infeasibility handling
    └── test_api.py             # Integration tests for Flask REST API routes
```

---

## 3. Dataset Attribution & Licensing

- **Dataset**: Power Consumption of Tetouan City (UCI Dataset ID: 849)
- **Creators**: Abdulwahed Salam, Abdellah El Hibaoui, Abdelouahid Lyhyaoui (2018)
- **Institution**: Abdelmalek Essaadi University, Tetouan, Morocco
- **URL**: [https://archive.ics.uci.edu/dataset/849/power+consumption+of+tetouan+city](https://archive.ics.uci.edu/dataset/849/power+consumption+of+tetouan+city)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Description**: Power consumption readings across 3 distribution zones (Zone 1, Zone 2, Zone 3) recorded every 10 minutes throughout 2017 with accompanying weather covariates.
- **Offline Fallback**: The repository includes `data/sample/sample_energy.csv` (8,640 records, 60 days @ 10-minute intervals) calibrated to Tetouan microclimate patterns, allowing the system to run 100% offline without external network access.

---

## 4. Installation & Setup (Mac / Linux)

### Step 1: Open Terminal in Project Directory
```bash
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W7-8
```

### Step 2: Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### Step 4: Download or Prepare Datasets
```bash
# Attempt download from UCI repository (gracefully falls back if network is offline)
python3 scripts/download_data.py

# Prepare calibrated sample data and hourly resampled dataset
python3 scripts/prepare_data.py
```

### Step 5: Run Automated Tests
```bash
pytest -q
```
Expected output:
```text
23 passed in 2.76s
```

### Step 6: Launch Web Application
```bash
python3 app.py
```

### Step 7: Access Dashboard in Browser
Open your browser and navigate to:
```
http://127.0.0.1:5003
```

---

## 5. Mathematical Formulation & Optimization Logic

### Flexible Load Optimization Model
The optimization module in `services/optimization.py` models flexible load shifting (e.g. EV fleet charging, HVAC pre-cooling) using Linear Programming solved via SciPy `linprog`:

$$\min_{\mathbf{x}, P_{\max}} \sum_{t=0}^{23} \text{Tariff}_t \cdot x_t + \lambda \cdot P_{\max}$$

**Subject to:**
1. **Energy Conservation**:
   $$\sum_{t=0}^{23} x_t = E_{req}$$
2. **Power Limits**:
   $$0 \le x_t \le P_{limit} \quad \forall t \in \text{EligibleHours}$$
3. **Forbidden Hours & Outside Window**:
   $$x_t = 0 \quad \forall t \in \text{UnavailableHours} \cup \{t < t_{start}\} \cup \{t > t_{end}\}$$
4. **Peak Demand Upper Bound**:
   $$\text{BaseDemand}_t + x_t \le P_{\max} \quad \forall t \in \{0, \dots, 23\}$$
5. **Non-negativity**:
   $$x_t \ge 0, \quad P_{\max} \ge 0$$

### Feasibility Pre-Check
The engine checks whether:
$$\sum_{t \in \text{EligibleHours}} P_{limit} \ge E_{req}$$
If the required energy exceeds the maximum deliverable power within the allowed window, the solver immediately rejects the request with a clear, actionable error message. It never silently reduces the required energy.

---

## 6. Machine Learning Algorithms & Evaluation

1. **Seasonal Naive (24h Baseline)**:
   - Predicts tomorrow's load directly from yesterday's same-hour load: $\hat{y}_t = y_{t-24}$.
   - Serves as the benchmark that all machine learning models must be compared against.
2. **Ridge Regression**:
   - $L_2$-regularized linear model trained on standardized calendar variables, cyclical sine/cosine encodings, weather features, past lags, and rolling averages.
3. **Random Forest Regressor**:
   - Ensemble of 80 decision trees capturing non-linear diurnal and weather interactions.
4. **HistGradientBoostingRegressor**:
   - High-speed histogram-based gradient boosted decision trees for time-series regression.

### Recursive 24-Hour Ahead Forecasting
- To forecast hours $t+1 \dots t+24$, the model predicts step $t+1$, adds $\hat{y}_{t+1}$ to an internal rolling history series, constructs subsequent lag features from newly generated predictions, and repeats sequentially.
- **Never uses true future demand observations as lags**.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the Energy Intelligence dashboard |
| `GET` | `/api/health` | Health status and dataset state |
| `GET` | `/api/datasets/sample` | Lists pre-installed sample datasets |
| `GET` | `/api/dataset/summary` | Dataset metadata, frequency, completeness, target stats |
| `GET` | `/api/dataset/preview` | Returns head preview records |
| `POST` | `/api/dataset/upload` | Validates and ingests user-uploaded CSV |
| `POST` | `/api/dataset/load-sample` | Switches active dataset to a bundled sample |
| `POST` | `/api/forecast/train` | Trains and benchmarks all selected models |
| `POST` | `/api/forecast/predict` | Generates recursive 24-hour ahead forecast |
| `POST` | `/api/forecast/evaluate` | Chronological evaluation metrics on held-out splits |
| `GET` | `/api/patterns` | Hourly profiles and 24x7 demand heatmap matrix |
| `GET` | `/api/anomalies` | Peak events and statistical residual anomalies |
| `GET` | `/api/weather` | Cached Open-Meteo hourly weather observations |
| `POST` | `/api/optimization/run` | Solves constrained load optimization via SciPy linprog |
| `GET` | `/api/experiments` | Retrieves experiment run history |
| `POST` | `/api/reports/export` | Generates standalone HTML report or CSV forecast file |

---

## 8. Analytical Limitations & Disclaimers

- **Load Shifting Simulation**: Calculations simulate demand-side management via mathematical programming. Cost savings represent estimations based on illustrative Time-Of-Use tariffs, not guaranteed commercial billing reductions.
- **Weather Projections**: Future weather variables rely on meteorological forecasts from Open-Meteo. When offline, microclimate patterns are synthesized based on historical seasonal distributions.
- **Machine Learning vs Baseline**: Machine learning regressors may not always outperform the Seasonal Naive baseline during periods of extreme regime change or highly repetitive diurnal behavior. All validation metrics are reported transparently.
