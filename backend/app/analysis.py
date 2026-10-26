"""Core logic. Pure functions on DataFrames so they are easy to test.

Key rule: for delivery day D, only forecasts with publishTime <= cutoff(D)
are allowed, where cutoff(D) = CUTOFF_HOUR (UK local) on D-1. For every
half-hour we use the most recently published of those forecasts.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import config


def local_day_bounds(day: date):
    s = pd.Timestamp(day.year, day.month, day.day, tz=config.TZ)
    nd = day + timedelta(days=1)
    e = pd.Timestamp(nd.year, nd.month, nd.day, tz=config.TZ)
    return s.tz_convert("UTC"), e.tz_convert("UTC")


def decision_cutoff(day: date, hour: int | None = None) -> pd.Timestamp:
    hour = config.CUTOFF_HOUR if hour is None else hour
    d1 = day - timedelta(days=1)
    return pd.Timestamp(d1.year, d1.month, d1.day, hour, tz=config.TZ).tz_convert("UTC")


def latest_forecast_for_day(fc: pd.DataFrame, day: date, hour: int | None = None) -> pd.DataFrame:
    """Latest forecast per half-hour that was available at decision time."""
    start, end = local_day_bounds(day)
    cutoff = decision_cutoff(day, hour)
    f = fc[(fc.startTime >= start) & (fc.startTime < end) & (fc.publishTime <= cutoff)]
    f = f.sort_values("publishTime").groupby("startTime").tail(1).sort_values("startTime").copy()
    f["delivery_day"] = day
    f["cutoff"] = cutoff
    f["horizon_h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
    return f


def _with_actuals(df: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
    a = act[["startTime", "generation"]].rename(columns={"generation": "actual"})
    df = df.rename(columns={"generation": "forecast"}).merge(a, on="startTime", how="left")
    df["error"] = df.forecast - df.actual  # + means forecast too high
    df["abs_error"] = df.error.abs()
    return df


def decision_table(fc: pd.DataFrame, act: pd.DataFrame, days: list[date], hour: int | None = None) -> pd.DataFrame:
    parts = [latest_forecast_for_day(fc, d, hour) for d in days]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast", "actual", "error", "abs_error", "delivery_day", "cutoff", "horizon_h"])
    return _with_actuals(pd.concat(parts, ignore_index=True), act)


def horizon_table(fc: pd.DataFrame, act: pd.DataFrame, days: list[date]) -> pd.DataFrame:
    """All forecasts (any publish time) for the delivery days, with their age."""
    start, _ = local_day_bounds(min(days))
    _, end = local_day_bounds(max(days))
    f = fc[(fc.startTime >= start) & (fc.startTime < end)].copy()
    f["horizon_h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
    f = f[f.horizon_h >= 0]
    return _with_actuals(f, act)


def _f(x):
    return None if x is None or pd.isna(x) else round(float(x), 2)


def metrics(df: pd.DataFrame) -> dict:
    d = df.dropna(subset=["forecast", "actual"])
    if d.empty:
        return {"n": 0}
    mae = d.abs_error.mean()
    mean_actual = d.actual.mean()
    return {
        "n": int(len(d)),
        "mae": _f(mae),
        "rmse": _f(np.sqrt((d.error ** 2).mean())),
        "bias": _f(d.error.mean()),
        "p90_abs_error": _f(d.abs_error.quantile(0.9)),
        "mean_actual": _f(mean_actual),
        "mae_pct_of_mean": _f(mae / mean_actual * 100) if mean_actual else None,
        # Buffers: MW by which the forecast was too high / too low in 90% of slots
        "over_forecast_p90": _f(max(0.0, d.error.quantile(0.9))),
        "under_forecast_p90": _f(max(0.0, -d.error.quantile(0.1))),
    }


def by_hour(df: pd.DataFrame) -> list[dict]:
    d = df.dropna(subset=["forecast", "actual"]).copy()
    d["hour"] = d.startTime.dt.tz_convert(config.TZ).dt.hour
    g = d.groupby("hour").agg(mae=("abs_error", "mean"), bias=("error", "mean"), n=("error", "size")).reset_index()
    return [{"hour": int(r.hour), "mae": _f(r.mae), "bias": _f(r.bias), "n": int(r.n)} for r in g.itertuples()]


def by_horizon(df: pd.DataFrame, width: int = 6) -> list[dict]:
    d = df.dropna(subset=["forecast", "actual"]).copy()
    if d.empty:
        return []
    top = int(np.ceil(d.horizon_h.max() / width) * width) + width
    bins = np.arange(0, top + 1, width)
    d["bin"] = pd.cut(d.horizon_h, bins=bins, right=False)
    g = d.groupby("bin", observed=True).agg(mae=("abs_error", "mean"), bias=("error", "mean"), n=("error", "size")).reset_index()
    return [
        {"label": f"{int(r.bin.left)}-{int(r.bin.right)}h", "mae": _f(r.mae), "bias": _f(r.bias), "n": int(r.n)}
        for r in g.itertuples()
    ]


def daily(df: pd.DataFrame) -> list[dict]:
    out = []
    for day, g in df.groupby("delivery_day"):
        m = metrics(g)
        out.append({
            "date": day.isoformat(),
            "mean_forecast": _f(g.forecast.mean()),
            "mean_actual": _f(g.actual.mean()),
            "mae": m.get("mae"),
            "bias": m.get("bias"),
        })
    return out
