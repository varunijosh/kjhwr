"""Download Jan-2026 wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon.

Run from the repo root:  python backend/scripts/fetch_data.py
Writes data/actuals.csv and data/forecasts.csv. No API key needed.
"""
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA = Path(__file__).resolve().parents[2] / "data"

# Decisions in Jan 2026 -> delivery days 2 Jan .. 1 Feb 2026 (UTC == UK time in winter)
DELIVERY_START = datetime(2026, 1, 2, tzinfo=timezone.utc)
DELIVERY_END = datetime(2026, 2, 2, tzinfo=timezone.utc)  # exclusive
# Forecasts for 2 Jan can be published ~2 days earlier.
PUBLISH_START = datetime(2025, 12, 29, tzinfo=timezone.utc)
CHUNK_DAYS = 2


def get(dataset, params, retries=3):
    for i in range(retries):
        r = requests.get(f"{BASE}/{dataset}/stream", params=params, timeout=120)
        if r.status_code == 200:
            data = r.json()
            return data["data"] if isinstance(data, dict) and "data" in data else data
        if r.status_code == 400:
            raise RuntimeError(f"400 from Elexon for {dataset} {params}: {r.text[:300]}")
        time.sleep(2 * (i + 1))
    r.raise_for_status()


def chunks(start, end, days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_actuals():
    rows = []
    for a, b in chunks(DELIVERY_START, DELIVERY_END, 7):
        params = {
            "settlementDateFrom": a.date().isoformat(),
            "settlementDateTo": (b - timedelta(days=1)).date().isoformat(),
            "fuelType": "WIND",
        }
        got = get("FUELHH", params)
        print(f"FUELHH {params['settlementDateFrom']}..{params['settlementDateTo']}: {len(got)} rows")
        rows += got
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"]
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df[(df.startTime >= DELIVERY_START) & (df.startTime < DELIVERY_END)]
    return df[["startTime", "generation"]].sort_values("startTime").drop_duplicates("startTime", keep="last")


def fetch_forecasts():
    rows = []
    for a, b in chunks(PUBLISH_START, DELIVERY_END, CHUNK_DAYS):
        params = {"publishDateTimeFrom": iso(a), "publishDateTimeTo": iso(b)}
        got = get("WINDFOR", params)
        print(f"WINDFOR publish {params['publishDateTimeFrom']}..: {len(got)} rows")
        rows += got
    df = pd.DataFrame(rows)
    for c in ("startTime", "publishTime"):
        df[c] = pd.to_datetime(df[c], utc=True)
    df = df[(df.startTime >= DELIVERY_START) & (df.startTime < DELIVERY_END)]
    df = df[["startTime", "publishTime", "generation"]]
    return df.drop_duplicates(["startTime", "publishTime"]).sort_values(["startTime", "publishTime"])


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    try:
        act, fc = fetch_actuals(), fetch_forecasts()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Fetch failed: {e}\nCheck parameter names at https://bmrs.elexon.co.uk/api-documentation")
    act.to_csv(DATA / "actuals.csv", index=False)
    fc.to_csv(DATA / "forecasts.csv", index=False)
    (DATA / "SYNTHETIC").unlink(missing_ok=True)
    print(f"\nactuals: {len(act)} rows, {act.startTime.min()} -> {act.startTime.max()}")
    print(f"forecasts: {len(fc)} rows, {fc.publishTime.min()} -> {fc.publishTime.max()}")
    print("Saved to data/. Commit these files so the deployed app can use them.")
