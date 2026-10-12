# Weekly Documentation Index — Energy Intelligence (W7-8)

> **Project:** Energy Intelligence — Demand Forecasting & Load Optimization Lab  
> **Module:** Weeks 7–8 of Hack-o-Week  
> **Stack:** Python · Flask · Pandas · scikit-learn · SciPy · Plotly.js · Vanilla CSS · JavaScript  

---

## Documented Weeks

| Week | Date Range | Date Confidence | Main Work | Status | README | Report |
|---|---|---|---|---|---|---|
| Week 01 | Oct 11, 2026, ~23:05–23:21 IST (estimated) | Estimated — single session split by milestone | Config, data pipeline, preprocessing (chronological 70/15/15 split), feature engineering (cyclical + lag), 4 ML models, evaluation metrics, weather API client, 5 test files (23 tests) | ✅ Completed | [README](Week-01/README.md) | [PDF](Week-01/Week-01-Report.pdf) |
| Week 02 | Oct 11, 2026, ~23:11–23:27 IST (estimated) | Estimated — same session, later files | Flask REST API (16 endpoints), SciPy linprog optimization engine, report service, complete SPA frontend (10 views), design system CSS, 5 JS modules | ✅ Completed | [README](Week-02/README.md) | [PDF](Week-02/Week-02-Report.pdf) |

---

## Total Progress Summary

### Completed (Across Both Weeks)

**Backend Infrastructure (Week 01)**
- ✅ `config.py`: All constants, TOU tariff, theme palette, ML params
- ✅ `scripts/prepare_data.py`: 8,640-row synthetic 10-min dataset → 1,440-row hourly
- ✅ `scripts/download_data.py`: UCI Dataset 849 download with offline fallback
- ✅ `services/data_service.py`: Thread-safe dataset caching, multi-source switching
- ✅ `services/preprocessing.py`: Dedup, interpolation, hourly resample, chronological split
- ✅ `services/feature_engineering.py`: Calendar, cyclical (sin/cos), lag (1/2/24/48/168h), rolling stats
- ✅ `services/forecasting.py`: Seasonal Naive, Ridge, Random Forest, HistGradientBoosting + recursive 24h
- ✅ `services/evaluation.py`: MAE, RMSE, WAPE, MAPE, R², hourly breakdown, anomaly z-scores
- ✅ `services/weather_service.py`: Open-Meteo API + 1-hour TTL cache + offline fallback
- ✅ 23/23 pytest tests passing

**API, Optimization & Frontend (Week 02)**
- ✅ `app.py`: 16 Flask REST endpoints, experiment history, error schema
- ✅ `services/optimization.py`: SciPy linprog LP — 3 scenarios (baseline, cost-focused, balanced), energy conservation, power cap, forbidden hours, feasibility pre-check
- ✅ `services/report_service.py`: HTML executive report, CSV forecast export
- ✅ `templates/index.html`: 10-view SPA with hash routing
- ✅ `static/css/style.css`: White/teal/emerald design system — NO purple gradients
- ✅ `static/js/app.js`, `charts.js`, `dataset.js`, `forecast.js`, `optimization.js`

### Not Fully Implemented / Known Limitations
- ⚠️ UCI Dataset 849 unavailable (server 404); offline sample data used automatically
- ⚠️ HistGradientBoosting artifact not confirmed saved in this browser session
- ❌ Optimization results are not persisted between page refreshes
- ❌ Live weather features are not automatically injected into the trained model's input
- ❌ HTML report export not verified to open in a PDF viewer

---

## File Links

| Week | README | PDF | Screenshots |
|---|---|---|---|
| Week 01 | [README](Week-01/README.md) | [Week-01-Report.pdf](Week-01/Week-01-Report.pdf) | [screenshots/](Week-01/screenshots/) |
| Week 02 | [README](Week-02/README.md) | [Week-02-Report.pdf](Week-02/Week-02-Report.pdf) | [screenshots/](Week-02/screenshots/) |

---

*Generated: October 11, 2026*
