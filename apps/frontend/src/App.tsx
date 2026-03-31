import React from "react";
import MapComponent from "./components/MapComponent";
import "./App.css";

const App: React.FC = () => {
  const [hours, setHours] = React.useState(24);
  const [summary, setSummary] = React.useState<{
    hours: number;
    total_events: number;
    total_clusters: number;
    outbreak_clusters: number;
    largest_cluster: number;
  } | null>(null);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Geospatial Disease Surveillance MVP</p>
          <h1>OutbreakX anomaly detection console</h1>
        </div>
        <div className="time-window-picker">
          <label htmlFor="hours">Time window</label>
          <select id="hours" value={hours} onChange={(event) => setHours(Number(event.target.value))}>
            <option value={6}>6 hours</option>
            <option value={12}>12 hours</option>
            <option value={24}>24 hours</option>
            <option value={48}>48 hours</option>
          </select>
        </div>
      </header>

      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Core Principle</p>
          <h2>An outbreak is a spatiotemporal density anomaly, not a single case.</h2>
          <p>
            The dashboard filters recent events, clusters them with Haversine DBSCAN, and flags
            compact high-density regions as potential outbreaks.
          </p>
        </div>

        <div className="metric-grid">
          <article className="metric-card">
            <span>Total events</span>
            <strong>{summary?.total_events ?? "--"}</strong>
          </article>
          <article className="metric-card">
            <span>Dense clusters</span>
            <strong>{summary?.total_clusters ?? "--"}</strong>
          </article>
          <article className="metric-card">
            <span>Flagged outbreaks</span>
            <strong>{summary?.outbreak_clusters ?? "--"}</strong>
          </article>
          <article className="metric-card">
            <span>Largest cluster</span>
            <strong>{summary?.largest_cluster ?? "--"}</strong>
          </article>
        </div>
      </section>

      <MapComponent hours={hours} onSummaryChange={setSummary} />
    </div>
  );
};

export default App;
