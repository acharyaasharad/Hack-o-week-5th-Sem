"""Dimensionality Reduction Visualizer — PCA & t-SNE Studio Flask Server.
Provides RESTful APIs for dataset ingestion, preprocessing pipelines,
PCA and t-SNE embeddings, side-by-side comparisons, and exports.
"""

from pathlib import Path
import os
import io
import json
import logging
import time
from typing import Dict, Any, List

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
    send_file,
)
from flask_cors import CORS
import pandas as pd
import numpy as np

import config
from services.dataset_service import DatasetService
from services.preprocessing_service import PreprocessingService
from services.dimensionality_service import DimensionalityService
from services.evaluation_service import EvaluationService
from services.experiment_service import ExperimentService
from services.export_service import ExportService

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder=str(config.STATIC_DIR),
    template_folder=str(config.TEMPLATES_DIR),
)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
CORS(app)

# Session / Service Singletons
dataset_service = DatasetService()
dim_service = DimensionalityService()
experiment_service = ExperimentService()

# --------------------------------------------------------------------------
# Web & Health Endpoints
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page PCA & t-SNE Studio dashboard."""
    return render_template("index.html", app_name=config.APP_NAME, version=config.VERSION)

@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns application health and configuration details."""
    active_df = dataset_service.get_active_df()
    return jsonify({
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.VERSION,
        "active_dataset": dataset_service._dataset_name,
        "rows_loaded": len(active_df) if active_df is not None else 0,
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "max_tsne_samples": config.MAX_TSNE_SAMPLES,
    })

# --------------------------------------------------------------------------
# Dataset Management Endpoints
# --------------------------------------------------------------------------
@app.route("/api/datasets", methods=["GET"])
def list_supported_datasets():
    """Lists built-in datasets available without file upload."""
    return jsonify({
        "datasets": [
            {
                "id": "wine",
                "name": "Wine Recognition Dataset (178 rows, 13 features)",
                "description": "Standard 3-class chemical analysis benchmark from UCI ML Repository.",
            },
            {
                "id": "iris",
                "name": "Iris Flower Dataset (150 rows, 4 features)",
                "description": "Classic 3-species morphological measurement benchmark.",
            },
            {
                "id": "sample",
                "name": "Synthetic Multi-Cluster Sample (200 rows, 8 features)",
                "description": "Offline deterministic sample data with 3 distinct clusters.",
            },
        ]
    })

@app.route("/api/dataset/load", methods=["POST"])
def load_dataset():
    """Loads a chosen built-in dataset."""
    payload = request.get_json(silent=True) or {}
    dataset_id = payload.get("dataset_id", "wine")

    if dataset_id == "wine":
        success = dataset_service.load_wine_dataset()
    elif dataset_id == "iris":
        success = dataset_service.load_iris_dataset()
    elif dataset_id == "sample":
        success = dataset_service.load_sample_dataset()
    else:
        return jsonify({"success": False, "message": f"Unknown dataset ID '{dataset_id}'"}), 400

    if not success:
        return jsonify({"success": False, "message": "Failed to load requested dataset."}), 500

    summary = dataset_service.get_summary()
    return jsonify({"success": True, "message": f"Successfully loaded {summary['dataset_name']}.", "summary": summary})

@app.route("/api/dataset/upload", methods=["POST"])
def upload_csv():
    """Validates and loads a user-uploaded CSV file."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in upload request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    success, msg, summary = dataset_service.load_user_csv(file, file.filename)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    return jsonify({"success": True, "message": msg, "summary": summary})

@app.route("/api/dataset/summary", methods=["GET"])
def get_dataset_summary():
    """Returns active dataset statistics and quality warnings."""
    return jsonify(dataset_service.get_summary())

@app.route("/api/dataset/preview", methods=["GET"])
def get_dataset_preview():
    """Returns paginated, searchable preview rows."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 15))
    search = request.args.get("search", "").strip()
    return jsonify(dataset_service.get_preview(page=page, page_size=page_size, search=search))

# --------------------------------------------------------------------------
# Machine Learning Dimensionality Reduction Endpoints
# --------------------------------------------------------------------------
@app.route("/api/pca/run", methods=["POST"])
def run_pca():
    """Executes PCA dimensionality reduction."""
    df = dataset_service.get_active_df()
    if df is None:
        return jsonify({"status": "error", "message": "No dataset loaded."}), 400

    payload = request.get_json(silent=True) or {}
    features = payload.get("features") or dataset_service._feature_columns
    n_components = int(payload.get("n_components", 2))
    scaler = payload.get("scaler", "standard")
    log_transform = bool(payload.get("log_transform", False))
    color_by = payload.get("color_by") or dataset_service._color_column
    kmeans_overlay = bool(payload.get("kmeans_overlay", False))
    kmeans_k = int(payload.get("kmeans_k", 3))

    if len(features) < 2:
        return jsonify({"status": "error", "message": "Select at least 2 features for PCA."}), 400

    try:
        res = dim_service.run_pca(
            df=df,
            features=features,
            n_components=n_components,
            scaler=scaler,
            log_transform=log_transform,
            color_by=color_by,
            kmeans_overlay=kmeans_overlay,
            kmeans_k=kmeans_k,
        )

        # Log experiment
        experiment_service.log_run(
            method="pca",
            dataset_name=dataset_service._dataset_name,
            n_samples=len(df),
            n_features=len(features),
            config_params=res["configuration"],
            metrics={
                "pc1_variance": res["pc1_variance"],
                "pc2_variance": res["pc2_variance"],
                "total_2d_variance": res["total_2d_variance"],
                "reconstruction_error": res["reconstruction_error"],
                "trustworthiness": res["trustworthiness"],
            },
            exec_time=res["execution_time_seconds"],
        )

        return jsonify(res)
    except Exception as e:
        logger.error("PCA run failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tsne/run", methods=["POST"])
def run_tsne():
    """Executes t-SNE dimensionality reduction."""
    df = dataset_service.get_active_df()
    if df is None:
        return jsonify({"status": "error", "message": "No dataset loaded."}), 400

    payload = request.get_json(silent=True) or {}
    features = payload.get("features") or dataset_service._feature_columns
    perplexity = float(payload.get("perplexity", 30.0))
    learning_rate = payload.get("learning_rate", "auto")
    max_iter = int(payload.get("max_iter", 1000))
    scaler = payload.get("scaler", "standard")
    log_transform = bool(payload.get("log_transform", False))
    color_by = payload.get("color_by") or dataset_service._color_column
    kmeans_overlay = bool(payload.get("kmeans_overlay", False))
    kmeans_k = int(payload.get("kmeans_k", 3))

    if len(features) < 2:
        return jsonify({"status": "error", "message": "Select at least 2 features for t-SNE."}), 400

    try:
        res = dim_service.run_tsne(
            df=df,
            features=features,
            perplexity=perplexity,
            learning_rate=learning_rate,
            max_iter=max_iter,
            scaler=scaler,
            log_transform=log_transform,
            color_by=color_by,
            kmeans_overlay=kmeans_overlay,
            kmeans_k=kmeans_k,
        )

        # Log experiment
        experiment_service.log_run(
            method="tsne",
            dataset_name=dataset_service._dataset_name,
            n_samples=res["n_samples"],
            n_features=len(features),
            config_params=res["configuration"],
            metrics={
                "perplexity": res["perplexity"],
                "kl_divergence": res["kl_divergence"],
                "trustworthiness": res["trustworthiness"],
            },
            exec_time=res["execution_time_seconds"],
        )

        return jsonify(res)
    except Exception as e:
        logger.error("t-SNE run failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/compare/run", methods=["POST"])
def run_comparison():
    """Executes PCA and t-SNE on a single aligned common observation sample."""
    df = dataset_service.get_active_df()
    if df is None:
        return jsonify({"status": "error", "message": "No dataset loaded."}), 400

    payload = request.get_json(silent=True) or {}
    features = payload.get("features") or dataset_service._feature_columns
    perplexity = float(payload.get("perplexity", 30.0))
    scaler = payload.get("scaler", "standard")
    log_transform = bool(payload.get("log_transform", False))
    color_by = payload.get("color_by") or dataset_service._color_column

    try:
        res = dim_service.run_comparison(
            df=df,
            features=features,
            perplexity=perplexity,
            scaler=scaler,
            log_transform=log_transform,
            color_by=color_by,
        )
        return jsonify(res)
    except Exception as e:
        logger.error("Comparison run failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/point/<string:row_id>", methods=["GET"])
def inspect_point(row_id: str):
    """Retrieves full original feature values and available embedding coordinates for a single observation."""
    df = dataset_service.get_active_df()
    if df is None:
        return jsonify({"error": "No dataset loaded."}), 400

    match_row = df[df["_row_id"] == row_id]
    if match_row.empty:
        return jsonify({"error": f"Observation '{row_id}' not found."}), 404

    row_dict = match_row.iloc[0].to_dict()

    # Look up coordinates in last PCA / t-SNE runs
    pca_coord = None
    if dim_service._last_pca_result:
        for c in dim_service._last_pca_result.get("coordinates", []):
            if c["row_id"] == row_id:
                pca_coord = c
                break

    tsne_coord = None
    if dim_service._last_tsne_result:
        for c in dim_service._last_tsne_result.get("coordinates", []):
            if c["row_id"] == row_id:
                tsne_coord = c
                break

    return jsonify({
        "row_id": row_id,
        "features": {k: v for k, v in row_dict.items() if k != "_row_id"},
        "pca_coordinates": pca_coord,
        "tsne_coordinates": tsne_coord,
    })

# --------------------------------------------------------------------------
# Experiments & Export Endpoints
# --------------------------------------------------------------------------
@app.route("/api/experiments", methods=["GET"])
def get_experiments():
    return jsonify(experiment_service.get_history())

@app.route("/api/export/pca.csv", methods=["GET"])
def export_pca_csv():
    if not dim_service._last_pca_result:
        return jsonify({"error": "Execute PCA before exporting coordinates."}), 400
    csv_str = ExportService.export_pca_csv(dim_service._last_pca_result)
    filename = f"pca_coordinates_{int(time.time())}.csv"
    return Response(csv_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route("/api/export/tsne.csv", methods=["GET"])
def export_tsne_csv():
    if not dim_service._last_tsne_result:
        return jsonify({"error": "Execute t-SNE before exporting coordinates."}), 400
    csv_str = ExportService.export_tsne_csv(dim_service._last_tsne_result)
    filename = f"tsne_coordinates_{int(time.time())}.csv"
    return Response(csv_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route("/api/export/combined.csv", methods=["GET"])
def export_combined_csv():
    if not dim_service._last_compare_result:
        return jsonify({"error": "Execute comparison before exporting combined results."}), 400
    csv_str = ExportService.export_combined_csv(dim_service._last_compare_result)
    filename = f"aligned_dimensionality_embeddings_{int(time.time())}.csv"
    return Response(csv_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route("/api/export/loadings.csv", methods=["GET"])
def export_loadings_csv():
    if not dim_service._last_pca_result:
        return jsonify({"error": "Execute PCA before exporting loadings."}), 400
    csv_str = ExportService.export_loadings_csv(dim_service._last_pca_result)
    filename = f"pca_component_loadings_{int(time.time())}.csv"
    return Response(csv_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route("/api/export/report", methods=["GET", "POST"])
def export_report():
    df = dataset_service.get_active_df()
    if df is None:
        return jsonify({"error": "No dataset loaded."}), 400

    html_str = ExportService.generate_html_report(
        dataset_name=dataset_service._dataset_name,
        dataset_source=dataset_service._dataset_source,
        total_rows=len(df),
        pca_result=dim_service._last_pca_result,
        tsne_result=dim_service._last_tsne_result,
    )
    filename = f"dimensionality_reduction_report_{int(time.time())}.html"
    return Response(html_str, mimetype="text/html", headers={"Content-Disposition": f"attachment;filename={filename}"})

if __name__ == "__main__":
    logger.info("Starting PCA & t-SNE Studio on http://%s:%s", config.HOST, config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
