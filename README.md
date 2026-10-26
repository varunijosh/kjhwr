# Wind Forecast Portal

Web app for a GB energy utility's day-ahead buying team. It shows (1) the latest national wind forecast available when the day-ahead decision must be made, and (2) how accurate those forecasts have been, in MW.

**Live app:** `<PASTE VERCEL/HEROKU URL HERE>`

> **AI tools disclosure:** Claude (Anthropic) was used to assist in building this project.

## Data
Elexon BMRS only: `FUELHH` (actual wind, `fuelType=WIND`) and `WINDFOR` (wind forecasts with `publishTime`). Scope: purchase decisions made in January 2026 (delivery days 2 Jan - 1 Feb 2026).

## Key assumptions
- Decision cutoff: **09:00 UK time on the day before delivery** (`CUTOFF_HOUR` in `backend/app/config.py`).
- For each half-hour we use the **latest forecast published at or before the cutoff**.
- Error = forecast - actual (positive = forecast too high).
- Data is saved as CSV snapshots in `data/` (fixed scope, reproducible, no runtime dependency on Elexon).

## Files and directories
```
backend/
  app/config.py        assumptions: cutoff, timezone, date scope
  app/data.py          loads data/*.csv
  app/analysis.py      cutoff logic + accuracy metrics (pure, tested)
  app/main.py          FastAPI routes (/api/...) and serves the React build
  scripts/fetch_data.py        downloads real data from Elexon -> data/
  scripts/make_sample_data.py  DEV ONLY fake data (shows a red banner in the UI)
  tests/               pytest unit tests
frontend/              React (Vite + Recharts)
data/                  actuals.csv, forecasts.csv
docs/ARCHITECTURE.md   design notes
Dockerfile, docker-compose.yml, heroku.yml
```

## Run it
**1. Get the data (once, needs internet):**
```bash
pip install -r backend/requirements.txt
python backend/scripts/fetch_data.py
```
Commit `data/*.csv` so the deployed app has data.

**2a. Docker (one command):**
```bash
docker compose up --build      # open http://localhost:8000
```

**2b. Local dev (two terminals):**
```bash
cd backend && uvicorn app.main:app --reload          # API on :8000, docs at /docs
cd frontend && npm install && npm run dev            # UI on :5173
```

**Tests:** `cd backend && python -m pytest`

## API
`/api/config`, `/api/forecast?date=YYYY-MM-DD`, `/api/accuracy/summary`, `/api/accuracy/by-hour`, `/api/accuracy/by-horizon`, `/api/accuracy/daily`

## Deploy (Heroku, container)
```bash
heroku create
heroku stack:set container
git push heroku main
```
(Alternative: deploy `frontend/` to Vercel with `VITE_API_URL` pointing at the hosted API.)
