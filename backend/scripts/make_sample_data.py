"""DEV ONLY: generate FAKE wind data so you can run the app before fetching real data.

Creates data/SYNTHETIC; the UI then shows a red warning banner. Running
fetch_data.py deletes that marker and overwrites the files with real data.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"
rng = np.random.default_rng(42)
start = datetime(2025, 12, 28, tzinfo=timezone.utc)
end = datetime(2026, 2, 2, tzinfo=timezone.utc)
slots = pd.date_range(start, end, freq="30min", inclusive="left")

walk = np.cumsum(rng.normal(0, 180, len(slots)))
walk = (walk - walk.min()) / (walk.max() - walk.min())
actual = np.clip(800 + walk * 12000 + rng.normal(0, 150, len(slots)), 100, 14500)
act = pd.DataFrame({"startTime": slots, "generation": actual.round(0)})

rows = []
pubs = pd.date_range(start, end - timedelta(hours=1), freq="3h")
idx = {t: i for i, t in enumerate(slots)}
for p in pubs:
    for k in range(1, 97):
        t = p + timedelta(minutes=30 * k)
        if t not in idx:
            continue
        h = k / 2
        noise = rng.normal(0, 150 + 70 * h)
        rows.append((t, p, max(0, round(actual[idx[t]] + noise))))
fc = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
fc = fc[(fc.startTime >= datetime(2026, 1, 2, tzinfo=timezone.utc))]
act = act[act.startTime >= datetime(2026, 1, 2, tzinfo=timezone.utc)]

DATA.mkdir(exist_ok=True)
act.to_csv(DATA / "actuals.csv", index=False)
fc.to_csv(DATA / "forecasts.csv", index=False)
(DATA / "SYNTHETIC").write_text("fake data for development only\n")
print("Wrote FAKE data:", len(act), "actual rows,", len(fc), "forecast rows")
