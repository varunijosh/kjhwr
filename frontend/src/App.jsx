import { useEffect, useState } from "react";
import { api } from "./api";
import ForecastView from "./components/ForecastView.jsx";
import AccuracyView from "./components/AccuracyView.jsx";

export default function App() {
  const [tab, setTab] = useState("forecast");
  const [config, setConfig] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/api/config").then(setConfig).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Wind Forecast Portal</h1>
        <p className="sub">GB national wind generation: day-ahead forecast and accuracy (Elexon data)</p>
        <nav>
          <button className={tab === "forecast" ? "on" : ""} onClick={() => setTab("forecast")}>Forecast for delivery day</button>
          <button className={tab === "accuracy" ? "on" : ""} onClick={() => setTab("accuracy")}>Forecast accuracy</button>
        </nav>
      </header>
      {config?.data_source === "synthetic" && (
        <div className="banner">DEMO DATA: this is fake development data, not Elexon data. Run backend/scripts/fetch_data.py.</div>
      )}
      {error && <div className="banner">Cannot reach API: {error}</div>}
      {config && (
        <main>
          {tab === "forecast" ? <ForecastView config={config} /> : <AccuracyView config={config} />}
        </main>
      )}
    </div>
  );
}
