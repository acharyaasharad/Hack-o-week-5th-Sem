# Ensemble Learning & Generalization Lab

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://palletsprojects.com/p/flask/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-orange.svg)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.4-red.svg)](https://xgboost.readthedocs.io/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.7-green.svg)](https://lightgbm.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An interactive, full-stack machine learning educational platform designed for college students and data science practitioners to investigate **Ensemble Learning**, the **Bias–Variance Trade-off**, **L1/L2 Regularization**, and **Leakage-Free Predictive Workflows**.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Machine Learning Concepts Covered](#key-machine-learning-concepts-covered)
3. [Architecture and Leakage Safeguards](#architecture-and-leakage-safeguards)
4. [Benchmark Datasets & Citations](#benchmark-datasets--citations)
5. [Technology Stack](#technology-stack)
6. [Directory Structure](#directory-structure)
7. [Installation & Setup on macOS](#installation--setup-on-macos)
8. [Testing & Verification](#testing--verification)
9. [REST API Specification](#rest-api-specification)
10. [References](#references)

---

## 1. Project Overview

The **Ensemble Learning & Generalization Lab** provides a hands-on, empirical workbench where users can train, evaluate, and inspect machine learning models across classification and regression benchmarks. Unlike static dashboards or isolated notebooks, every curve, metric, and diagnostic insight is calculated dynamically from real fitted `scikit-learn`, `XGBoost`, and `LightGBM` estimators.

### Core Capabilities
- **Model Arena:** Compare Dummy baselines, Logistic Regression (L1/L2), Ridge/Lasso, Decision Trees, Bagging, Random Forest, Gradient Boosting, XGBoost, and LightGBM on strictly fair data splits.
- **Bias–Variance & Generalization Lab:** Real-time parameter sweeps (`max_depth`, `n_estimators`, `min_samples_leaf`) plotting Training vs. Validation curves, generalization gaps, and a synthetic polynomial regression demonstration (Degrees 1, 4, 12).
- **L1 & L2 Regularization Lab:** Inspect parameter penalties, weight shrinkage, and coefficient sparsity (zero-valued weights in Lasso/L1) across log-scaled regularization grids.
- **Prediction Playground:** Interactive dynamic form generated from the fitted model's schema, performing end-to-end inference through the learned preprocessing pipeline.
- **Executive Reporting & Exports:** Download benchmark leaderboards as CSV or generate standalone, styled HTML experiment reports with timestamps and model metadata.

---

## 2. Key Machine Learning Concepts Covered

### A. Bagging (Bootstrap Aggregation)
- Multiple base estimators (typically high-variance Decision Trees) are trained independently in parallel on bootstrap resamples of the dataset.
- In Random Forests, random feature subsets are additionally considered at each node split to decorrelate individual trees.
- **Primary Benefit:** Significantly reduces overall variance without increasing bias.

### B. Boosting (Gradient Tree Boosting)
- Base models are trained sequentially. Each subsequent learner fits the negative gradient (pseudo-residuals) of the cumulative loss function.
- Shrinkage (learning rate) scales the contribution of each new tree, dampening oscillation and preventing premature overfitting.
- **Primary Benefit:** Systematically lowers bias and variance, requiring careful regularization (`max_depth`, `subsample`, `reg_alpha`, `reg_lambda`).

### C. XGBoost vs. LightGBM
- **XGBoost:** Implements exact/approximate greedy split finding with 2nd-order Taylor expansion approximations of the loss function and explicit L1 (`reg_alpha`) and L2 (`reg_lambda`) leaf weight penalties.
- **LightGBM:** Employs histogram-based feature binning and leaf-wise (best-first) tree growth with maximum depth constraints, optimizing execution speed and memory efficiency.

### D. The Bias–Variance Tradeoff
- **Underfitting (High Bias):** Model assumptions are too restrictive (e.g. Degree 1 polynomial on quadratic data). Both training and validation errors are high.
- **Overfitting (High Variance):** Model captures idiosyncratic noise in the training set (e.g. unpruned deep decision tree). Training performance is near-perfect, but validation error spikes, creating a wide **generalization gap**.
- **Optimal Complexity:** The hyperparameter balance that minimizes validation error on unseen data.

### E. L1 vs. L2 Regularization
- **L1 Penalty (Lasso / `reg_alpha`):** Adds the absolute sum of coefficients to the loss ($\lambda \sum |w_i|$). Induces geometric corners at zero axes, yielding true **feature sparsity**.
- **L2 Penalty (Ridge / `reg_lambda`):** Adds the squared magnitude of coefficients ($\lambda \sum w_i^2$). Shrinks weights smoothly toward zero without eliminating them completely.

---

## 3. Architecture and Leakage Safeguards

```
Raw Observations
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 1. Train / Validation / Final Held-Out Test Splitting  │
│    (Default: 70% Train, 15% Validation, 15% Held-Out)   │
└────────────────────────────────────────────────────────┘
       │                              │                 │
   Train Split                   Validation Split   Held-Out Test
       │                              │                 │
       ▼                              │                 │
┌──────────────────────────────┐      │                 │
│ 2. Feature Preprocessor      │      │                 │
│    Fitted ONLY on Train Data │      │                 │
│    - Median Imputation       │      │                 │
│    - OneHotEncoder (ignore)  │      │                 │
│    - Scaler (if linear)      │      │                 │
└──────────────────────────────┘      │                 │
       │                              │                 │
       ▼                              │                 │
┌──────────────────────────────┐      │                 │
│ 3. Model Training            │      │                 │
│    Estimator fit on Train    │      │                 │
└──────────────────────────────┘      │                 │
       │                              │                 │
       ▼                              ▼                 │
┌──────────────────────────────────────────────┐        │
│ 4. Validation Evaluation & Arena Ranking     │        │
│    Hyperparameters tuned on Validation only  │        │
└──────────────────────────────────────────────┘        │
                                                        ▼
┌───────────────────────────────────────────────────────────────┐
│ 5. Held-Out Test Evaluation                                   │
│    Evaluated ONCE on the selected winner for unbiased testing │
└───────────────────────────────────────────────────────────────┘
```

### Critical Leakage Safeguards
1. **UCI Bank Marketing Safeguard:** The `duration` attribute describes call duration in seconds. In realistic banking workflows, call length is completely unknown *prior* to dialing. Including it causes severe target leakage. The system automatically excludes `duration` by default and raises prominent visual warnings.
2. **UCI Bike Sharing Safeguard:** `casual` and `registered` rider counts directly sum to total rentals `cnt` ($casual + registered = cnt$). Excluded by default to prevent circular target leakage.
3. **Split-First Preprocessing:** All imputers, encoders, and scalers are fitted exclusively on `X_train`. Validation and test splits are transformed using the training parameters.

---

## 4. Benchmark Datasets & Citations

1. **UCI Bank Marketing** (Classification)
   - *Target:* `deposit_subscribed` (or `y`, binary classification).
   - *Citation:* Moro, S., Rita, P., & Cortez, P. (2014). Bank Marketing. UCI Machine Learning Repository. [https://doi.org/10.24432/C5K306](https://doi.org/10.24432/C5K306). Licensed under CC BY 4.0.
2. **UCI Bike Sharing** (Regression)
   - *Target:* `rental_count` (or `cnt`, continuous regression).
   - *Citation:* Fanaee-T, H. (2013). Bike Sharing. UCI Machine Learning Repository. [https://doi.org/10.24432/C5W894](https://doi.org/10.24432/C5W894). Licensed under CC BY 4.0.
3. **Synthetic Demonstration Fallbacks**
   - Deterministic sample CSV files (`sample_classification.csv`, `sample_regression.csv`) generated with fixed seed `42` ensuring the application is fully functional offline without external internet access.

---

## 5. Technology Stack

- **Backend:** Python 3.12 / 3.14, Flask, pandas, NumPy, SciPy, scikit-learn, XGBoost, LightGBM, python-dotenv.
- **Frontend:** Semantic HTML5, Vanilla CSS3 (modern analytics theme: dark navy sidebar, clean cards, teal/indigo accents), Vanilla JavaScript, Plotly.js CDN.
- **Testing:** pytest, Flask test client.

---

## 6. Directory Structure

```
W13-14/
├── app.py                      # Flask REST application & routing entrypoint
├── config.py                   # Centralized application paths, port 5006, thresholds
├── requirements.txt            # Dependency list
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── README.md                   # Comprehensive documentation
├── templates/
│   ├── index.html              # Complete single-page analytics dashboard
│   └── report_template.html    # Standalone HTML experiment report template
├── static/
│   ├── css/style.css           # Modern professional analytics UI stylesheet
│   ├── js/
│   │   ├── app.js              # Application controller & tab orchestrator
│   │   ├── charts.js           # Plotly visualization wrappers
│   │   ├── dataset.js          # Dataset loader, CSV upload, leakage warnings
│   │   ├── model_arena.js      # Leaderboard, candidate training, held-out test
│   │   ├── generalization.js   # Complexity sweeps & synthetic demo
│   │   ├── regularization.js   # L1/L2 penalty sweeps & sparsity tracking
│   │   ├── prediction.js       # Dynamic input form & live inference
│   │   └── reports.js          # CSV and HTML report export handlers
│   └── assets/logo.svg         # Application vector brand logo
├── services/
│   ├── data_service.py         # Dataset ingestion & leakage guards
│   ├── split_service.py        # Leakage-free 70/15/15 partitioning
│   ├── preprocessing_service.py# scikit-learn ColumnTransformer pipelines
│   ├── model_registry.py       # Estimator factory (Dummy, Ensembles, XGB, LGBM)
│   ├── training_service.py     # Fair pipeline execution & metric logging
│   ├── metrics_service.py      # Classification & regression score calculations
│   ├── generalization_service.py# Complexity curves & synthetic polynomial lab
│   ├── regularization_service.py# Parameter penalty sweeps & coefficient analysis
│   ├── interpretation_service.py# Feature importance extraction
│   ├── experiment_service.py   # Local experiment run persistence
│   └── export_service.py       # CSV and executive HTML generation
├── scripts/
│   ├── download_datasets.py    # Optional UCI repo ingestion
│   └── generate_sample_data.py # Deterministic offline sample generation
├── tests/
│   ├── test_data_service.py    # Data ingestion and leakage tests
│   ├── test_preprocessing.py   # Preprocessing pipeline tests
│   ├── test_splits.py          # Data split ratio and disjointness tests
│   ├── test_models.py          # Model catalog verification
│   ├── test_metrics.py         # Scoring metric calculations
│   ├── test_generalization.py  # Synthetic polynomial demonstration tests
│   ├── test_regularization.py  # L1/L2 sweep tests
│   ├── test_api.py             # Flask endpoint integration tests
│   └── test_exports.py         # CSV & HTML export validation tests
└── data/
    ├── raw/                    # Raw UCI datasets (optional)
    ├── processed/              # Cleaned splits
    └── sample/                 # Offline fallback synthetic datasets
```

---

## 7. Installation & Setup on macOS

### Step 1: Create Virtual Environment
```bash
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W13-14
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python3 app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5006`**

---

## 8. Testing & Verification

Run the comprehensive automated test suite:
```bash
python3 -m pytest -q
```
*Result:* 20 passed tests covering data pipelines, preprocessing, leakage safeguards, model catalog, metrics, generalization, regularization, REST endpoints, and exports.

Run compilation validation:
```bash
python3 -m compileall app.py config.py services scripts tests
```

---

## 9. REST API Specification

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | Serves main interactive single-page dashboard |
| `GET /api/health` | `GET` | System health check, XGBoost/LightGBM status |
| `GET /api/datasets` | `GET` | List available benchmark datasets |
| `POST /api/dataset/load` | `POST` | Load dataset with automated leakage guards |
| `POST /api/dataset/upload` | `POST` | Upload and validate custom CSV dataset |
| `GET /api/models` | `GET` | Return catalog of supported models for active task |
| `POST /api/models/compare` | `POST` | Train multiple candidate models on identical splits |
| `POST /api/models/final-evaluate` | `POST` | Evaluate selected validation winner on held-out test |
| `POST /api/generalization/complexity-sweep` | `POST` | Run model complexity sweep across parameter values |
| `POST /api/generalization/synthetic-demo` | `POST` | Compute synthetic polynomial regression tradeoff |
| `POST /api/regularization/sweep` | `POST` | Run L1/L2 regularization strength sweep |
| `POST /api/predict` | `POST` | Perform live inference for custom observation |
| `GET /api/export/comparison` | `GET` | Download model arena leaderboard as CSV |
| `GET /api/export/report` | `GET` | Download standalone executive HTML report |

---

## 10. References

- **scikit-learn Ensemble Methods:** [https://scikit-learn.org/stable/modules/ensemble.html](https://scikit-learn.org/stable/modules/ensemble.html)
- **scikit-learn Validation & Learning Curves:** [https://scikit-learn.org/stable/modules/learning_curve.html](https://scikit-learn.org/stable/modules/learning_curve.html)
- **XGBoost Python API:** [https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html)
- **LightGBM Python API:** [https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html)
- **UCI Bank Marketing:** [https://doi.org/10.24432/C5K306](https://doi.org/10.24432/C5K306)
- **UCI Bike Sharing:** [https://doi.org/10.24432/C5W894](https://doi.org/10.24432/C5W894)
