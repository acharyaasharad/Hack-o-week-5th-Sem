# MovieScope — Movie Ratings & Recommendation Explorer

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-darkblue.svg)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24%2B-orange.svg)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8%2B-teal.svg)](https://matplotlib.org/)
[![Seaborn](https://img.shields.io/badge/Seaborn-0.13%2B-magenta.svg)](https://seaborn.pydata.org/)

**MovieScope** is a full-stack, data-driven web application and movie exploration platform built with Python, Flask, Pandas, NumPy, Matplotlib, Seaborn, and modern vanilla HTML5/CSS3/JavaScript. It demonstrates practical data science techniques: data cleaning, multi-dimensional aggregation, content-based recommendation via multi-hot vector cosine similarity, Bayesian-style weighted rankings, and analytical visualization generation.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Architecture & Technology Stack](#architecture--technology-stack)
3. [Project Structure](#project-structure)
4. [Dataset Specifications](#dataset-specifications)
5. [Recommendation & Ranking Algorithms](#recommendation--ranking-algorithms)
6. [Data Science & Analytics Implementation](#data-science--analytics-implementation)
7. [Installation & Setup (macOS / Local)](#installation--setup-macos--local)
8. [Running the Application](#running-the-application)
9. [Running Automated Tests](#running-automated-tests)
10. [REST API Documentation](#rest-api-documentation)
11. [Data Quality & Cleaning Rules](#data-quality--cleaning-rules)
12. [Troubleshooting & FAQ](#troubleshooting--faq)
13. [Future Enhancements & Limitations](#future-enhancements--limitations)

---

## Key Features

### 1. Live Interactive Dashboard
- **Real-Time KPIs**: Total movies, total ratings, unique users, unique genres, overall average rating, and highest-rated movie (applying a minimum rating threshold $m = 5$).
- **Top-Rated Films**: Curated showcase of top-tier cinema ranked by Bayesian weighted scores rather than single 5.0 outlier reviews.
- **Data Source Banner**: Active badge indicating whether the bundled verified sample or user-uploaded custom dataset is loaded.

### 2. Movie Explorer
- **Multi-parameter Search & Filter**: Search movie titles by keyword, filter by genre, filter by minimum star rating ($0.0 - 5.0$), and filter by minimum review volume ($0 - 50+$).
- **Sort Options**: Sort by title (A-Z/Z-A), average rating, popularity (rating count), or release year.
- **Server-Side Pagination**: Responsive card and table layouts with configurable page sizes, debounced input queries, and clear filter states.

### 3. Movie Detail View & Distribution
- **Deep-Dive Modal**: Detailed metadata including extracted release year, pipe-delimited genre badges, average rating, and total rating counts.
- **Rating Distribution**: Visual breakdown of 0.5 to 5.0 star frequencies for the selected movie.
- **One-Click Recommendations**: Directly triggers recommendations for any film from its modal view.

### 4. Hybrid Recommendation Engine
- **Content-Based Similarity**: Multi-hot genre encoding paired with vectorized cosine similarity across all catalog films.
- **Bayesian Confidence Adjustment**: Balances genre similarity with rating confidence so poorly reviewed or unreviewed movies don't dominate recommendations.
- **Transparent Explanations**: Dynamic, human-readable rationale (e.g. *"Shares Sci-Fi, Adventure, and Action genres with Interstellar"*).

### 5. Genre Analytics
- **Distribution & Popularity**: Explodes multi-genre films into individual categories to accurately capture overlaps without double-counting base records.
- **Visual Charts**: Matplotlib/Seaborn-generated bar charts comparing average ratings across genres subject to sample thresholds.

### 6. Rating Insights & Visualizations
- **Statistical Charts**:
  - `Rating Distribution`: Histogram displaying frequency of user ratings.
  - `Ratings vs. Popularity`: Scatter plot showing average rating against rating counts.
  - `Numerical Correlation Heatmap`: Seaborn correlation matrix between rating count, average rating, release year, and genre count.
  - `Release Year Trends`: Line and bar trend of cinematic output and rating progression over time.

### 7. Data Quality & Cleaning Audit
- **Full Transparency**: Reports missing values, duplicate user-movie pairs, rating range violations, and ratings referencing unknown movie IDs.
- **Audit Retainment**: Displays exact valid rows preserved after pipeline sanitization.

### 8. Data Export
- Export filtered movies as CSV.
- Export genre analytics summary as CSV.
- Export high-resolution analytical charts as PNG.
- Export data quality audit summary report as formatted TXT.

---

## Architecture & Technology Stack

```
   ┌─────────────────────────────────────────────────────────┐
   │                     Client Browser                      │
   │  (Vanilla HTML5, CSS3 Variables, ES6+ Fetch, Responsive) │
   └────────────────────────────┬────────────────────────────┘
                                │ JSON / PNG / CSV Streams
   ┌────────────────────────────▼────────────────────────────┐
   │                     Flask REST API                      │
   │           (app.py - Routing, Serialization)             │
   └───────┬────────────────────┼────────────────────┬───────┘
           │                    │                    │
┌──────────▼───────────┐ ┌──────▼────────────┐ ┌─────▼───────────────┐
│     DataManager      │ │  AnalyticsEngine  │ │   MovieRecommender  │
│ (data_manager.py)    │ │  (analytics.py)   │ │   (recommender.py)  │
│ Data loading, regex  │ │ Aggregation, KPIs │ │ Multi-hot encoding, │
│ year parsing, dedupe,│ │ Matplotlib/Seaborn│ │ Cosine similarity,  │
│ sanitization         │ │ headless charts   │ │ Bayesian weighting  │
└──────────┬───────────┘ └──────┬────────────┘ └─────┬───────────────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                                │
                   ┌────────────▼───────────┐
                   │    Pandas & NumPy      │
                   │ In-Memory DataFrames & │
                   │  Vectorized Matrices   │
                   └────────────────────────┘
```

- **Backend**: Python 3.9+, Flask 3.0+
- **Data Manipulation**: Pandas 2.0+ (DataFrames, GroupBy, Merging, Exploding)
- **Vectorized Mathematics**: NumPy 1.24+ (Cosine similarity, matrix dot products, Bayesian math)
- **Data Visualizations**: Matplotlib 3.8+ (headless `Agg` backend), Seaborn 0.13+
- **Frontend**: Semantic HTML5, CSS3 Grid/Flexbox with dark cinema design system, Vanilla JavaScript (ES6+ async/await)
- **Iconography & Fonts**: Lucide Icons, Google Fonts (Outfit & JetBrains Mono)

---

## Project Structure

```
W3-4/
├── app.py                     # Flask application routes, error handlers, and server bootstrap
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive documentation
├── .gitignore                 # Version control exclusions
│
├── data/
│   ├── movies.csv             # Movie catalog (movieId, title, genres)
│   └── ratings.csv            # Rating records (userId, movieId, rating, timestamp)
│
├── services/
│   ├── __init__.py            # Service package initializer
│   ├── data_manager.py        # Data loading, validation, year extraction, cleaning
│   ├── analytics.py           # Dashboard KPIs, distributions, trends, chart generation
│   └── recommender.py         # Multi-hot genre vectors, cosine similarity, Bayesian ranking
│
├── templates/
│   └── index.html             # Single-page application template
│
├── static/
│   ├── css/
│   │   └── style.css          # Dark cinema design system, layout, responsive styles
│   ├── js/
│   │   └── script.js          # SPA navigation, Fetch API client, modal and filter handlers
│   └── charts/
│       └── .gitkeep           # Target directory for server-generated chart PNGs
│
└── tests/
    ├── __init__.py            # Test package initializer
    ├── test_data_manager.py   # Unit tests for DataManager loading and validation
    ├── test_analytics.py      # Unit tests for analytics aggregations and KPIs
    ├── test_recommender.py    # Unit tests for similarity, weighting, and edge cases
    └── test_api.py            # Integration tests for Flask endpoints and error handling
```

---

## Dataset Specifications

The application consumes two standardized CSV files in `data/`:

### 1. `movies.csv`
| Column | Type | Description |
|---|---|---|
| `movieId` | Integer | Unique identifier for each movie |
| `title` | String | Movie title, with optional release year in parentheses e.g. `Inception (2010)` |
| `genres` | String | Pipe-delimited list of genres e.g. `Action\|Sci-Fi\|Thriller` |

### 2. `ratings.csv`
| Column | Type | Description |
|---|---|---|
| `userId` | Integer | Identifier of the user submitting the rating |
| `movieId` | Integer | Foreign key matching `movieId` in `movies.csv` |
| `rating` | Float | Rating between `0.5` and `5.0` in half-star increments |
| `timestamp`| Integer | Optional Unix epoch timestamp representing submission time |

*Bundled Sample Dataset*: Contains **60 diverse landmark films** (spanning 1968 to 2024 across 18 genres) and **1,576 authentic user ratings** submitted by 45 users, enabling rich statistical exploration out-of-the-box. Compatible with standard MovieLens small/full datasets.

---

## Recommendation & Ranking Algorithms

### Method A: Vectorized Genre Cosine Similarity
1. **Genre Vocabulary**: Extract all unique genres across the dataset into an ordered vocabulary $G = [g_1, g_2, \dots, g_K]$.
2. **Multi-Hot Encoding**: For each film $i$, construct a binary vector $\mathbf{v}_i \in \{0, 1\}^K$ where $v_{i,k} = 1$ if movie $i$ has genre $k$, else $0$.
3. **NumPy Cosine Similarity**: Given selected movie vector $\mathbf{u}$ and matrix of all movie vectors $\mathbf{M} \in \{0, 1\}^{N \times K}$:
   $$\text{similarity}(\mathbf{u}, \mathbf{v}_i) = \frac{\mathbf{u} \cdot \mathbf{v}_i}{\|\mathbf{u}\|_2 \|\mathbf{v}_i\|_2}$$
   Computed in NumPy using vectorized dot products and broadcasting with zero-division safety:
   ```python
   dot_prods = np.dot(genre_matrix, target_vector)
   norms = np.linalg.norm(genre_matrix, axis=1) * target_norm
   similarities = np.divide(dot_prods, norms, out=np.zeros_like(dot_prods), where=norms > 0)
   ```

### Method B: Bayesian-Style Weighted Rating
To prevent movies with 1 single 5.0 rating from ranking higher than cinematic masterpieces with thousands of high reviews, MovieScope applies the Bayesian weighted rating formula:
$$WR = \left(\frac{v}{v + m}\right) \times R + \left(\frac{m}{v + m}\right) \times C$$
- **$R$**: Movie's average rating.
- **$v$**: Number of ratings received by the movie.
- **$m$**: Prior minimum rating count threshold (configurable, default $m = 5$).
- **$C$**: Overall mean rating across the entire dataset.

### Combined Hybrid Score
The recommendation engine combines genre similarity with Bayesian rating confidence:
$$\text{Score} = w_{\text{sim}} \times \text{Similarity} + w_{\text{wr}} \times \left(\frac{WR}{5.0}\right)$$
- Default weights: $w_{\text{sim}} = 0.65$, $w_{\text{wr}} = 0.35$.
- Normalized on a scale of $0.0$ to $1.0$.
- Candidates are filtered to exclude the target movie itself.
- If a movie lacks genres, the system automatically falls back to rating confidence and explains why.

---

## Data Science & Analytics Implementation

### Pandas & NumPy Integration
- **`services/data_manager.py`**:
  - Regular expression extraction of 4-digit release years: `r'\((\d{4})\)'`.
  - Handling missing or invalid ratings outside $[0.5, 5.0]$.
  - Deduplicating `(userId, movieId)` pairs while retaining the latest record by timestamp.
  - Left-merging `movies` and `ratings` so unrated movies are preserved.
- **`services/analytics.py`**:
  - Exploding pipe-delimited genre lists (`df.explode('genre_list')`) to evaluate multi-genre movies accurately across all categories.
  - Computing standard deviation, rating counts, mean scores, and quantile distributions using NumPy and Pandas aggregations.
- **`services/recommender.py`**:
  - Efficient multi-hot genre matrix generation and vectorized cosine computations.

### Matplotlib & Seaborn Chart Architecture
- Matplotlib is configured with the headless **`Agg`** backend (`matplotlib.use('Agg')`) at the module level to ensure thread-safe chart generation on macOS and Linux servers without window-system dependency.
- Every chart explicitly closes its figure (`plt.close(fig)`) to eliminate memory leaks.
- Charts are styled with a dark theme palette matching the web interface.

---

## Installation & Setup (macOS / Local)

### Prerequisites
- macOS, Linux, or Windows with **Python 3.9+** installed.
- Terminal (macOS Terminal, iTerm2, or VS Code integrated terminal).

### 1. Clone or Open the Project
Navigate to the project root directory:
```bash
cd /Users/sharadvardhanacharya/Desktop/Hack-o-Week/W3-4
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate on macOS/Linux
source .venv/bin/activate

# (On Windows PowerShell: .venv\Scripts\Activate.ps1)
```

### 3. Install Required Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

---

## Running the Application

### 1. Start the Flask Server
```bash
python3 app.py
```
*Expected terminal output:*
```
[INFO] Loading dataset from: .../data
[INFO] Dataset loaded successfully: 60 movies, 1576 ratings.
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

### 2. Open in Your Browser
Open your favorite web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Running Automated Tests

MovieScope includes a comprehensive test suite across data management, analytics, recommendations, and API routes.

```bash
# Run all tests using unittest
python3 -m unittest discover -s tests -v
```

*Test Coverage Highlights:*
- `test_data_manager.py`: File loading, header validation, deduplication, invalid rating filtering, unknown movie ID handling, empty data resilience.
- `test_analytics.py`: KPI accuracy, multi-genre aggregation, top-rated thresholds, distribution calculations.
- `test_recommender.py`: Self-exclusion check, multi-hot matrix correctness, identical genre scores, zero-genre fallback, empty data handling.
- `test_api.py`: Route status codes, JSON structure validation, query parameter sanitization, error responses.

---

## REST API Documentation

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/api/health` | `GET` | None | Health check & service readiness |
| `/api/dashboard` | `GET` | None | Dashboard KPIs and top 6 rated movies |
| `/api/data-quality` | `GET` | None | Audit of data cleaning and row retention |
| `/api/movies` | `GET` | `page`, `page_size`, `search`, `genre`, `min_rating`, `min_votes`, `sort_by`, `sort_order` | Filterable, paginated movie list |
| `/api/movies/<id>` | `GET` | `id` (int) | Single movie details and statistics |
| `/api/movies/<id>/distribution` | `GET` | `id` (int) | Rating frequency breakdown for a movie |
| `/api/recommendations/<id>` | `GET` | `limit` (int, 1-30) | Recommendations for target film |
| `/api/analytics/genres` | `GET` | None | Genre rating statistics & counts |
| `/api/analytics/ratings` | `GET` | None | Overall rating histogram & metrics |
| `/api/analytics/trends` | `GET` | None | Trends by release decade/year |
| `/api/charts/<name>` | `GET` | `name` in `[ratings, genres, heatmap, popularity, trends]` | Serves generated high-res PNG chart |
| `/api/export/<type>` | `GET` | `type` in `[movies, genres, report]` | Downloads filtered CSV or TXT report |
| `/api/upload` | `POST` | `movies_file`, `ratings_file` (multipart) | Upload custom dataset files |
| `/api/reset-data` | `POST` | None | Reverts to bundled verified dataset |

---

## Data Quality & Cleaning Rules

1. **Title & Year Extraction**: Release years matching pattern `(YYYY)` are parsed into a dedicated numerical `year` column. Titles without years default `year` to `None`.
2. **Genre Normalization**: Empty or missing genres are tagged as `(no genres listed)`. Pipe-separated tags are trimmed and split into sets.
3. **Rating Validation**: Ratings must be numerical values in the range $[0.5, 5.0]$. Values outside this range or non-numeric types are dropped and logged.
4. **Deduplication**: When multiple ratings exist for the same `(userId, movieId)` pair, only the entry with the highest (most recent) timestamp is retained.
5. **Referential Integrity**: Ratings referencing movie IDs not present in `movies.csv` are filtered out and reported in the data quality audit.
6. **Preservation of Unrated Movies**: A Left Join ensures movies with zero ratings remain discoverable in search with $0$ reviews and a displayed rating of `N/A`.

---

## Troubleshooting & FAQ

### 1. `python: command not found` on macOS
macOS comes with Python 3 aliased as `python3`. Run:
```bash
python3 --version
python3 app.py
```

### 2. `Address already in use` (Port 5000 occupied)
If port 5000 is occupied by macOS AirPlay Receiver or another process:
- Turn off AirPlay Receiver in *System Settings > General > AirDrop & AirPlay > AirPlay Receiver*, **OR**
- Run Flask on a different port:
  ```bash
  FLASK_RUN_PORT=5050 python3 app.py
  ```
  (Or modify `port=5000` at the bottom of `app.py`).

### 3. Matplotlib GUI warnings on macOS
MovieScope sets `matplotlib.use('Agg')` in `services/analytics.py` prior to importing `pyplot`, preventing GUI framework conflicts on macOS Cocoa threads.

---

## Future Enhancements & Limitations

- **Current Recommendation Model**: Content-based filtering relying on genre multi-hot vectors combined with Bayesian rating weighting. It does not perform collaborative filtering (e.g., Matrix Factorization / SVD) across user-item interaction matrices.
- **Planned Enhancements**:
  - Collaborative filtering using SVD / ALS for personalized user profiles.
  - Natural Language Processing (NLP) on movie overviews and plot synopses via TF-IDF / sentence embeddings.
  - Direct integration with TMDB API for live poster art and actor filmographies.

---

*MovieScope — Built with Python, Flask, Pandas, NumPy, Matplotlib & Seaborn.*
