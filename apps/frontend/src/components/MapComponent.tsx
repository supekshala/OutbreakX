import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Circle,
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

type DiseaseEvent = {
  id: number;
  timestamp: string;
  lat: number;
  lng: number;
  symptoms: string[];
};

type Cluster = {
  cluster_id: number;
  size: number;
  centroid: {
    lat: number;
    lng: number;
  };
  radius_km: number;
  event_ids: number[];
  symptom_counts: Record<string, number>;
  start_time: string;
  end_time: string;
  is_outbreak: boolean;
};

type Summary = {
  hours: number;
  total_events: number;
  total_clusters: number;
  outbreak_clusters: number;
  largest_cluster: number;
};

type Props = {
  hours: number;
  onSummaryChange: (summary: Summary | null) => void;
};

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ?? "http://localhost:8000/api/v1/surveillance";

const SYMPTOM_OPTIONS = ["fever", "cough", "fatigue", "headache", "nausea"];
const MELBOURNE_CENTER: [number, number] = [-37.8136, 144.9631];

const formatTimestamp = (value: string) =>
  new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });

const MapEventCapture: React.FC<{
  onSelectLocation: (coords: { lat: number; lng: number }) => void;
}> = ({ onSelectLocation }) => {
  useMapEvents({
    click(event) {
      onSelectLocation({
        lat: event.latlng.lat,
        lng: event.latlng.lng,
      });
    },
  });

  return null;
};

const MapComponent: React.FC<Props> = ({ hours, onSummaryChange }) => {
  const [events, setEvents] = useState<DiseaseEvent[]>([]);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(["fever", "cough"]);
  const [submitting, setSubmitting] = useState(false);

  const outbreakClusters = useMemo(
    () => clusters.filter((cluster) => cluster.is_outbreak),
    [clusters],
  );

  const fetchSurveillanceData = useCallback(async () => {
    setLoading(true);

    try {
      const [eventsResult, clustersResult, summaryResult] = await Promise.allSettled([
        axios.get<DiseaseEvent[]>(`${API_BASE_URL}/events`, { params: { hours } }),
        axios.get<Cluster[]>(`${API_BASE_URL}/clusters`, { params: { hours } }),
        axios.get<Summary>(`${API_BASE_URL}/summary`, { params: { hours } }),
      ]);

      let hasAnySuccess = false;

      if (eventsResult.status === "fulfilled") {
        setEvents(eventsResult.value.data);
        hasAnySuccess = true;
      }

      if (clustersResult.status === "fulfilled") {
        setClusters(clustersResult.value.data);
        hasAnySuccess = true;
      }

      if (summaryResult.status === "fulfilled") {
        onSummaryChange(summaryResult.value.data);
        hasAnySuccess = true;
      } else {
        onSummaryChange(null);
      }

      if (hasAnySuccess) {
        setError(null);
      } else {
        setError("Unable to load surveillance data. Confirm the FastAPI service is running.");
      }
    } catch (requestError) {
      setError("Unable to load surveillance data. Confirm the FastAPI service is running.");
    } finally {
      setLoading(false);
    }
  }, [hours, onSummaryChange]);

  useEffect(() => {
    void fetchSurveillanceData();
  }, [fetchSurveillanceData]);

  const toggleSymptom = (symptom: string) => {
    setSelectedSymptoms((currentSymptoms) =>
      currentSymptoms.includes(symptom)
        ? currentSymptoms.filter((item) => item !== symptom)
        : [...currentSymptoms, symptom],
    );
  };

  const handleCreateEvent = async () => {
    if (!selectedLocation || selectedSymptoms.length === 0) {
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_BASE_URL}/events`, {
        timestamp: new Date().toISOString(),
        lat: selectedLocation.lat,
        lng: selectedLocation.lng,
        symptoms: selectedSymptoms,
      });
      setSelectedLocation(null);
      await fetchSurveillanceData();
    } catch (requestError) {
      setError("Event submission failed. Check the API and database configuration.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="surveillance-grid">
      <div className="map-shell">
        <div className="map-toolbar">
          <div>
            <p className="eyebrow">Operational Map</p>
            <h2>Recent symptom activity and outbreak candidates</h2>
          </div>
          <button className="ghost-button" onClick={() => void fetchSurveillanceData()}>
            Refresh
          </button>
        </div>

        <MapContainer
          center={MELBOURNE_CENTER}
          zoom={11}
          scrollWheelZoom
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MapEventCapture onSelectLocation={setSelectedLocation} />

          {events.map((event) => (
            <CircleMarker
              key={event.id}
              center={[event.lat, event.lng]}
              radius={5}
              pathOptions={{
                color: "#0f172a",
                weight: 1,
                fillColor: "#f97316",
                fillOpacity: 0.9,
              }}
            >
              <Popup>
                <strong>Event #{event.id}</strong>
                <br />
                {formatTimestamp(event.timestamp)}
                <br />
                Symptoms: {event.symptoms.join(", ") || "None"}
              </Popup>
            </CircleMarker>
          ))}

          {clusters.map((cluster) => (
            <Circle
              key={cluster.cluster_id}
              center={[cluster.centroid.lat, cluster.centroid.lng]}
              radius={Math.max(cluster.radius_km * 1000, 250)}
              pathOptions={{
                color: cluster.is_outbreak ? "#b91c1c" : "#0369a1",
                weight: cluster.is_outbreak ? 3 : 2,
                fillColor: cluster.is_outbreak ? "#ef4444" : "#38bdf8",
                fillOpacity: cluster.is_outbreak ? 0.2 : 0.12,
              }}
            >
              <Popup>
                <strong>
                  {cluster.is_outbreak ? "Potential outbreak" : "Cluster"} #{cluster.cluster_id}
                </strong>
                <br />
                Size: {cluster.size}
                <br />
                Radius: {cluster.radius_km} km
                <br />
                Window: {formatTimestamp(cluster.start_time)} to {formatTimestamp(cluster.end_time)}
              </Popup>
            </Circle>
          ))}
        </MapContainer>

        <div className="map-legend">
          <span>
            <i className="legend-swatch event-swatch" /> Symptom events
          </span>
          <span>
            <i className="legend-swatch cluster-swatch" /> Dense clusters
          </span>
          <span>
            <i className="legend-swatch outbreak-swatch" /> Flagged outbreaks
          </span>
        </div>
      </div>

      <aside className="control-panel">
        <div className="panel-card">
          <p className="eyebrow">MVP Input</p>
          <h3>Create a symptom event</h3>
          <p className="panel-copy">
            Click the map to choose a location, then submit a symptom report into the active time
            window.
          </p>

          <div className="selected-location">
            <span>Latitude</span>
            <strong>{selectedLocation ? selectedLocation.lat.toFixed(5) : "Select on map"}</strong>
            <span>Longitude</span>
            <strong>{selectedLocation ? selectedLocation.lng.toFixed(5) : "Select on map"}</strong>
          </div>

          <div className="symptom-grid">
            {SYMPTOM_OPTIONS.map((symptom) => (
              <button
                key={symptom}
                className={
                  selectedSymptoms.includes(symptom)
                    ? "symptom-pill symptom-pill-active"
                    : "symptom-pill"
                }
                onClick={() => toggleSymptom(symptom)}
                type="button"
              >
                {symptom}
              </button>
            ))}
          </div>

          <button
            className="primary-button"
            disabled={!selectedLocation || selectedSymptoms.length === 0 || submitting}
            onClick={() => void handleCreateEvent()}
          >
            {submitting ? "Submitting..." : "Submit event"}
          </button>
        </div>

        <div className="panel-card">
          <p className="eyebrow">Detection Output</p>
          <h3>Flagged clusters</h3>
          {loading && <p className="panel-copy">Loading recent events and clusters...</p>}
          {error && <p className="error-text">{error}</p>}
          {!loading && !error && outbreakClusters.length === 0 && (
            <p className="panel-copy">
              No outbreak-sized clusters detected in the current {hours}-hour window.
            </p>
          )}
          <div className="cluster-list">
            {outbreakClusters.map((cluster) => (
              <article key={cluster.cluster_id} className="cluster-item">
                <div className="cluster-heading">
                  <strong>Cluster #{cluster.cluster_id}</strong>
                  <span>{cluster.size} events</span>
                </div>
                <p>
                  Centroid {cluster.centroid.lat.toFixed(3)}, {cluster.centroid.lng.toFixed(3)}
                </p>
                <p>Radius {cluster.radius_km} km</p>
                <p>
                  Top symptoms:{" "}
                  {Object.keys(cluster.symptom_counts).slice(0, 3).join(", ") || "No symptoms"}
                </p>
              </article>
            ))}
          </div>
        </div>
      </aside>
    </section>
  );
};

export default MapComponent;
