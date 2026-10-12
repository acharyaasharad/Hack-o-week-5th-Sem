"""Customer Segmentation & Intelligence Dashboard — Flask Web Application.
Provides RESTful APIs for dataset ingestion, preprocessing, scikit-learn clustering,
interactive Plotly visualizations, customer exploration, and report exports.
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
from services.data_service import DataService
from services.preprocessing import PreprocessingService
from services.clustering_service import ClusteringService
from services.evaluation_service import EvaluationService
from services.profiling_service import ProfilingService
from services.visualization_service import VisualizationService
from services.export_service import ExportService

# --------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Flask Application Setup
# --------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder=str(config.STATIC_DIR),
    template_folder=str(config.TEMPLATES_DIR),
)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
CORS(app)

# Service Singletons for workspace session
data_service = DataService()
clustering_service = ClusteringService()

# In-memory / persistent experiment run history
experiments_history: List[Dict[str, Any]] = []

def _load_experiments_history():
    global experiments_history
    if config.EXPERIMENTS_FILE.exists():
        try:
            with open(config.EXPERIMENTS_FILE, "r") as f:
                experiments_history = json.load(f)
        except Exception as e:
            logger.warning("Failed to load experiments history: %s", e)
            experiments_history = []

def _save_experiments_history():
    try:
        with open(config.EXPERIMENTS_FILE, "w") as f:
            json.dump(experiments_history, f, indent=2)
    except Exception as e:
        logger.warning("Failed to persist experiments history: %s", e)

_load_experiments_history()

# --------------------------------------------------------------------------
# Core Web Route
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page Customer Segmentation dashboard."""
    return render_template("index.html", app_name=config.APP_NAME, version=config.VERSION)

# --------------------------------------------------------------------------
# System Health & Info
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns application health and environment details."""
    active_df = data_service.get_active_df()
    return jsonify({
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.VERSION,
        "active_dataset": data_service._dataset_name,
        "rows_loaded": len(active_df) if active_df is not None else 0,
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "python_framework": "Flask & scikit-learn",
        "supported_algorithms": list(config.SUPPORTED_ALGORITHMS.keys()),
    })

# --------------------------------------------------------------------------
# Dataset Ingestion & Metadata Endpoints
# --------------------------------------------------------------------------
@app.route("/api/dataset/sample", methods=["GET"])
def load_sample():
    """Loads either the official UCI dataset or synthetic fallback."""
    use_synthetic = request.args.get("synthetic", "false").lower() == "true"
    if use_synthetic:
        success = data_service.load_sample_dataset()
    else:
        success = data_service.load_default_dataset()

    if not success:
        return jsonify({"success": False, "message": "Failed to load sample dataset"}), 500

    summary = data_service.get_summary()
    return jsonify({
        "success": True,
        "message": f"Loaded {summary['dataset_name']} ({summary['total_rows']} observations)",
        "summary": summary
    })

@app.route("/api/dataset/upload", methods=["POST"])
def upload_csv():
    """Validates and ingests user-uploaded CSV file."""
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file was selected."}), 400

    success, message, summary = data_service.load_user_csv(file, file.filename)
    if not success:
        return jsonify({"success": False, "message": message}), 400

    return jsonify({"success": True, "message": message, "summary": summary})

@app.route("/api/dataset/summary", methods=["GET"])
def get_dataset_summary():
    """Returns full metadata, missing values, duplicates, and column metrics."""
    return jsonify(data_service.get_summary())

@app.route("/api/dataset/preview", methods=["GET"])
def get_dataset_preview():
    """Returns paginated and searchable rows for table preview."""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 15))
    search = request.args.get("search", "").strip()
    return jsonify(data_service.get_preview(page=page, page_size=page_size, search=search))

@app.route("/api/dataset/validate", methods=["POST"])
def validate_features():
    """Validates selected feature configuration before model execution."""
    payload = request.get_json(silent=True) or {}
    numeric_features = payload.get("numeric_features", [])
    categorical_features = payload.get("categorical_features", [])
    id_column = payload.get("id_column")
    context_columns = payload.get("context_columns", [])
    log_transform = payload.get("log_transform", False)

    validation = data_service.validate_configuration(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        id_column=id_column,
        context_columns=context_columns,
        log_transform=log_transform,
    )
    return jsonify(validation)

# --------------------------------------------------------------------------
# Machine Learning Clustering Endpoints
# --------------------------------------------------------------------------
@app.route("/api/clustering/run", methods=["POST"])
def run_clustering():
    """Fits an end-to-end scikit-learn Pipeline and evaluates the discovered clusters."""
    payload = request.get_json(silent=True) or {}
    df = data_service.get_active_df()
    if df is None:
        return jsonify({"status": "error", "message": "No dataset is currently loaded."}), 400

    algorithm = payload.get("algorithm", "kmeans").lower()
    params = payload.get("params", {})
    numeric_features = payload.get("numeric_features") or data_service._feature_columns
    categorical_features = payload.get("categorical_features") or data_service._categorical_columns
    context_columns = payload.get("context_columns") or data_service._context_columns
    scaling_method = payload.get("scaling_method", "standard")
    log_transform = bool(payload.get("log_transform", False))
    numeric_impute_strategy = payload.get("numeric_impute_strategy", "median")

    # Validate configuration first
    val = data_service.validate_configuration(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        log_transform=log_transform,
    )
    if not val["valid"]:
        return jsonify({"status": "error", "message": "Validation failed.", "errors": val["errors"]}), 400

    try:
        result = clustering_service.fit_clustering_model(
            df=df,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            algorithm=algorithm,
            params=params,
            scaling_method=scaling_method,
            log_transform=log_transform,
            numeric_impute_strategy=numeric_impute_strategy,
        )

        # Generate cluster profiles in raw units
        labels = clustering_service.get_last_labels()
        profiles = ProfilingService.generate_cluster_profiles(
            df=df,
            labels=labels,
            numeric_features=numeric_features,
            context_columns=context_columns,
        )

        result["profiles"] = profiles

        # Record experiment history entry
        exp_entry = {
            "id": f"EXP-{len(experiments_history)+1:03d}",
            "timestamp": result["timestamp"],
            "dataset_name": data_service._dataset_name,
            "row_count": len(df),
            "algorithm": result["algorithm_name"],
            "parameters": result["parameters"],
            "cluster_count": result["cluster_count"],
            "noise_percentage": result["noise_percentage"],
            "metrics": result["metrics"],
            "execution_time_seconds": result["execution_time_seconds"],
        }
        experiments_history.insert(0, exp_entry)
        _save_experiments_history()

        return jsonify(result)
    except Exception as e:
        logger.error("Clustering run failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/clustering/results", methods=["GET"])
def get_clustering_results():
    """Returns the most recent clustering run results and profiles."""
    res = clustering_service.get_last_run()
    if not res:
        return jsonify({"status": "empty", "message": "No clustering model has been run yet."})
    
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    profiles = ProfilingService.generate_cluster_profiles(
        df=df,
        labels=labels,
        numeric_features=res["preprocessing"]["numeric_features"],
        context_columns=data_service._context_columns,
    )
    res_copy = dict(res)
    res_copy["profiles"] = profiles
    return jsonify(res_copy)

@app.route("/api/clustering/cluster/<int:cluster_id>", methods=["GET"])
def get_cluster_details(cluster_id: int):
    """Returns detailed records and profile for a specific cluster or noise (-1)."""
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    if df is None or labels is None:
        return jsonify({"error": "No clustering analysis has been performed yet."}), 400

    df_labeled = df.copy()
    df_labeled["_cluster"] = labels
    cluster_df = df_labeled[df_labeled["_cluster"] == cluster_id]

    if cluster_df.empty:
        return jsonify({"error": f"Cluster {cluster_id} has no records."}), 404

    # Pagination for cluster records
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    start = (page - 1) * page_size
    records = cluster_df.iloc[start:start+page_size].to_dict(orient="records")

    return jsonify({
        "cluster_id": cluster_id,
        "is_noise": cluster_id == -1,
        "total_count": len(cluster_df),
        "page": page,
        "page_size": page_size,
        "records": records,
    })

@app.route("/api/clustering/customers", methods=["GET"])
def search_customers():
    """Allows searching and filtering customer observations by spend and cluster."""
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    if df is None:
        return jsonify({"error": "No dataset loaded."}), 400

    df_out = df.copy()
    if labels is not None and len(labels) == len(df_out):
        df_out["_cluster"] = labels
    else:
        df_out["_cluster"] = None

    cluster_filter = request.args.get("cluster")
    if cluster_filter is not None and cluster_filter != "":
        try:
            c_val = int(cluster_filter)
            df_out = df_out[df_out["_cluster"] == c_val]
        except ValueError:
            pass

    search_query = request.args.get("search", "").strip()
    if search_query:
        mask = df_out.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
        df_out = df_out[mask]

    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 15))
    start = (page - 1) * page_size
    end = start + page_size

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total_records": len(df_out),
        "data": df_out.iloc[start:end].to_dict(orient="records"),
    })

@app.route("/api/clustering/customer-lookup", methods=["POST"])
def lookup_new_customer():
    """Assigns an out-of-sample customer observation using fitted K-Means pipeline."""
    payload = request.get_json(silent=True) or {}
    res = clustering_service.predict_new_customer(payload)
    return jsonify(res)

@app.route("/api/clustering/elbow", methods=["GET"])
def get_elbow_curve():
    """Computes inertia and silhouette scores for K-Means k=2..10."""
    df = data_service.get_active_df()
    if df is None:
        return jsonify({"error": "No dataset loaded."}), 400

    k_min = int(request.args.get("k_min", 2))
    k_max = int(request.args.get("k_max", 10))
    scaling = request.args.get("scaling_method", "standard")
    log_tf = request.args.get("log_transform", "false").lower() == "true"

    elbow_data = clustering_service.compute_elbow_curve(
        df=df,
        numeric_features=data_service._feature_columns,
        k_min=k_min,
        k_max=k_max,
        scaling_method=scaling,
        log_transform=log_tf,
    )
    return jsonify(elbow_data)

@app.route("/api/clustering/compare", methods=["POST"])
def compare_models():
    """Executes a bounded benchmark comparison across K-Means, Hierarchical, and DBSCAN."""
    df = data_service.get_active_df()
    if df is None:
        return jsonify({"error": "No dataset loaded."}), 400

    payload = request.get_json(silent=True) or {}
    scaling = payload.get("scaling_method", "standard")
    log_tf = bool(payload.get("log_transform", False))

    comparison = clustering_service.compare_configurations(
        df=df,
        numeric_features=data_service._feature_columns,
        scaling_method=scaling,
        log_transform=log_tf,
    )
    return jsonify({"comparison": comparison})

@app.route("/api/clustering/dendrogram", methods=["GET"])
def get_dendrogram():
    """Calculates hierarchical tree leaf coordinates using SciPy."""
    df = data_service.get_active_df()
    if df is None:
        return jsonify({"available": False, "reason": "No dataset loaded."}), 400

    linkage_method = request.args.get("linkage", "ward")
    metric = request.args.get("metric", "euclidean")
    scaling = request.args.get("scaling_method", "standard")
    log_tf = request.args.get("log_transform", "false").lower() == "true"

    dendro = VisualizationService.compute_dendrogram_data(
        df=df,
        numeric_features=data_service._feature_columns,
        linkage_method=linkage_method,
        metric=metric,
        scaling_method=scaling,
        log_transform=log_tf,
    )
    return jsonify(dendro)

@app.route("/api/visualization/correlation", methods=["GET"])
def get_correlation():
    """Returns Pearson correlation matrix for numeric features."""
    df = data_service.get_active_df()
    if df is None:
        return jsonify({"columns": [], "z": []})
    return jsonify(VisualizationService.compute_correlation_heatmap(df, data_service._feature_columns))

# --------------------------------------------------------------------------
# Exports & Reporting
# --------------------------------------------------------------------------
@app.route("/api/export/clusters.csv", methods=["POST", "GET"])
def export_clusters_csv():
    """Exports full dataset with appended cluster labels."""
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    if df is None or labels is None:
        return jsonify({"error": "Please execute a clustering run before exporting data."}), 400

    csv_data = ExportService.export_labeled_dataset_csv(df, labels)
    filename = f"customer_clusters_{int(time.time())}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route("/api/export/profiles.csv", methods=["POST", "GET"])
def export_profiles_csv():
    """Exports cluster profiles and category spend means/medians."""
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    if df is None or labels is None:
        return jsonify({"error": "Please execute a clustering run before exporting profiles."}), 400

    profiles = ProfilingService.generate_cluster_profiles(
        df=df,
        labels=labels,
        numeric_features=data_service._feature_columns,
        context_columns=data_service._context_columns,
    )
    csv_data = ExportService.export_cluster_profiles_csv(profiles)
    filename = f"cluster_profiles_{int(time.time())}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route("/api/export/report.html", methods=["POST", "GET"])
def export_html_report():
    """Generates and downloads a self-contained executive HTML intelligence report."""
    res = clustering_service.get_last_run()
    df = data_service.get_active_df()
    labels = clustering_service.get_last_labels()
    if not res or df is None or labels is None:
        return jsonify({"error": "Run clustering analysis before generating the report."}), 400

    profiles = ProfilingService.generate_cluster_profiles(
        df=df,
        labels=labels,
        numeric_features=res["preprocessing"]["numeric_features"],
        context_columns=data_service._context_columns,
    )

    report_html = ExportService.generate_html_report(
        dataset_name=data_service._dataset_name,
        dataset_source=data_service._dataset_source,
        total_rows=len(df),
        features_used=res["preprocessing"]["numeric_features"],
        result=res,
        profiles=profiles,
    )
    filename = f"customer_segmentation_report_{int(time.time())}.html"
    return Response(
        report_html,
        mimetype="text/html",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# --------------------------------------------------------------------------
# Experiments History Endpoints
# --------------------------------------------------------------------------
@app.route("/api/experiments", methods=["GET"])
def get_experiments():
    """Returns history of recorded clustering runs."""
    return jsonify(experiments_history)

@app.route("/api/experiments", methods=["POST"])
def save_experiment():
    """Saves current run configuration into persistent history."""
    res = clustering_service.get_last_run()
    if not res:
        return jsonify({"error": "No recent run to save."}), 400

    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes", "")

    exp_entry = {
        "id": f"EXP-{len(experiments_history)+1:03d}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": notes,
        "dataset_name": data_service._dataset_name,
        "algorithm": res["algorithm_name"],
        "parameters": res["parameters"],
        "cluster_count": res["cluster_count"],
        "metrics": res["metrics"],
    }
    experiments_history.insert(0, exp_entry)
    _save_experiments_history()
    return jsonify({"success": True, "experiment": exp_entry})

# --------------------------------------------------------------------------
# Application Entrypoint
# --------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Customer Segmentation & Intelligence Dashboard on http://%s:%s", config.HOST, config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
