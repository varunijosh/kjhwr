import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmtMW, fmtTime, hhmm } from "../api";
import Card from "./Card.jsx";

export default function ForecastView({ config }) {
  const days = config.delivery_days;
  const [day, setDay] = useState(days[Math.floor(days.length / 2)]);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    api(`/api/forecast?date=${day}`).then(setData).catch((e) => setError(e.message));
  }, [day]);

  const s = data?.summary;
  const acc = data?.day_accuracy;

  return (
    <section>
      <div className="row">
        <label>
          Delivery day{" "}
          <select value={day} onChange={(e) => setDay(e.target.value)}>
            {days.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>
        {data && (
          <span className="note">
            Decision cutoff: <b>{fmtTime(data.cutoff)}</b> (UK). Latest forecast used was published{" "}
            <b>{fmtTime(data.latest_publish_time)}</b>.
          </span>
        )}
      </div>

      {error && <div className="banner">{error}</div>}
      {!data && !error && <p>Loading...</p>}

      {data && (
        <>
          <div className="cards">
            <Card label="Average forecast wind" value={fmtMW(s.mean_forecast)} hint="Power you do NOT need to buy from other sources" />
            <Card label="Peak forecast" value={fmtMW(s.peak_forecast)} hint={`at ${hhmm(s.peak_time)}`} />
            <Card label="Lowest forecast" value={fmtMW(s.min_forecast)} hint="Highest need for thermal/other supply" />
            <Card label="Day forecast error (MAE)" value={acc.n ? fmtMW(acc.mae) : "-"} hint="Average miss vs actual, known after the day" />
          </div>

          <div className="chart">
            <h3>Forecast (as known at decision time) vs actual</h3>
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={data.series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" tickFormatter={hhmm} minTickGap={40} />
                <YAxis tickFormatter={(v) => `${Math.round(v / 1000)}k`} label={{ value: "MW", angle: -90, position: "insideLeft" }} />
                <Tooltip labelFormatter={fmtTime} formatter={(v) => fmtMW(v)} />
                <Legend />
                <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#2563eb" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="actual" name="Actual" stroke="#16a34a" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </section>
  );
}
