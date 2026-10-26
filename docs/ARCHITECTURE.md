# Architecture (notes for the tech-lead walkthrough)

```
Elexon API --(fetch_data.py, run once)--> data/*.csv --> FastAPI (analysis.py) --> React UI
```

- **Why CSV snapshots?** Scope is fixed to January 2026, so data never changes. The deployed app is fast, free of Elexon rate limits/outages, and results are reproducible.
- **config.py**: all assumptions (cutoff hour, timezone, date scope) in one place.
- **analysis.py**: pure functions on DataFrames, unit-tested.
  - `latest_forecast_for_day`: keeps forecasts with `publishTime <= cutoff` (D-1 09:00 UK), takes the newest per half-hour. No look-ahead.
  - `metrics`: MAE, RMSE, bias, P90 absolute error, plus P90 over/under-forecast buffers.
  - `by_hour`, `by_horizon`, `daily`: breakdowns. By-horizon uses all forecasts (any age) to show how accuracy degrades with age.
- **main.py**: thin FastAPI layer; results cached in memory at first request. In Docker it also serves the React build, so one container = one deployment.
- **Frontend**: two views (Forecast, Accuracy), Recharts, one `api.js` helper.

## Assumptions to state in the video
1. Cutoff = 09:00 UK time on D-1 (configurable via `CUTOFF_HOUR`).
2. "Decisions made in January 2026" = delivery days 2 Jan to 1 Feb 2026.
3. Timestamps are UTC; UK local time equals UTC in January.
4. Error = forecast - actual (positive = forecast too high = risk of under-buying).
