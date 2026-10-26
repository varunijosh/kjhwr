"""Central configuration. Change assumptions here, not in the analysis code."""
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parents[1] / "static"))

TZ = "Europe/London"
# Assumption: the buyer must decide by this local (UK) hour on day D-1.
# The GB day-ahead auctions close in the morning of D-1; 09:00 is a
# deliberately conservative choice. Override with env var CUTOFF_HOUR.
CUTOFF_HOUR = int(os.getenv("CUTOFF_HOUR", "9"))

# Scope: purchase decisions MADE in January 2026 -> delivery days are D+1.
DECISION_START = date(2026, 1, 1)
DECISION_END = date(2026, 1, 31)


def delivery_days():
    n = (DECISION_END - DECISION_START).days + 1
    return [DECISION_START + timedelta(days=i + 1) for i in range(n)]
