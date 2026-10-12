# Dimensionality Reduction Visualizer — PCA & t-SNE Studio

> **High-Dimensional Data Compression, Orthogonal Variance & Manifold Learning**  
> Built with Python 3, Flask, scikit-learn Pipelines, and Plotly.js.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg)](https://palletsprojects.com/p/flask/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8%2B-orange.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()

---

## 📌 Executive Overview

The **Dimensionality Reduction Visualizer — PCA & t-SNE Studio** is an interactive machine learning laboratory designed to explore, compress, and compare multi-dimensional data distributions using two foundational paradigms:
1. **Principal Component Analysis (PCA):** Linear, global orthogonal projection maximizing captured feature variance.
2. **t-Distributed Stochastic Neighbor Embedding (t-SNE):** Non-linear, probabilistic manifold embedding preserving local neighborhood structure.

The platform provides student and researcher workflows with:
- **scikit-learn `Pipeline` & `ColumnTransformer` integration** (median imputation, `StandardScaler`, `RobustScaler`, and `np.log1p` variance stabilization).
- **PCA variance diagnostics:** Scree plots, cumulative explained variance, 2D/3D projections, reconstruction errors, and feature loadings (eigenvector coefficients).
- **t-SNE parameter controls:** Perplexity tuning with strict sample-size validation guards, iteration bounds, learning rates, and Kullback–Leibler (KL) divergence monitoring.
- **Side-by-side benchmarking:** Common observation sampling and color-mapping to compare PCA and t-SNE directly.
- **Observation Point Inspector:** Click-to-audit any scatter plot point to reveal original untransformed feature measurements.
- **Data & report exports:** Download PCA, t-SNE, or aligned combined coordinates (`.csv`), feature loadings (`.csv`), or standalone executive HTML reports.

---

## 🔬 Dataset & Citation

The default production benchmark is the official **Wine Recognition Dataset** from the UCI Machine Learning Repository:
* **Observations:** 178 chemical samples, 13 continuous chemical measurements, 3 cultivars.
* **DOI:** [https://doi.org/10.24432/C5PC7J](https://doi.org/10.24432/C5PC7J)
* **Attribution:**
  > Aeberhard, S. & Forina, M. (1991). *Wine Recognition Dataset*. UCI Machine Learning Repository. https://doi.org/10.24432/C5PC7J. Licensed under CC BY 4.0.

*Also includes built-in support for the Iris dataset (`load_iris`) and deterministic synthetic multi-cluster fallback data (`data/sample/sample_data.csv`).*

---

## 🏗️ Project Architecture

```
W11-12/
├── app.py                      # Flask web server & REST API
├── config.py                   # Central configuration & hyperparameters
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Complete documentation
├── data/
│   ├── raw/                    # Raw uploaded files
│   ├── sample/                 # Synthetic demonstration CSV
│   └── processed/              # Runtime embeddings
├── reports/                    # Generated reports
├── instance/                   # Runtime experiment history database
├── scripts/
│   └── generate_sample_data.py # Deterministic multi-cluster generator
├── services/
│   ├── __init__.py             # Service package exports
│   ├── dataset_service.py      # Wine, Iris, sample, and CSV upload management
│   ├── preprocessing_service.py# scikit-learn ColumnTransformers and Scalers
│   ├── dimensionality_service.py # PCA, t-SNE, loadings, and comparison pipelines
│   ├── evaluation_service.py   # Trustworthiness and reconstruction error scorers
│   ├── experiment_service.py   # Persistent experiment run logger
│   └── export_service.py       # Aligned CSV and HTML report exports
├── static/
│   ├── assets/logo.svg         # Brand SVG icon
│   ├── css/style.css           # Premium analytics design system
│   └── js/
│       ├── app.js              # View switcher and point inspector
│       ├── dataset.js          # Ingestion, CSV upload, table preview
│       ├── preprocessing.js    # Scaler and feature selectors
│       ├── pca.js              # PCA execution, loadings, scree plots
│       ├── tsne.js             # t-SNE execution and perplexity controls
│       ├── comparison.js       # Aligned side-by-side benchmarking
│       ├── charts.js           # Plotly interactive scatter and bar renderers
│       └── reports.js          # Exports and experiment history manager
├── templates/
│   └── index.html              # Single-page studio dashboard
└── tests/
    ├── test_dataset_service.py # Dataset loading & CSV validation tests
    ├── test_preprocessing.py   # Pipeline & scaler tests
    ├── test_pca.py             # PCA 2D/3D & loadings tests
    ├── test_tsne.py            # t-SNE & perplexity guard tests
    ├── test_evaluation.py      # Trustworthiness & reconstruction tests
    ├── test_api.py             # Flask API endpoints tests
    └── test_exports.py         # CSV & HTML export tests
```

---

## 💻 Installation & Setup (macOS / Linux / Windows)

```bash
# 1. Navigate to the project directory
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W11-12

# 2. (Optional) Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 4. Generate fallback demonstration data
python3 scripts/generate_sample_data.py

# 5. Run the test suite
python3 -m pytest -q

# 6. Start the Flask application
python3 app.py
```

Open your browser to: **[http://127.0.0.1:5005](http://127.0.0.1:5005)**

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Single-page analytics dashboard |
| `GET` | `/api/health` | System health, loaded dataset, and sample limits |
| `GET` | `/api/datasets` | List supported built-in datasets (Wine, Iris, Sample) |
| `POST` | `/api/dataset/load` | Load a chosen built-in dataset |
| `POST` | `/api/dataset/upload` | Upload and validate custom CSV file |
| `GET` | `/api/dataset/summary` | Dataset metadata, statistics, and quality warnings |
| `GET` | `/api/dataset/preview` | Paginated and searchable preview table |
| `POST` | `/api/pca/run` | Execute PCA with variance, loadings, and 2D/3D projections |
| `POST` | `/api/tsne/run` | Execute t-SNE with perplexity guards and KL divergence |
| `POST` | `/api/compare/run` | Run PCA and t-SNE on aligned common observation sample |
| `GET` | `/api/point/<row_id>` | Return original measurements and embedding coordinates for a row |
| `GET` | `/api/experiments` | List historical dimensionality reduction runs |
| `GET` | `/api/export/pca.csv` | Download PCA PC1/PC2 coordinates |
| `GET` | `/api/export/tsne.csv` | Download t-SNE coordinates |
| `GET` | `/api/export/combined.csv` | Download row-aligned PCA and t-SNE coordinates |
| `GET` | `/api/export/loadings.csv` | Download principal component eigenvector coefficients |
| `GET` | `/api/export/report` | Download standalone executive HTML intelligence report |

---

## 🧪 Automated Test Verification

All **17 automated unit and integration tests** pass cleanly:

```bash
$ python3 -m pytest -q
.................                                                        [100%]
17 passed in 3.04s
```
