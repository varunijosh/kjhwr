"""Load the pre-downloaded Elexon CSV files (see scripts/fetch_data.py)."""
from functools import lru_cache

import pandas as pd

from . import config


class DataNotFound(RuntimeError):
    pass


def _read(name: str) -> pd.DataFrame:
    path = config.DATA_DIR / name
    if not path.exists():
        raise DataNotFound(
            f"{path} not found. Run `python backend/scripts/fetch_data.py` first."
        )
    df = pd.read_csv(path)
    for c in ("startTime", "publishTime"):
        if c in df:
            df[c] = pd.to_datetime(df[c], utc=True)
    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    return df


@lru_cache
def load_actuals() -> pd.DataFrame:
    df = _read("actuals.csv")
    return df.sort_values("startTime").drop_duplicates("startTime", keep="last")


@lru_cache
def load_forecasts() -> pd.DataFrame:
    df = _read("forecasts.csv")
    return df.dropna(subset=["generation"]).drop_duplicates(["startTime", "publishTime"])


def data_source() -> str:
    return "synthetic" if (config.DATA_DIR / "SYNTHETIC").exists() else "elexon"
