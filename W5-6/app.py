"""Touchline Analytics — Football Analytics & Player Comparison Lab.
Flask Application Web Server & REST API.
"""

from pathlib import Path
import os
import io
import csv
import logging
import socket
from typing import Dict, Any

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file,
    Response,
)

import pandas as pd
import numpy as np

import config
from services.data_manager import DataManager
from services.analytics_engine import AnalyticsEngine
from services.comparison_engine import ComparisonEngine
from services.insights_engine import InsightsEngine
from services.chart_service import ChartService
from utils.validators import validate_query_params, sanitize_filename

# --------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Flask Application Factory
# --------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder=str(config.TEMPLATES_DIR),
    static_folder=str(config.STATIC_DIR),
)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize Domain Services
data_manager = DataManager()
analytics_engine = AnalyticsEngine(data_manager)
comparison_engine = ComparisonEngine(data_manager)
insights_engine = InsightsEngine(data_manager)
chart_service = ChartService(data_manager)


# --------------------------------------------------------------------------
# Web Page Route
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the main single-page application interface."""
    return render_template(
        "index.html",
        app_name=config.APP_NAME,
        version=config.VERSION,
        source_name=data_manager.source_name,
        is_custom=data_manager.is_custom,
    )


# --------------------------------------------------------------------------
# Health & Status API
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint reporting dataset readiness and service status."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.VERSION,
        "players_loaded": len(data_manager.get_players_df()),
        "matches_loaded": len(data_manager.get_matches_df()),
        "source": data_manager.source_name,
        "is_custom": data_manager.is_custom,
    })


@app.route("/api/filters", methods=["GET"])
def get_filters():
    """Returns dynamic available filter choices from the loaded dataset."""
    try:
        filters = analytics_engine.get_available_filters()
        return jsonify({"success": True, "data": filters})
    except Exception as e:
        logger.error("Error fetching filters: %s", e)
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------------------------------------------------------
# Dashboard Overview API
# --------------------------------------------------------------------------
@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    """Returns 6 KPI cards, chart datasets, and top performers."""
    season = request.args.get("season")
    league = request.args.get("league")
    try:
        stats = analytics_engine.get_dashboard_stats(season=season, league=league)
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        logger.error("Error computing dashboard stats: %s", e)
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------------------------------------------------------
# Players API
# --------------------------------------------------------------------------
@app.route("/api/players", methods=["GET"])
def get_players():
    """Returns filterable, searchable, and paginated players."""
    try:
        sanitized_params = validate_query_params(request.args.to_dict())
        results = analytics_engine.filter_players(sanitized_params)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        logger.error("Error filtering players: %s", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/players/<int:player_id>", methods=["GET"])
def get_player_details(player_id: int):
    """Returns single player profile record with derived statistics."""
    player = data_manager.get_player_by_id(player_id)
    if not player:
        return jsonify({"success": False, "message": f"Player with ID {player_id} not found."}), 404

    # Clean NaNs
    clean_player = {k: (None if pd.isna(v) else v) for k, v in player.items()}
    return jsonify({"success": True, "data": clean_player})


# --------------------------------------------------------------------------
# Compare Players API
# --------------------------------------------------------------------------
@app.route("/api/compare", methods=["GET"])
def compare_players():
    """Compares 2 to 4 unique players simultaneously."""
    raw_ids = request.args.get("ids", "")
    if not raw_ids:
        return jsonify({"success": False, "message": "Missing 'ids' parameter (comma-separated IDs)."}), 400

    try:
        ids_list = [int(i.strip()) for i in raw_ids.split(",") if i.strip().isdigit()]
    except ValueError:
        return jsonify({"success": False, "message": "Invalid player IDs provided."}), 400

    result = comparison_engine.compare_players(ids_list)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


# --------------------------------------------------------------------------
# Analytics Endpoints
# --------------------------------------------------------------------------
@app.route("/api/analytics/positions", methods=["GET"])
def get_position_analytics():
    """Returns position-level aggregate statistics."""
    try:
        data = analytics_engine.get_position_analytics()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/clubs", methods=["GET"])
def get_club_analytics():
    """Returns club-level summaries."""
    try:
        data = analytics_engine.get_club_analytics()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/leagues", methods=["GET"])
def get_league_analytics():
    """Returns league-level summaries."""
    try:
        data = analytics_engine.get_league_analytics()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/ratings", methods=["GET"])
def get_ratings_analytics():
    """Returns rating distribution data."""
    try:
        stats = analytics_engine.get_dashboard_stats()
        return jsonify({"success": True, "data": stats.get("rating_distribution", [])})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/correlation", methods=["GET"])
def get_correlation():
    """Returns Pearson correlation matrix for numerical metrics."""
    try:
        data = analytics_engine.get_correlation_matrix()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/age", methods=["GET"])
def get_age_performance():
    """Returns scatter plot data of player age vs selected performance metric."""
    y_metric = request.args.get("metric", "rating")
    try:
        data = analytics_engine.get_age_performance_data(y_metric=y_metric)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/trends", methods=["GET"])
def get_match_trends():
    """Returns match scoring trends over valid calendar months."""
    try:
        stats = analytics_engine.get_dashboard_stats()
        return jsonify({"success": True, "data": stats.get("match_trends", [])})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/analytics/matches", methods=["GET"])
def get_match_analytics():
    """Returns match fixtures, results, and scoring summaries."""
    season = request.args.get("season")
    league = request.args.get("league")
    try:
        data = analytics_engine.get_match_analytics(season=season, league=league)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/insights", methods=["GET"])
def get_insights():
    """Returns deterministic mathematical observations from loaded data."""
    try:
        data = insights_engine.generate_insights()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/data-quality", methods=["GET"])
def get_data_quality():
    """Returns structured data-quality audit report."""
    try:
        report = data_manager.get_data_quality_report()
        return jsonify({"success": True, "data": report})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------------------------------------------------------
# Chart Image Streaming Endpoints (Matplotlib & Seaborn Generated PNGs)
# --------------------------------------------------------------------------
@app.route("/api/charts/<chart_name>", methods=["GET"])
def get_chart(chart_name: str):
    """Serves high-resolution Matplotlib / Seaborn visualization charts."""
    try:
        if chart_name == "correlation":
            chart_file = chart_service.generate_correlation_heatmap()
        elif chart_name == "positions":
            chart_file = chart_service.generate_position_comparison()
        elif chart_name == "ratings":
            chart_file = chart_service.generate_rating_distribution()
        elif chart_name == "age":
            chart_file = chart_service.generate_age_performance_scatter()
        else:
            return jsonify({"success": False, "message": f"Unknown chart type: {chart_name}"}), 404

        return send_file(chart_file, mimetype="image/png", max_age=30)
    except Exception as e:
        logger.error("Chart generation failed for %s: %s", chart_name, e)
        return jsonify({"success": False, "message": f"Chart rendering failed: {str(e)}"}), 500


# --------------------------------------------------------------------------
# Export Endpoints (CSV & Plain Text Quality Reports)
# --------------------------------------------------------------------------
@app.route("/api/export/players.csv", methods=["GET"])
def export_players_csv():
    """Exports filtered or complete player records as downloadable CSV."""
    try:
        sanitized_params = validate_query_params(request.args.to_dict())
        # Disable pagination for export
        sanitized_params["page_size"] = 10000
        filtered = analytics_engine.filter_players(sanitized_params)
        players = filtered.get("players", [])

        if not players:
            return Response("No player records found matching filters.", mimetype="text/csv", status=404)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(players[0].keys()))
        writer.writeheader()
        writer.writerows(players)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=touchline_players_export.csv"},
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/export/matches.csv", methods=["GET"])
def export_matches_csv():
    """Exports match records as downloadable CSV."""
    try:
        matches_df = data_manager.get_matches_df()
        if matches_df.empty:
            return Response("No match records found.", mimetype="text/csv", status=404)

        output = io.StringIO()
        matches_df.to_csv(output, index=False)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=touchline_matches_export.csv"},
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/export/data-quality", methods=["GET"])
def export_data_quality():
    """Downloads formatted text report of data quality and cleaning audit."""
    try:
        report = data_manager.get_data_quality_report()
        lines = [
            "================================================================================",
            " TOUCHLINE ANALYTICS — DATA QUALITY & AUDIT REPORT",
            "================================================================================",
            f"Active Dataset: {report.get('source_name')}",
            f"Completeness Score: {report.get('completeness_score')}%\n",
            "--- PLAYERS DATASET ---",
            f"Raw Rows Ingested: {report.get('players', {}).get('raw_rows')}",
            f"Valid Rows Retained: {report.get('players', {}).get('valid_rows')}",
            f"Dropped Rows: {report.get('players', {}).get('dropped_rows')}",
            "Issues Encountered:",
        ]
        for issue in report.get("players", {}).get("issues", []):
            lines.append(f" - [{issue.get('issue_type')}] Column: {issue.get('column')}, Count: {issue.get('count')} -> Action: {issue.get('action')}")

        lines.extend([
            "\n--- MATCHES DATASET ---",
            f"Raw Rows Ingested: {report.get('matches', {}).get('raw_rows')}",
            f"Valid Rows Retained: {report.get('matches', {}).get('valid_rows')}",
            f"Dropped Rows: {report.get('matches', {}).get('dropped_rows')}",
            "Issues Encountered:",
        ])
        for issue in report.get("matches", {}).get("issues", []):
            lines.append(f" - [{issue.get('issue_type')}] Column: {issue.get('column')}, Count: {issue.get('count')} -> Action: {issue.get('action')}")

        lines.append("\nReport generated by Touchline Analytics DataManager.\n")

        return Response(
            "\n".join(lines),
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment; filename=data_quality_audit.txt"},
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------------------------------------------------------
# Dataset Upload & Reset Endpoints
# --------------------------------------------------------------------------
@app.route("/api/upload/players", methods=["POST"])
def upload_players():
    """Validates and activates user uploaded players CSV."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in upload request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "message": "No file selected."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Unsupported file format. Please upload a CSV file."}), 400

    filename = sanitize_filename(file.filename)
    target_path = config.UPLOADS_DIR / f"custom_players_{filename}"

    try:
        file.save(target_path)
        # Attempt loading
        data_manager.load_data(
            target_path,
            data_manager.default_matches_path,
            source_name=f"Custom: {file.filename}",
            is_custom=True,
        )
        analytics_engine.set_data_manager(data_manager)
        comparison_engine.set_data_manager(data_manager)
        insights_engine.set_data_manager(data_manager)
        chart_service.set_data_manager(data_manager)

        logger.info("Custom player dataset successfully activated: %s", target_path)
        return jsonify({
            "success": True,
            "message": "Player dataset successfully validated and activated.",
            "data": data_manager.get_data_quality_report(),
        })
    except Exception as e:
        logger.error("Player upload validation failed: %s", e)
        # Clean up failed upload file if exists
        if target_path.exists():
            target_path.unlink()
        return jsonify({"success": False, "message": f"Dataset validation failed: {str(e)}"}), 400


@app.route("/api/upload/matches", methods=["POST"])
def upload_matches():
    """Validates and activates user uploaded matches CSV."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in upload request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "message": "No file selected."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Unsupported file format. Please upload a CSV file."}), 400

    filename = sanitize_filename(file.filename)
    target_path = config.UPLOADS_DIR / f"custom_matches_{filename}"

    try:
        file.save(target_path)
        data_manager.load_data(
            data_manager.default_players_path,
            target_path,
            source_name=data_manager.source_name,
            is_custom=True,
        )
        analytics_engine.set_data_manager(data_manager)
        chart_service.set_data_manager(data_manager)

        return jsonify({
            "success": True,
            "message": "Matches dataset successfully validated and activated.",
            "data": data_manager.get_data_quality_report(),
        })
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        return jsonify({"success": False, "message": f"Matches validation failed: {str(e)}"}), 400


@app.route("/api/dataset/reset", methods=["POST"])
def reset_dataset():
    """Restores the bundled synthetic demo datasets."""
    try:
        data_manager.reset_to_default()
        analytics_engine.set_data_manager(data_manager)
        comparison_engine.set_data_manager(data_manager)
        insights_engine.set_data_manager(data_manager)
        chart_service.set_data_manager(data_manager)

        return jsonify({
            "success": True,
            "message": "Dataset successfully reset to verified demo statistics.",
            "source": data_manager.source_name,
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# --------------------------------------------------------------------------
# Global Error Handlers
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"success": False, "message": "Resource or endpoint not found."}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "An internal server error occurred."}), 500


# --------------------------------------------------------------------------
# Bootstrap & Safe Port Binding
# --------------------------------------------------------------------------
def find_available_port(start_port: int = 5002) -> int:
    """Finds the lowest free port starting at start_port to prevent macOS AirPlay conflicts."""
    port = start_port
    while port < start_port + 20:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            port += 1
    return start_port


if __name__ == "__main__":
    port = int(os.environ.get("PORT", find_available_port(config.DEFAULT_PORT)))
    logger.info("Starting Touchline Analytics on http://127.0.0.1:%s", port)
    app.run(host="127.0.0.1", port=port, debug=config.DEBUG)
