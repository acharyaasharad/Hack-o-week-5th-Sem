"""
MovieScope — Movie Ratings & Recommendation Explorer
Flask Web Application Backend
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)
from werkzeug.utils import secure_filename

from services.analytics import AnalyticsEngine
from services.data_manager import DataManager
from services.recommender import MovieRecommender

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
)
logger = logging.getLogger("MovieScope")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
CHARTS_DIR = STATIC_DIR / "charts"
TEMPLATES_DIR = BASE_DIR / "templates"

app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATES_DIR))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# Initialize Core Services
data_manager = DataManager(data_dir=DATA_DIR)
recommender = MovieRecommender(data_manager=data_manager)
analytics_engine = AnalyticsEngine(data_manager=data_manager)

logger.info("MovieScope services successfully initialized with dataset: %s", data_manager.source_type)


# --------------------------------------------------------------------------
# Central Error Handlers
# --------------------------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Not Found", "message": "The requested resource was not found."}), 404
    return render_template("index.html"), 200


@app.errorhandler(500)
def server_error(error):
    logger.error("Internal Server Error: %s", error)
    return jsonify({"success": False, "error": "Internal Server Error", "message": "An unexpected error occurred."}), 500


# --------------------------------------------------------------------------
# Web Routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the main application SPA."""
    return render_template("index.html")


# --------------------------------------------------------------------------
# Health and Dashboard API Endpoints
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Reports health status of the application."""
    return jsonify(
        {
            "status": "ok",
            "version": "1.0.0",
            "dataset_source": data_manager.source_type,
            "movies_count": len(data_manager.get_movies_df()),
            "ratings_count": len(data_manager.get_ratings_df()),
        }
    )


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Returns dashboard overview KPI summary statistics."""
    stats = analytics_engine.get_dashboard_stats()
    return jsonify({"success": True, "data": stats})


@app.route("/api/data-quality", methods=["GET"])
def get_data_quality():
    """Returns dataset cleaning and validation metrics."""
    report = data_manager.get_data_quality_report()
    return jsonify({"success": True, "data": report})


# --------------------------------------------------------------------------
# Movies API Endpoints
# --------------------------------------------------------------------------
@app.route("/api/movies", methods=["GET"])
def get_movies():
    """
    Returns filtered, sorted, paginated movie list.
    Query params:
      - search: string
      - genre: string
      - min_rating: float
      - min_votes: int
      - sort: 'rating' | 'popularity' | 'title' | 'year'
      - order: 'desc' | 'asc'
      - page: int
      - page_size: int
    """
    search = request.args.get("search", type=str)
    genre = request.args.get("genre", type=str)
    min_rating = request.args.get("min_rating", type=float)
    min_votes = request.args.get("min_votes", type=int)
    sort_by = request.args.get("sort", default="rating", type=str)
    sort_order = request.args.get("order", default="desc", type=str)
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=12, type=int)

    summary = analytics_engine.get_movie_summary(
        search=search,
        genre=genre,
        min_rating=min_rating,
        min_votes=min_votes,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return jsonify({"success": True, "data": summary})


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_single_movie(movie_id: int):
    """Returns detailed statistics for a single movie."""
    movie = data_manager.get_movie(movie_id)
    if not movie:
        return jsonify({"success": False, "message": f"Movie #{movie_id} not found."}), 404
    return jsonify({"success": True, "data": movie})


@app.route("/api/movies/<int:movie_id>/distribution", methods=["GET"])
def get_movie_rating_distribution(movie_id: int):
    """Returns rating frequency distribution for a specific movie."""
    dist = analytics_engine.get_movie_distribution(movie_id)
    return jsonify({"success": True, "data": dist})


# --------------------------------------------------------------------------
# Recommendations API Endpoints
# --------------------------------------------------------------------------
@app.route("/api/recommendations/<int:movie_id>", methods=["GET"])
def get_recommendations(movie_id: int):
    """
    Returns deterministic recommendations based on genre cosine similarity
    and Bayesian weighted ratings.
    """
    limit = request.args.get("limit", default=5, type=int)
    limit = max(1, min(20, limit))

    try:
        recommendations = recommender.recommend_similar_movies(movie_id=movie_id, limit=limit)
        return jsonify({"success": True, "movie_id": movie_id, "data": recommendations})
    except KeyError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        logger.error("Error generating recommendations: %s", e)
        return jsonify({"success": False, "message": "Failed to compute recommendations."}), 500


# --------------------------------------------------------------------------
# Analytics API Endpoints
# --------------------------------------------------------------------------
@app.route("/api/analytics/genres", methods=["GET"])
def get_genre_analytics():
    """Returns aggregated genre counts and ratings."""
    genres = analytics_engine.get_genre_statistics()
    return jsonify({"success": True, "data": genres})


@app.route("/api/analytics/ratings", methods=["GET"])
def get_ratings_analytics():
    """Returns statistical distribution of user ratings."""
    dist = analytics_engine.get_rating_distribution()
    return jsonify({"success": True, "data": dist})


@app.route("/api/analytics/trends", methods=["GET"])
def get_trends_analytics():
    """Returns release decade rating and volume trends."""
    trends = analytics_engine.get_rating_year_trends()
    return jsonify({"success": True, "data": trends})


@app.route("/api/analytics/top-movies", methods=["GET"])
def get_top_movies():
    """Returns top rated movies subject to sample size."""
    limit = request.args.get("limit", default=10, type=int)
    min_ratings = request.args.get("min_ratings", default=5, type=int)
    top_movies = analytics_engine.get_top_rated_movies(limit=limit, min_ratings=min_ratings)
    return jsonify({"success": True, "data": top_movies})


# --------------------------------------------------------------------------
# Charts API Endpoints (Serves Matplotlib & Seaborn Generated PNGs)
# --------------------------------------------------------------------------
@app.route("/api/charts/<chart_name>", methods=["GET"])
def get_chart(chart_name: str):
    """Generates and serves Matplotlib / Seaborn visualization charts."""
    try:
        if chart_name == "ratings":
            chart_file = analytics_engine.generate_rating_histogram()
        elif chart_name == "genres":
            chart_file = analytics_engine.generate_genre_chart()
        elif chart_name == "popularity":
            chart_file = analytics_engine.generate_popularity_chart()
        elif chart_name == "heatmap":
            chart_file = analytics_engine.generate_correlation_heatmap()
        elif chart_name == "trends":
            chart_file = analytics_engine.generate_trends_chart()
        else:
            return jsonify({"success": False, "message": f"Unknown chart: {chart_name}"}), 404

        return send_file(chart_file, mimetype="image/png", max_age=60)
    except Exception as e:
        logger.error("Chart generation error for %s: %s", chart_name, e)
        return jsonify({"success": False, "message": f"Could not generate chart: {e}"}), 500


# --------------------------------------------------------------------------
# Export API Endpoints
# --------------------------------------------------------------------------
@app.route("/api/export/<export_type>", methods=["GET"])
def export_data(export_type: str):
    """Exports data in CSV or TXT format."""
    try:
        if export_type == "movies":
            search = request.args.get("search", type=str)
            genre = request.args.get("genre", type=str)
            min_rating = request.args.get("min_rating", type=float)
            min_votes = request.args.get("min_votes", type=int)
            sort_by = request.args.get("sort", default="rating", type=str)
            sort_order = request.args.get("order", default="desc", type=str)

            content = analytics_engine.export_filtered_movies(
                search=search,
                genre=genre,
                min_rating=min_rating,
                min_votes=min_votes,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            return Response(
                content,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=moviescope_movies.csv"},
            )

        elif export_type == "genres":
            content = analytics_engine.export_genre_statistics()
            return Response(
                content,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=moviescope_genre_analysis.csv"},
            )

        elif export_type == "top-movies":
            content = analytics_engine.export_top_movies()
            return Response(
                content,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=moviescope_top_movies.csv"},
            )

        elif export_type == "report":
            content = analytics_engine.export_analysis_report()
            return Response(
                content,
                mimetype="text/plain",
                headers={"Content-Disposition": "attachment; filename=moviescope_report.txt"},
            )

        else:
            return jsonify({"success": False, "message": f"Invalid export type: {export_type}"}), 400

    except Exception as e:
        logger.error("Export error: %s", e)
        return jsonify({"success": False, "message": "Failed to generate export file."}), 500


# --------------------------------------------------------------------------
# Dataset Management (Upload & Reset)
# --------------------------------------------------------------------------
@app.route("/api/reset-data", methods=["POST"])
def reset_dataset():
    """Restores default bundled sample dataset."""
    try:
        data_manager.reset_to_sample()
        recommender.fit(data_manager)
        analytics_engine.set_data_manager(data_manager)
        logger.info("Dataset reset to sample data.")
        return jsonify({"success": True, "message": "Reset to bundled sample dataset successfully."})
    except Exception as e:
        logger.error("Reset data error: %s", e)
        return jsonify({"success": False, "message": f"Failed to reset data: {e}"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_dataset():
    """Uploads custom movies.csv and ratings.csv files."""
    if "movies" not in request.files or "ratings" not in request.files:
        return jsonify({"success": False, "message": "Both 'movies' and 'ratings' CSV files must be provided."}), 400

    movies_file = request.files["movies"]
    ratings_file = request.files["ratings"]

    if not movies_file.filename.endswith(".csv") or not ratings_file.filename.endswith(".csv"):
        return jsonify({"success": False, "message": "Only CSV files (.csv) are supported."}), 400

    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_movies_path = upload_dir / f"uploaded_movies_{secure_filename(movies_file.filename)}"
    temp_ratings_path = upload_dir / f"uploaded_ratings_{secure_filename(ratings_file.filename)}"

    try:
        movies_file.save(temp_movies_path)
        ratings_file.save(temp_ratings_path)

        # Validate and load
        data_manager.load_data(temp_movies_path, temp_ratings_path, source="User Uploaded Dataset")
        recommender.fit(data_manager)
        analytics_engine.set_data_manager(data_manager)

        logger.info("Custom dataset successfully loaded and models refitted.")
        return jsonify(
            {
                "success": True,
                "message": "Custom dataset uploaded and processed successfully.",
                "quality_report": data_manager.get_data_quality_report(),
            }
        )
    except Exception as e:
        logger.error("Dataset upload failed: %s", e)
        return jsonify({"success": False, "message": f"Dataset validation failed: {str(e)}"}), 400


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5000))
    # If default port is occupied (e.g. macOS AirPlay receiver on port 5000), fall back smoothly
    test_sock = socket.socket()
    try:
        test_sock.bind(("127.0.0.1", port))
        test_sock.close()
    except OSError:
        fallback_port = 5001
        logger.warning("Port %d is in use (e.g. macOS AirPlay Receiver). Using fallback port %d.", port, fallback_port)
        port = fallback_port

    logger.info("Starting MovieScope web application on http://127.0.0.1:%s", port)
    app.run(host="127.0.0.1", port=port, debug=True)

