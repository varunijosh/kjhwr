"""FastAPI app: JSON API under /api, and (in Docker) the built React app at /."""
from datetime import date
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import analysis, config, data

app = FastAPI(title="Wind Forecast Portal API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@lru_cache
def state():
    try:
        fc, act = data.load_forecasts(), data.load_actuals()
    except data.DataNotFound as e:
        raise HTTPException(503, str(e))
    days = config.delivery_days()
    dec = analysis.decision_table(fc, act, days)
    allf = analysis.horizon_table(fc, act, days)
    return {"dec": dec, "all": allf, "days": days}


def _iso(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    days = config.delivery_days()
    return {
        "timezone": config.TZ,
        "cutoff_hour_local": config.CUTOFF_HOUR,
        "decision_start": config.DECISION_START.isoformat(),
        "decision_end": config.DECISION_END.isoformat(),
        "delivery_days": [d.isoformat() for d in days],
        "data_source": data.data_source(),
    }


@app.get("/api/forecast")
def forecast(date: date):
    s = state()
    if date not in s["days"]:
        raise HTTPException(404, "Date outside the January 2026 decision scope")
    d = s["dec"][s["dec"].delivery_day == date]
    if d.empty:
        raise HTTPException(404, "No forecast available before the cutoff for this day")
    series = [
        {
            "time": _iso(r.startTime),
            "forecast": analysis._f(r.forecast),
            "actual": analysis._f(r.actual),
            "published": _iso(r.publishTime),
        }
        for r in d.itertuples()
    ]
    peak = d.loc[d.forecast.idxmax()]
    return {
        "delivery_day": date.isoformat(),
        "cutoff": _iso(d.cutoff.iloc[0]),
        "latest_publish_time": _iso(d.publishTime.max()),
        "summary": {
            "mean_forecast": analysis._f(d.forecast.mean()),
            "min_forecast": analysis._f(d.forecast.min()),
            "peak_forecast": analysis._f(peak.forecast),
            "peak_time": _iso(peak.startTime),
            "slots": int(len(d)),
        },
        "day_accuracy": analysis.metrics(d),
        "series": series,
    }


@app.get("/api/accuracy/summary")
def acc_summary():
    return analysis.metrics(state()["dec"])


@app.get("/api/accuracy/by-hour")
def acc_hour():
    return analysis.by_hour(state()["dec"])


@app.get("/api/accuracy/by-horizon")
def acc_horizon():
    return analysis.by_horizon(state()["all"])


@app.get("/api/accuracy/daily")
def acc_daily():
    return analysis.daily(state()["dec"])


# Serve the React build when present (Docker / Heroku single-container deploy).
if config.STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=config.STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = config.STATIC_DIR / path
        return FileResponse(f if path and f.is_file() else config.STATIC_DIR / "index.html")
