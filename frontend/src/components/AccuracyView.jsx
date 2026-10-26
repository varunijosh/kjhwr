import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmtMW } from "../api";
import Card from "./Card.jsx";

function BarBlock({ title, note, data, x, y = "mae", name = "MAE" }) {
  return (
    <div className="chart">
      <h3>{title}</h3>
      {note && <p className="note">{note}</p>}
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={x} />
          <YAxis />
          <Tooltip formatter={(v) => [fmtMW(v), name]} />
          <Bar dataKey={y} fill="#2563eb" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function AccuracyView({ config }) {
  const [d, setD] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      api("/api/accuracy/summary"),
      api("/api/accuracy/daily"),
      api("/api/accuracy/by-hour"),
      api("/api/accuracy/by-horizon"),
    ])
      .then(([summary, daily, hour, horizon]) => setD({ summary, daily, hour, horizon }))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="banner">{error}</div>;
  if (!d) return <p>Loading...</p>;
  const s = d.summary;

  return (
    <section>
      <p className="note">
        Based on the forecast available at the {config.cutoff_hour_local}:00 UK cutoff on the day before delivery,
        for delivery days {config.delivery_days[0]} to {config.delivery_days[config.delivery_days.length - 1]} ({s.n} half-hours).
        Error = forecast minus actual; positive means the forecast was too high.
      </p>
      <div className="cards">
        <Card label="Average error (MAE)" value={fmtMW(s.mae)} hint={`${s.mae_pct_of_mean}% of average wind output`} />
        <Card label="Typical large error (RMSE)" value={fmtMW(s.rmse)} hint="Penalises big misses" />
        <Card label="Bias" value={fmtMW(s.bias)} hint={s.bias > 0 ? "Forecast tends to be too high" : "Forecast tends to be too low"} />
        <Card label="90% of misses below" value={fmtMW(s.p90_abs_error)} hint="Absolute error, 90th percentile" />
      </div>

      <div className="callout">
        <b>What this means for buying:</b> in 90% of half-hours the forecast was no more than{" "}
        <b>{fmtMW(s.over_forecast_p90)}</b> too high (risk of under-buying) and no more than{" "}
        <b>{fmtMW(s.under_forecast_p90)}</b> too low (risk of over-buying). Use these as a safety margin on the day-ahead volume.
      </div>

      <BarBlock title="Average error by delivery day" data={d.daily} x="date" />
      <BarBlock title="Average error by hour of day (UK time)" data={d.hour} x="hour" />
      <BarBlock
        title="Average error by forecast age"
        note="How old the forecast was when it targeted the slot. Older forecasts are less accurate. The decision-time forecast is roughly 15-39 hours old."
        data={d.horizon}
        x="label"
      />
    </section>
  );
}
