"""Energy Demand Forecasting & Optimization Web Application.
Flask REST API and dashboard server for time-series forecasting, machine learning comparisons,
and constrained flexible load optimization.
"""

from pathlib import Path
import os
import json
import logging
from typing import Dict, Any, List

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
    send_file,
)
import numpy as np
import pandas as pd

import config
from services.data_service import DataService
from services.preprocessing import PreprocessingPipeline
from services.forecasting import ForecastingEngine
from services.weather_service import WeatherService
from services.optimization import FlexibleLoadOptimizer
from services.evaluation import ModelEvaluator
from services.report_service import ReportService

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
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize Domain Services
data_service = DataService()
forecasting_engine = ForecastingEngine()
weather_service = WeatherService()
optimizer = FlexibleLoadOptimizer()

# In-memory / Instance experiment history
EXPERIMENTS_FILE = config.INSTANCE_DIR / "experiments.json"
if not EXPERIMENTS_FILE.exists():
    EXPERIMENTS_FILE.write_text("[]")


def load_experiments_list() -> List[Dict[str, Any]]:
    try:
        return json.loads(EXPERIMENTS_FILE.read_text())
    except Exception:
        return []


def save_experiment_record(record: Dict[str, Any]) -> None:
    history = load_experiments_list()
    history.insert(0, record)
    EXPERIMENTS_FILE.write_text(json.dumps(history[:100], indent=2))


# --------------------------------------------------------------------------
# Frontend Dashboard Route
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the main Energy Intelligence dashboard."""
    return render_template("index.html")


# --------------------------------------------------------------------------
# REST API: Health & Dataset Endpoints
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def api_health():
    """Returns application status and active dataset state."""
    active_meta = data_service.get_active_meta()
    return jsonify({
        "status": "healthy",
        "app_name": "Energy Intelligence",
        "version": "1.0.0",
        "dataset_loaded": active_meta["is_loaded"],
        "active_source": active_meta["source_name"],
        "row_count": active_meta["row_count"],
        "port": config.PORT,
    })


@app.route("/api/datasets/sample", methods=["GET"])
def api_datasets_sample():
    """Lists available pre-installed and sample datasets."""
    items = [
        {
            "id": "sample",
            "name": "Tetouan Calibrated Sample (60 Days @ 10-Min)",
            "description": "High-fidelity microclimate and tri-zone power readings calibrated to Tetouan.",
            "is_available": config.SAMPLE_DATASET_PATH.exists(),
        },
        {
            "id": "processed",
            "name": "Tetouan Hourly Aggregation (1-Hour Means)",
            "description": "Cleaned hourly arithmetic averages ready for immediate forecasting.",
            "is_available": config.PROCESSED_DATASET_PATH.exists(),
        },
    ]
    if config.RAW_DATASET_PATH.exists():
        items.insert(0, {
            "id": "raw",
            "name": "UCI Repository Tetouan City (Full Raw 2017)",
            "description": "Complete 52,416 observations across Zones 1, 2, and 3.",
            "is_available": True,
        })
    return jsonify({"success": True, "datasets": items})


@app.route("/api/dataset/summary", methods=["GET"])
def api_dataset_summary():
    """Returns quality diagnostics, summary statistics, and column inventory."""
    target_col = request.args.get("target")
    summary = data_service.get_summary(target_col=target_col)
    return jsonify(summary)


@app.route("/api/dataset/preview", methods=["GET"])
def api_dataset_preview():
    """Returns table preview records for the active dataset."""
    limit = int(request.args.get("limit", 15))
    preview = data_service.get_preview(n=limit)
    return jsonify({"success": True, **preview})


@app.route("/api/dataset/load-sample", methods=["POST"])
def api_dataset_load_sample():
    """Switches the active dataset to one of the bundled samples."""
    body = request.get_json(silent=True) or {}
    sample_name = body.get("name", "sample")
    success, msg, _ = data_service.load_dataset_by_name(sample_name)
    if not success:
        return jsonify({"success": False, "error": msg}), 400
    summary = data_service.get_summary()
    return jsonify({"success": True, "message": msg, "summary": summary})


@app.route("/api/dataset/upload", methods=["POST"])
def api_dataset_upload():
    """Validates and ingests an uploaded CSV file."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file field in request."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "Empty filename submitted."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Only CSV files are supported."}), 400

    content = file.read()
    success, msg, summary = data_service.process_uploaded_csv(content, file.filename)
    if not success:
        return jsonify({"success": False, "error": msg}), 400

    return jsonify({"success": True, "message": msg, "summary": summary})


# --------------------------------------------------------------------------
# REST API: Demand Patterns & Anomaly Analytics
# --------------------------------------------------------------------------
@app.route("/api/patterns", methods=["GET"])
def api_patterns():
    """Aggregates historical demand profiles, 24x7 heatmap matrix, and weather correlations."""
    df = data_service.get_active_dataframe()
    if df is None or df.empty:
        return jsonify({"success": False, "error": "No active dataset loaded."}), 400

    target = request.args.get("target") or data_service.get_active_meta()["target_column"]
    if target not in df.columns:
        target = config.DEFAULT_TARGET_COLUMN if config.DEFAULT_TARGET_COLUMN in df.columns else df.columns[-1]

    # Preprocess to hourly
    preprocessor = PreprocessingPipeline(target_column=target)
    hourly_df, _ = preprocessor.clean_and_resample(df, target_col=target)

    dt = pd.to_datetime(hourly_df["DateTime"])
    hourly_df["hour"] = dt.dt.hour
    hourly_df["dayofweek"] = dt.dt.dayofweek
    hourly_df["day_name"] = dt.dt.day_name()
    hourly_df["is_weekend"] = hourly_df["dayofweek"] >= 5

    # 1. Hourly average profile (Weekday vs Weekend)
    hourly_profile = []
    for h in range(24):
        sub_wd = hourly_df[(hourly_df["hour"] == h) & (~hourly_df["is_weekend"])][target]
        sub_we = hourly_df[(hourly_df["hour"] == h) & (hourly_df["is_weekend"])][target]
        hourly_profile.append({
            "hour": h,
            "hour_label": f"{h:02d}:00",
            "weekday_avg": round(float(sub_wd.mean()), 1) if not sub_wd.empty else 0.0,
            "weekend_avg": round(float(sub_we.mean()), 1) if not sub_we.empty else 0.0,
            "overall_avg": round(float(hourly_df[hourly_df["hour"] == h][target].mean()), 1),
        })

    # 2. 7x24 Demand Heatmap Matrix (Day of Week vs Hour)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_matrix = []
    for d_idx, d_name in enumerate(day_order):
        row_vals = []
        for h in range(24):
            val = hourly_df[(hourly_df["dayofweek"] == d_idx) & (hourly_df["hour"] == h)][target].mean()
            row_vals.append(round(float(val), 1) if pd.notnull(val) else 0.0)
        heatmap_matrix.append({
            "day": d_name,
            "day_index": d_idx,
            "hourly_demand": row_vals,
        })

    # 3. Weather-demand correlation scatter points (if temperature column present)
    weather_scatter = []
    if "Temperature" in hourly_df.columns:
        sample_subset = hourly_df.sample(min(300, len(hourly_df)), random_state=42)
        for _, row in sample_subset.iterrows():
            weather_scatter.append({
                "temperature": round(float(row["Temperature"]), 1),
                "demand": round(float(row[target]), 1),
                "hour": int(row["hour"]),
            })

    return jsonify({
        "success": True,
        "target": target,
        "hourly_profile": hourly_profile,
        "heatmap": {
            "days": day_order,
            "hours": [f"{h:02d}:00" for h in range(24)],
            "matrix": heatmap_matrix,
        },
        "weather_relationship": weather_scatter,
    })


@app.route("/api/anomalies", methods=["GET"])
def api_anomalies():
    """Screens active dataset for peak consumption periods and statistical anomalies."""
    df = data_service.get_active_dataframe()
    if df is None or df.empty:
        return jsonify({"success": False, "error": "No dataset loaded."}), 400

    target = request.args.get("target") or data_service.get_active_meta()["target_column"]
    threshold_param = request.args.get("threshold")
    threshold = float(threshold_param) if threshold_param else None

    preprocessor = PreprocessingPipeline(target_column=target)
    hourly_df, _ = preprocessor.clean_and_resample(df, target_col=target)

    ts_list = hourly_df["DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    values = hourly_df[target].values

    diag = ModelEvaluator.detect_peaks_and_anomalies(ts_list, values, threshold=threshold)
    return jsonify({"success": True, "target": target, **diag})


# --------------------------------------------------------------------------
# REST API: Open-Meteo Weather Integration
# --------------------------------------------------------------------------
@app.route("/api/weather", methods=["GET"])
def api_weather():
    """Returns cached Open-Meteo forecast observations with offline fallback."""
    lat = float(request.args.get("latitude", config.DEFAULT_LATITUDE))
    lon = float(request.args.get("longitude", config.DEFAULT_LONGITUDE))
    tz = request.args.get("timezone", config.DEFAULT_TIMEZONE)
    refresh = request.args.get("refresh", "false").lower() == "true"

    weather = weather_service.get_forecast(latitude=lat, longitude=lon, timezone=tz, force_refresh=refresh)
    return jsonify(weather)


# --------------------------------------------------------------------------
# REST API: Machine Learning Training & Forecasting
# --------------------------------------------------------------------------
@app.route("/api/forecast/train", methods=["POST"])
def api_forecast_train():
    """Trains selected models chronologically and returns leaderboard comparison."""
    df = data_service.get_active_dataframe()
    if df is None or df.empty:
        return jsonify({"success": False, "error": "No active dataset loaded."}), 400

    body = request.get_json(silent=True) or {}
    target_col = body.get("target_column") or data_service.get_active_meta()["target_column"]
    model_keys = body.get("model_keys")  # e.g., ['seasonal_naive', 'ridge', 'random_forest', 'hist_gradient_boosting']
    include_weather = body.get("include_weather", True)

    try:
        results = forecasting_engine.train_and_compare(
            df=df,
            target_col=target_col,
            model_keys=model_keys,
            include_weather=include_weather,
        )

        # Record experiment
        save_experiment_record({
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": target_col,
            "best_model": results["best_model"],
            "test_mae": results["test_metrics"]["mae"],
            "test_rmse": results["test_metrics"]["rmse"],
            "test_wape": results["test_metrics"]["wape"],
            "models_tested": list(results["arena_results"].keys()),
        })

        return jsonify(results)

    except Exception as exc:
        logger.error(f"Error training models: {exc}", exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/forecast/predict", methods=["POST"])
def api_forecast_predict():
    """Generates recursive 24-hour future energy forecast."""
    df = data_service.get_active_dataframe()
    if df is None or df.empty:
        return jsonify({"success": False, "error": "No active dataset loaded."}), 400

    body = request.get_json(silent=True) or {}
    horizon = int(body.get("horizon", config.DEFAULT_FORECAST_HORIZON))
    model_key = body.get("model_key")
    target_col = body.get("target_column") or data_service.get_active_meta()["target_column"]

    # Fetch future weather if enabled
    future_weather = None
    if body.get("use_weather_forecast", True):
        w_res = weather_service.get_forecast()
        if w_res.get("success"):
            future_weather = w_res.get("forecast_records")

    try:
        preds = forecasting_engine.generate_recursive_forecast(
            df=df,
            horizon=horizon,
            model_key=model_key,
            target_col=target_col,
            future_weather=future_weather,
        )
        return jsonify(preds)

    except Exception as exc:
        logger.error(f"Forecast generation failed: {exc}", exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/forecast/evaluate", methods=["POST"])
def api_forecast_evaluate():
    """Runs evaluation diagnostics on active model."""
    df = data_service.get_active_dataframe()
    if df is None:
        return jsonify({"success": False, "error": "No dataset loaded."}), 400

    target = data_service.get_active_meta()["target_column"]
    if not forecasting_engine.model_results:
        # Train default models
        res = forecasting_engine.train_and_compare(df, target_col=target)
    else:
        res = {
            "success": True,
            "best_model": forecasting_engine.best_model_key,
            "best_model_name": config.SUPPORTED_MODELS.get(forecasting_engine.best_model_key, "Selected Model"),
            "arena_results": forecasting_engine.model_results,
            "test_metrics": forecasting_engine.last_train_meta.get("test_metrics", {}),
        }
    return jsonify(res)


# --------------------------------------------------------------------------
# REST API: Constrained Flexible Load Optimization
# --------------------------------------------------------------------------
@app.route("/api/optimization/run", methods=["POST"])
def api_optimization_run():
    """Executes linear-programming flexible load shifting."""
    body = request.get_json(silent=True) or {}

    # Extract base demand or pull from latest 24h forecast / dataset
    base_demand = body.get("base_demand")
    if not base_demand or len(base_demand) != 24:
        # Pull latest 24 hours of target demand
        df = data_service.get_active_dataframe()
        if df is not None and not df.empty:
            target = data_service.get_active_meta()["target_column"]
            pre = PreprocessingPipeline(target_column=target)
            hourly_df, _ = pre.clean_and_resample(df, target_col=target)
            base_demand = hourly_df[target].tail(24).tolist()
        else:
            # Fallback illustrative base curve
            base_demand = [
                18000, 16000, 15000, 14500, 15000, 17000,
                22000, 27000, 31000, 33000, 32000, 31000,
                30000, 29000, 28000, 30000, 34000, 38000,
                42000, 44000, 41000, 35000, 26000, 20000,
            ]

    # Normalize base demand to kW if in raw watts (> 1000)
    base_demand = [round(b / 1000.0, 1) if b > 5000 else round(b, 1) for b in base_demand]

    required_energy = float(body.get("required_energy", config.OPTIMIZATION_DEFAULTS["required_energy"]))
    max_power = float(body.get("max_power", config.OPTIMIZATION_DEFAULTS["max_power"]))
    start_hour = int(body.get("start_hour", config.OPTIMIZATION_DEFAULTS["start_hour"]))
    end_hour = int(body.get("end_hour", config.OPTIMIZATION_DEFAULTS["end_hour"]))
    unavailable_hours = body.get("unavailable_hours", config.OPTIMIZATION_DEFAULTS["unavailable_hours"])
    tariffs = body.get("tariffs", config.DEFAULT_TOU_TARIFF)
    objective = body.get("objective", "balanced")
    peak_penalty = float(body.get("peak_penalty_weight", config.OPTIMIZATION_DEFAULTS["peak_penalty_weight"]))

    try:
        opt_results = optimizer.solve(
            base_demand=base_demand,
            required_energy=required_energy,
            max_power=max_power,
            start_hour=start_hour,
            end_hour=end_hour,
            unavailable_hours=unavailable_hours,
            tariffs=tariffs,
            objective_type=objective,
            peak_penalty_weight=peak_penalty,
        )
        return jsonify(opt_results)

    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 400
    except Exception as exc:
        logger.error(f"Optimization execution failed: {exc}", exc_info=True)
        return jsonify({"success": False, "error": str(exc)}), 500


# --------------------------------------------------------------------------
# REST API: Experiments & Report Export
# --------------------------------------------------------------------------
@app.route("/api/experiments", methods=["GET", "POST"])
def api_experiments():
    """Retrieves or logs experiment runs."""
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        save_experiment_record(body)
        return jsonify({"success": True, "message": "Experiment saved."})

    return jsonify({"success": True, "experiments": load_experiments_list()})


@app.route("/api/reports/export", methods=["POST"])
def api_reports_export():
    """Generates and downloads an HTML or CSV report."""
    body = request.get_json(silent=True) or {}
    report_type = body.get("type", "html").lower()

    dataset_meta = data_service.get_active_meta()
    model_res = {
        "best_model": forecasting_engine.best_model_key,
        "best_model_name": config.SUPPORTED_MODELS.get(forecasting_engine.best_model_key, "Selected Model"),
        "arena_results": forecasting_engine.model_results,
        "test_metrics": forecasting_engine.last_train_meta.get("test_metrics", {}),
    }

    forecast_res = body.get("forecast_results")
    optimization_res = body.get("optimization_results")

    if report_type == "csv":
        series = (forecast_res or {}).get("forecast_series", [])
        csv_data = ReportService.export_forecast_csv(series)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=energy_forecast_24h.csv"},
        )

    # HTML Report
    html_content = ReportService.generate_html_report(
        dataset_meta=dataset_meta,
        model_results=model_res,
        forecast_results=forecast_res,
        optimization_results=optimization_res,
    )

    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "attachment;filename=energy_intelligence_report.html"},
    )


# --------------------------------------------------------------------------
# Application Entrypoint
# --------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Starting Energy Demand Forecasting & Optimization on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
