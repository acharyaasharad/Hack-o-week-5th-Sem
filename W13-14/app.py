"""Ensemble Learning & Generalization Lab Flask Application.
Provides RESTful APIs for dataset exploration, leakage safeguards, model arena training,
bias-variance complexity sweeps, regularization experiments, and report generation.
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
from services.split_service import SplitService
from services.preprocessing_service import PreprocessingService
from services.model_registry import ModelRegistry
from services.training_service import TrainingService
from services.metrics_service import MetricsService
from services.generalization_service import GeneralizationService
from services.regularization_service import RegularizationService
from services.interpretation_service import InterpretationService
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

# Service Singletons
data_service = DataService()
training_service = TrainingService()
experiment_service = ExperimentService()

# Cached data splits to guarantee consistency across models
cached_splits: Dict[str, Any] = {}

def get_or_create_splits() -> Dict[str, Any]:
    global cached_splits
    df = data_service.get_active_df()
    if df is None:
        raise ValueError("No active dataset loaded.")
    if not cached_splits:
        cached_splits = SplitService.create_splits(
            df=df,
            target_column=data_service._target_column,
            feature_columns=data_service._feature_columns,
            task=data_service._task,
        )
    return cached_splits

# --------------------------------------------------------------------------
# Web & Health Endpoints
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page dashboard."""
    return render_template("index.html", app_name=config.APP_NAME, version=config.VERSION)

@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns application health, environment, and model dependencies status."""
    from services.model_registry import XGB_AVAILABLE, LGBM_AVAILABLE
    df = data_service.get_active_df()
    return jsonify({
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.VERSION,
        "active_dataset": data_service._dataset_name,
        "task": data_service._task,
        "rows_loaded": len(df) if df is not None else 0,
        "xgboost_available": XGB_AVAILABLE,
        "lightgbm_available": LGBM_AVAILABLE,
        "supported_models_count": len(ModelRegistry.get_supported_models(data_service._task)),
    })

# --------------------------------------------------------------------------
# Dataset Endpoints
# --------------------------------------------------------------------------
@app.route("/api/datasets", methods=["GET"])
def list_datasets():
    return jsonify({
        "datasets": [
            {"id": "bank_marketing", "name": "UCI Bank Marketing", "task": "classification", "description": "Predict term deposit subscription. Excludes 'duration' by default."},
            {"id": "bike_sharing", "name": "UCI Bike Sharing", "task": "regression", "description": "Predict hourly rental demand cnt. Excludes 'casual' & 'registered'."},
        ]
    })

@app.route("/api/dataset/load", methods=["POST"])
def load_dataset():
    global cached_splits
    payload = request.get_json(silent=True) or {}
    did = payload.get("dataset_id", "bank_marketing")

    if did == "bank_marketing":
        success = data_service.load_bank_marketing()
    elif did == "bike_sharing":
        success = data_service.load_bike_sharing()
    else:
        return jsonify({"success": False, "message": f"Unknown dataset ID '{did}'"}), 400

    cached_splits = {} # Invalidate cached splits
    summary = data_service.get_summary()
    return jsonify({"success": True, "message": f"Loaded {summary['dataset_name']}.", "summary": summary})

@app.route("/api/dataset/upload", methods=["POST"])
def upload_csv():
    global cached_splits
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file in request."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    success, msg, summary = data_service.load_user_csv(file, file.filename)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    cached_splits = {}
    return jsonify({"success": True, "message": msg, "summary": summary})

@app.route("/api/dataset/summary", methods=["GET"])
def get_dataset_summary():
    return jsonify(data_service.get_summary())

@app.route("/api/dataset/preview", methods=["GET"])
def get_dataset_preview():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 15))
    search = request.args.get("search", "").strip()
    return jsonify(data_service.get_preview(page=page, page_size=page_size, search=search))

@app.route("/api/dataset/configure", methods=["POST"])
def configure_task():
    global cached_splits
    payload = request.get_json(silent=True) or {}
    data_service._task = payload.get("task", data_service._task)
    data_service._target_column = payload.get("target_column", data_service._target_column)
    if "features" in payload:
        data_service._feature_columns = payload["features"]
    cached_splits = {}
    return jsonify({"success": True, "summary": data_service.get_summary()})

# --------------------------------------------------------------------------
# Model Arena & Training Endpoints
# --------------------------------------------------------------------------
@app.route("/api/models", methods=["GET"])
def get_available_models():
    models = ModelRegistry.get_supported_models(task=data_service._task)
    return jsonify({"models": models})

@app.route("/api/models/train", methods=["POST"])
def train_single_model():
    payload = request.get_json(silent=True) or {}
    model_id = payload.get("model_id", "decision_tree")
    params = payload.get("params", {})

    splits = get_or_create_splits()
    res = training_service.train_model(
        splits=splits,
        model_id=model_id,
        task=data_service._task,
        params=params,
    )
    return jsonify(res)

@app.route("/api/models/compare", methods=["POST"])
def compare_arena():
    payload = request.get_json(silent=True) or {}
    model_ids = payload.get("model_ids")
    splits = get_or_create_splits()
    results = training_service.compare_arena_models(
        splits=splits,
        task=data_service._task,
        model_ids=model_ids,
    )
    return jsonify({"leaderboard": results})

@app.route("/api/models/final-evaluate", methods=["POST"])
def evaluate_held_out_test():
    splits = get_or_create_splits()
    try:
        eval_res = training_service.evaluate_final_test(splits=splits)
        return jsonify(eval_res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/models/importance", methods=["GET"])
def get_feature_importance():
    res = InterpretationService.extract_feature_importance(training_service._last_fitted_pipeline)
    return jsonify(res)

# --------------------------------------------------------------------------
# Generalization & Regularization Labs
# --------------------------------------------------------------------------
@app.route("/api/generalization/complexity-sweep", methods=["POST"])
def complexity_sweep():
    payload = request.get_json(silent=True) or {}
    model_id = payload.get("model_id", "decision_tree")
    param_name = payload.get("param_name", "max_depth")
    param_values = payload.get("param_values", [1, 2, 3, 5, 8, 12, 16, 20])

    splits = get_or_create_splits()
    res = GeneralizationService.run_complexity_sweep(
        splits=splits,
        model_id=model_id,
        task=data_service._task,
        param_name=param_name,
        param_values=param_values,
    )
    return jsonify(res)

@app.route("/api/generalization/synthetic-demo", methods=["POST", "GET"])
def synthetic_demo():
    res = GeneralizationService.run_synthetic_demo()
    return jsonify(res)

@app.route("/api/regularization/sweep", methods=["POST"])
def regularization_sweep():
    payload = request.get_json(silent=True) or {}
    model_id = payload.get("model_id", "ridge" if data_service._task == "regression" else "logistic_l2")
    param_name = "alpha" if "ridge" in model_id or "lasso" in model_id else "C"
    strengths = payload.get("strengths", [0.01, 0.1, 1.0, 10.0, 100.0])

    splits = get_or_create_splits()
    res = RegularizationService.run_regularization_sweep(
        splits=splits,
        model_id=model_id,
        task=data_service._task,
        strength_param=param_name,
        strengths=strengths,
    )
    return jsonify(res)

# --------------------------------------------------------------------------
# Prediction Playground
# --------------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def predict_observation():
    if not training_service._last_fitted_pipeline:
        return jsonify({"error": "No model has been trained yet."}), 400

    payload = request.get_json(silent=True) or {}
    df_obs = pd.DataFrame([payload])

    pipeline = training_service._last_fitted_pipeline
    try:
        raw_pred = pipeline.predict(df_obs)[0]
        # Decode if label encoded
        if training_service._last_target_encoder:
            pred_class = training_service._last_target_encoder.inverse_transform([raw_pred])[0]
        else:
            pred_class = str(raw_pred)

        prob_dict = {}
        if hasattr(pipeline.named_steps["model"], "predict_proba"):
            probs = pipeline.predict_proba(df_obs)[0]
            classes = pipeline.named_steps["model"].classes_
            if training_service._last_target_encoder:
                classes = training_service._last_target_encoder.inverse_transform(classes)
            for c, p in zip(classes, probs):
                prob_dict[str(c)] = float(round(p, 4))

        return jsonify({
            "prediction": pred_class,
            "probabilities": prob_dict,
        })
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 400

# --------------------------------------------------------------------------
# Exports & Experiments Endpoints
# --------------------------------------------------------------------------
@app.route("/api/experiments", methods=["GET"])
def get_experiments():
    return jsonify(experiment_service.get_history())

@app.route("/api/export/comparison", methods=["GET"])
def export_comparison():
    csv_str = ExportService.export_comparison_csv(training_service._leaderboard)
    filename = f"model_arena_comparison_{int(time.time())}.csv"
    return Response(csv_str, mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={filename}"})

@app.route("/api/export/report", methods=["GET", "POST"])
def export_report():
    splits = get_or_create_splits()
    test_eval = None
    try:
        test_eval = training_service.evaluate_final_test(splits=splits)
    except Exception:
        pass

    best_m = training_service._leaderboard[0] if training_service._leaderboard else {}
    html_str = ExportService.generate_html_report(
        dataset_name=data_service._dataset_name,
        dataset_source=data_service._dataset_source,
        task=data_service._task,
        leaderboard=training_service._leaderboard,
        best_model=best_m,
        test_evaluation=test_eval,
    )
    filename = f"ensemble_generalization_report_{int(time.time())}.html"
    return Response(html_str, mimetype="text/html", headers={"Content-Disposition": f"attachment;filename={filename}"})

if __name__ == "__main__":
    logger.info("Starting Ensemble Learning & Generalization Lab on http://%s:%s", config.HOST, config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
