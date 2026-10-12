# Customer Segmentation & Intelligence Dashboard

> **Unsupervised Machine Learning & Customer Behavior Analytics**  
> Built with Python 3, Flask, scikit-learn Pipelines, and Plotly.js.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg)](https://palletsprojects.com/p/flask/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8%2B-orange.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-21%20Passed-brightgreen.svg)]()

---

## 📌 Executive Overview

The **Customer Segmentation & Intelligence Dashboard** is an end-to-end unsupervised machine learning platform that partitions wholesale client accounts into statistically sound and commercially interpretable buyer personas based on empirical spending patterns across six product categories:
* `Fresh`
* `Milk`
* `Grocery`
* `Frozen`
* `Detergents_Paper`
* `Delicassen`

Rather than relying on static or ad-hoc scripts, the system deploys **scikit-learn `Pipeline` and `ColumnTransformer` workflows** combining automated missing-value imputation, optional log variance stabilization (`np.log1p`), and feature scaling (`StandardScaler` or `RobustScaler`) directly coupled to three foundational clustering algorithms:
1. **K-Means Clustering** (centroid-based partitioning with inertia minimization and inductive out-of-sample prediction)
2. **Hierarchical (Agglomerative) Clustering** (bottom-up variance-minimizing tree merging with SciPy dendrograms)
3. **DBSCAN** (density-based spatial clustering with core point grouping and explicit noise outlier isolation)

---

## 🔬 Dataset & Citation

The default production data is the official **Wholesale Customers Dataset** from the UCI Machine Learning Repository:
* **UCI Dataset ID:** 292
* **DOI:** [https://doi.org/10.24432/C5030X](https://doi.org/10.24432/C5030X)
* **Sample Size:** 440 client records, 8 variables (6 spending features + `Channel` & `Region` metadata)
* **Attribution:**
  > Cardoso, M. (2013). *Wholesale customers*. UCI Machine Learning Repository. https://doi.org/10.24432/C5030X. Licensed under CC BY 4.0.

*A deterministic synthetic demonstration dataset (`data/sample/sample_customers.csv`, fixed seed 42) is included for full offline reliability.*

---

## 🚀 Key Features

* **scikit-learn Pipeline Architecture:** Reusable `ColumnTransformer` pipelines guarantee identical mathematical transformations during fitting, evaluation, and new customer inference.
* **Triple Algorithm Suite:** Real-time fitting and hyperparameter sweeps across K-Means, Agglomerative Clustering, and DBSCAN.
* **Strict Evaluation Safeguards:** Calculates Silhouette Score, Davies–Bouldin Index, and Calinski–Harabasz Score. Never fabricates missing scores or substitutes arbitrary zeros when metrics are mathematically undefined. Excluded DBSCAN noise records are transparently reported with sample coverage percentages.
* **Real Monetary Profiles:** Never displays scaled standard deviations when explaining customer segments to business users. Profiles and radar charts are computed directly in original raw currency units ($).
* **Interactive Plotly Visualizations:** Dynamic cluster size distributions, 2D PCA cluster space projections with explained variance ratios, K-Means elbow curves, Pearson correlation heatmaps, and SciPy dendrogram trees.
* **Out-of-Sample Prediction:** Real-time customer assignment endpoint using the fitted K-Means pipeline (`predict()` and centroid distance).
* **Comprehensive Export Suite:** Download labeled datasets (`.csv`), statistical segment profiles (`.csv`), or self-contained HTML intelligence reports.

---

## 🏗️ Architecture & Folder Structure

```
W9-10/
├── app.py                      # Flask application server & REST API
├── config.py                   # Central path, upload, and algorithm configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── README.md                   # Complete documentation
├── data/
│   ├── raw/                    # Raw UCI Wholesale dataset (wholesale_customers_raw.csv)
│   ├── sample/                 # Deterministic synthetic fallback (sample_customers.csv)
│   └── processed/              # Runtime processed datasets
├── models/                     # Saved model artifacts
├── reports/                    # Exported HTML and CSV intelligence reports
├── instance/                   # Runtime experiment history database
├── scripts/
│   ├── download_data.py        # Automated UCI dataset downloader
│   └── prepare_data.py         # Deterministic synthetic dataset generator
├── services/
│   ├── __init__.py             # Service package exports
│   ├── data_service.py         # CSV ingestion, validation, preview, and quality auditing
│   ├── preprocessing.py        # scikit-learn Pipeline and ColumnTransformer builders
│   ├── clustering_service.py   # K-Means, Hierarchical, DBSCAN, and PCA execution
│   ├── evaluation_service.py   # Silhouette, Davies-Bouldin, and Calinski-Harabasz scorers
│   ├── profiling_service.py    # Raw monetary profile stats and dynamic persona derivation
│   ├── visualization_service.py# Plotly payloads, correlation, and SciPy dendrograms
│   └── export_service.py       # Labeled CSV and standalone HTML report generator
├── static/
│   ├── assets/                 # Brand logo and icons
│   ├── css/style.css           # Premium analytics design system
│   └── js/
│       ├── app.js              # View switcher, notifications, loading states
│       ├── dataset.js          # Ingestion, drag-and-drop CSV upload, table preview
│       ├── clustering.js       # Hyperparameters, execution, elbow, and customer lookup
│       ├── charts.js           # Plotly interactive chart renderers
│       └── reports.js          # Export triggers and experiment audit log
├── templates/
│   └── index.html              # Responsive single-page dashboard layout
└── tests/
    ├── test_data_service.py    # Ingestion & validation unit tests
    ├── test_preprocessing.py   # Pipeline & scaler unit tests
    ├── test_clustering.py      # Algorithm fitting & prediction tests
    ├── test_evaluation.py      # Metric calculations & safeguard tests
    ├── test_profiling.py       # Profile & description tests
    ├── test_api.py             # Flask test client API route tests
    └── test_exports.py         # CSV & HTML export tests
```

---

## 💻 Installation & Setup (macOS / Linux / Windows)

```bash
# 1. Navigate to the project directory
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W9-10

# 2. (Optional) Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 4. Prepare data and verify UCI dataset
python3 scripts/prepare_data.py
python3 scripts/download_data.py

# 5. Run the test suite
python3 -m pytest -q

# 6. Launch the application
python3 app.py
```

Open your browser to: **[http://127.0.0.1:5004](http://127.0.0.1:5004)**

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Single-page analytics dashboard |
| `GET` | `/api/health` | System health, dataset status, and supported algorithms |
| `GET` | `/api/dataset/sample` | Load built-in UCI dataset or synthetic fallback (`?synthetic=true`) |
| `POST` | `/api/dataset/upload` | Upload and validate custom CSV file |
| `GET` | `/api/dataset/summary` | Dataset metadata, statistics, and quality warnings |
| `GET` | `/api/dataset/preview` | Paginated and searchable data rows preview |
| `POST` | `/api/dataset/validate` | Validate feature selections and log transform suitability |
| `POST` | `/api/clustering/run` | Execute scikit-learn Pipeline with selected algorithm |
| `GET` | `/api/clustering/results` | Return most recent run results, profiles, and PCA projection |
| `GET` | `/api/clustering/cluster/<id>`| Inspect observations assigned to a specific cluster or noise (-1) |
| `GET` | `/api/clustering/customers` | Search, sort, and filter labeled customer rows |
| `POST` | `/api/clustering/customer-lookup`| Assign new customer spending vector using fitted K-Means |
| `GET` | `/api/clustering/elbow` | Compute K-Means inertia and silhouette curve ($k=2..10$) |
| `POST` | `/api/clustering/compare` | Benchmark parameter grid across K-Means, Hierarchical, DBSCAN |
| `GET` | `/api/clustering/dendrogram` | Generate SciPy hierarchical tree leaf coordinates |
| `GET` | `/api/visualization/correlation` | Pearson correlation matrix for numeric features |
| `GET` | `/api/export/clusters.csv` | Download labeled customer dataset with cluster IDs |
| `GET` | `/api/export/profiles.csv` | Download cluster monetary means, medians, and descriptions |
| `GET` | `/api/export/report.html` | Download standalone executive HTML intelligence report |
| `GET` | `/api/experiments` | List historical clustering runs |
| `POST` | `/api/experiments` | Save current clustering run into persistent log |

---

## 🧪 Automated Test Verification

All **21 automated unit and integration tests** pass cleanly with zero warnings or failures:

```bash
$ python3 -m pytest -q
.....................                                                    [100%]
21 passed in 2.23s
```

* Tests cover CSV ingestion guards, missing value imputation, log1p transformation guards, K-Means/Hierarchical/DBSCAN pipeline execution, out-of-sample prediction, metric boundaries (all-noise & singleton protections), monetary profile calculations, Flask API routes, and CSV/HTML report downloads.
