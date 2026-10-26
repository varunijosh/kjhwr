from datetime import date

import pandas as pd

from app import analysis

DAY = date(2026, 1, 15)  # cutoff = 2026-01-14 09:00 UK (= 09:00 UTC in January)


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def fc_frame(rows):
    return pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"]).assign(
        startTime=lambda d: d.startTime.map(ts), publishTime=lambda d: d.publishTime.map(ts)
    )


def test_forecast_after_cutoff_is_ignored_and_latest_before_cutoff_wins():
    fc = fc_frame([
        ("2026-01-15 12:00", "2026-01-14 06:00", 100),
        ("2026-01-15 12:00", "2026-01-14 08:59", 110),
        ("2026-01-15 12:00", "2026-01-14 09:30", 200),  # too late
    ])
    out = analysis.latest_forecast_for_day(fc, DAY)
    assert len(out) == 1
    assert out.generation.iloc[0] == 110


def test_slot_with_only_late_forecasts_is_dropped():
    fc = fc_frame([("2026-01-15 13:00", "2026-01-14 10:00", 50)])
    assert analysis.latest_forecast_for_day(fc, DAY).empty


def test_other_days_are_excluded():
    fc = fc_frame([("2026-01-16 00:30", "2026-01-14 06:00", 50)])
    assert analysis.latest_forecast_for_day(fc, DAY).empty


def test_metrics_values():
    fc = fc_frame([
        ("2026-01-15 12:00", "2026-01-14 06:00", 110),
        ("2026-01-15 12:30", "2026-01-14 06:00", 80),
    ])
    act = pd.DataFrame({"startTime": [ts("2026-01-15 12:00"), ts("2026-01-15 12:30")], "generation": [100, 100]})
    t = analysis.decision_table(fc, act, [DAY])
    m = analysis.metrics(t)
    assert m["mae"] == 15 and m["bias"] == -5 and m["n"] == 2
    assert m["rmse"] == round(((100 + 400) / 2) ** 0.5, 2)


def test_horizon_is_forecast_age_in_hours():
    fc = fc_frame([("2026-01-15 12:00", "2026-01-14 06:00", 100)])
    out = analysis.latest_forecast_for_day(fc, DAY)
    assert out.horizon_h.iloc[0] == 30
