# Weekly Documentation Index — MovieScope (W3-4)

> **Project:** MovieScope — Movie Ratings & Recommendation Explorer  
> **Module:** Weeks 3–4 of Hack-o-Week  
> **Stack:** Python · Flask · Pandas · Matplotlib · Seaborn · Vanilla CSS · JavaScript  

---

## Documented Weeks

| Week | Date Range | Date Confidence | Main Work | Status | README | Report |
|---|---|---|---|---|---|---|
| Week 01 | Oct 11, 2026, ~21:33–21:55 IST (estimated) | Estimated — single session | Full MovieScope application: data pipeline, analytics engine, cosine-similarity recommender, pre-generated charts, 16-endpoint REST API, SPA frontend, 27 passing tests | ✅ Completed | [README](Week-01/README.md) | [PDF](Week-01/Week-01-Report.pdf) |

---

## Total Progress Summary

### Completed
- ✅ `DataManager`: movies + ratings CSV loading, merged stats, data quality report
- ✅ `AnalyticsEngine`: genre distribution, rating distribution, rating-vs-popularity scatter, yearly trends, correlation heatmap (all as Matplotlib/Seaborn PNGs)
- ✅ `MovieRecommender`: cosine similarity on user–movie pivot table, top-N recommendations
- ✅ Flask REST API with 16 endpoints (movie list/search/filter, recommendations, analytics, data quality, export, upload, reset)
- ✅ SPA frontend with tab-based navigation (Dashboard, Explorer, Recommendations, Analytics, Trends, Data Quality)
- ✅ CSV data generation script
- ✅ 27/27 unit and integration tests passing

### Not Implemented / Limitations
- ❌ Interactive (Plotly.js) charts — current charts are static server-rendered PNGs
- ❌ Charts do not auto-update after custom CSV upload without server restart
- ❌ Advanced recommendation algorithms (matrix factorisation / SVD)
- ❌ Pagination controls in the movie explorer
- ❌ User authentication or personalisation

---

## File Links

- [Week-01 README](Week-01/README.md)
- [Week-01 PDF Report](Week-01/Week-01-Report.pdf)
- [Week-01 Screenshots](Week-01/screenshots/)

---

*Generated: October 11, 2026*
