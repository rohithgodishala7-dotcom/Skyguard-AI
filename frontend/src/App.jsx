import React, { Suspense, lazy, useCallback, useEffect, useState } from 'react';
import { Activity, AlertCircle, MapPin, Radio, RefreshCw } from 'lucide-react';
import {
  getBackendHealth,
  getLiveStations,
  repairObservation,
} from './api';

const StationMap = lazy(() => import('./components/StationMap'));
const TelemetryChart = lazy(() => import('./components/TelemetryChart'));

export default function App() {
  const [systemStatus, setSystemStatus] = useState("Connecting...");
  const [isLstmReady, setIsLstmReady] = useState(false);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [stations, setStations] = useState([]);
  const [coords, setCoords] = useState({ lat: 17.3850, lon: 78.4866 });
  const [repairingStationId, setRepairingStationId] = useState(null);
  const [repairMessage, setRepairMessage] = useState("");

  const fetchDynamicStations = useCallback(async (lat, lon) => {
    try {
      const { stations: liveStations } = await getLiveStations(lat, lon);
      setStations(liveStations);
      const centralStation = liveStations[0];
      if (centralStation) {
        setTelemetryHistory(prev => [
          ...prev.slice(-14),
          {
            timestamp: new Date().toLocaleTimeString(),
            station_id: centralStation.station_id,
            raw_temperature: centralStation.raw_temperature,
            repaired_temperature: centralStation.repaired_temperature,
            has_anomaly: centralStation.has_anomaly,
            flag_reason: centralStation.flag_reason,
            repair_method: centralStation.repair_method
          }
        ]);
      }
    } catch (error) {
      console.error("Error fetching live stations:", error);
    }
  }, []);

  const handleRepair = async station => {
    setRepairingStationId(station.station_id);
    setRepairMessage("");
    try {
      const { observation } = await repairObservation({
        station_id: station.station_id,
        latitude: station.latitude,
        longitude: station.longitude,
        temperature: station.raw_temperature,
        pressure: station.pressure,
        humidity: station.humidity,
      });
      setStations(current => current.map(item => (
        item.station_id === observation.station_id
          ? { ...item, ...observation }
          : item
      )));
      setTelemetryHistory(prev => [
        ...prev.slice(-14),
        {
          timestamp: new Date().toLocaleTimeString(),
          station_id: observation.station_id,
          raw_temperature: observation.raw_temperature,
          repaired_temperature: observation.repaired_temperature,
          has_anomaly: observation.has_anomaly,
          flag_reason: observation.flag_reason,
          repair_method: observation.repair_method,
        },
      ]);
      setRepairMessage(
        `${observation.station_id} repaired with ${observation.repair_method}.`,
      );
    } catch (error) {
      console.error("Error repairing station:", error);
      setRepairMessage(
        error.response?.data?.detail || "Unable to repair this observation.",
      );
    } finally {
      setRepairingStationId(null);
    }
  };

  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(pos => {
        const newCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        setCoords(newCoords);
      }, error => {
        setRepairMessage(`Unable to read current location: ${error.message}`);
      });
    }
  };

  useEffect(() => {
    let active = true;
    getBackendHealth()
      .then(health => {
        if (active) {
          setSystemStatus(health.status);
          setIsLstmReady(health.onnx_lstm_ready);
        }
      })
      .catch(() => {
        if (active) setSystemStatus("Offline");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => fetchDynamicStations(coords.lat, coords.lon));
    const stationInterval = setInterval(
      () => fetchDynamicStations(coords.lat, coords.lon),
      30000,
    );

    return () => clearInterval(stationInterval);
  }, [coords, fetchDynamicStations]);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0f172a', color: '#f8fafc', padding: '1.5rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '1.5rem', borderBottom: '1px solid #334155' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
            <Radio style={{ color: '#38bdf8' }} /> SkyGuard AI Dashboard
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>MoES / IMD AWS Real-Time Anomaly Engine (SIH26073)</p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={useCurrentLocation} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', backgroundColor: '#1e293b', border: '1px solid #334155', color: '#38bdf8', padding: '0.375rem 0.75rem', borderRadius: '0.5rem', cursor: 'pointer', fontSize: '0.75rem' }}>
            <MapPin style={{ width: '1rem', height: '1rem' }} /> Use My Live GPS Location
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#1e293b', padding: '0.375rem 0.75rem', borderRadius: '0.5rem', border: '1px solid #334155', fontSize: '0.75rem' }}>
            <Activity style={{ width: '1rem', height: '1rem', color: systemStatus === 'online' ? '#34d399' : '#f87171' }} />
            <span>Backend: <strong style={{ color: systemStatus === 'online' ? '#34d399' : '#f87171' }}>{systemStatus}</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#1e293b', padding: '0.375rem 0.75rem', borderRadius: '0.5rem', border: '1px solid #334155', fontSize: '0.75rem' }}>
            LSTM: <strong style={{ color: isLstmReady ? '#34d399' : '#f87171' }}>
              {isLstmReady ? 'ready' : 'unavailable'}
            </strong>
          </div>
        </div>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f8fafc' }}>
                Dynamic AWS Station Grid ({stations.length} Active Nodes)
              </h2>
              <button onClick={() => fetchDynamicStations(coords.lat, coords.lon)} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#38bdf8', background: 'none', border: 'none', cursor: 'pointer' }}>
                <RefreshCw style={{ width: '0.875rem', height: '0.875rem' }} /> Regenerate Dynamic Nodes
              </button>
            </div>
            <Suspense fallback={<div style={{ height: '320px' }}>Loading station map...</div>}>
              <StationMap
                stations={stations}
                center={coords}
                onRepair={handleRepair}
                repairingStationId={repairingStationId}
              />
            </Suspense>
            {repairMessage && (
              <p role="status" style={{ color: '#94a3b8', marginTop: '0.75rem' }}>
                {repairMessage}
              </p>
            )}
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#f8fafc' }}>
              Real-Time Temperature & Imputation Feed
            </h2>
            <Suspense fallback={<div style={{ height: '16rem' }}>Loading telemetry chart...</div>}>
              <TelemetryChart data={telemetryHistory} />
            </Suspense>
          </div>
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155', height: '100%' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle style={{ color: '#ef4444' }} /> Anomaly Detection Log
          </h2>
          <div style={{ height: '32rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', padding: '1rem', fontFamily: 'monospace', fontSize: '0.75rem', overflowY: 'auto', border: '1px solid #334155' }}>
            {telemetryHistory.map((item, idx) => (
              <div key={idx} style={{ marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid #1e293b' }}>
                <span style={{ color: '#64748b' }}>[{item.timestamp}]</span> {item.station_id}:
                {item.has_anomaly ? (
                  <div style={{ color: '#f87171', marginTop: '0.25rem' }}>
                    🚨 ANOMALY DETECTED: {item.raw_temperature}°C
                    <br />
                    🛠️ AI Auto-Repaired: {item.repaired_temperature}°C
                    <br />
                    {item.repair_method}: {item.flag_reason}
                  </div>
                ) : (
                  <div style={{ color: '#34d399', marginTop: '0.25rem' }}>
                    ✅ Live Reading: {item.raw_temperature}°C
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
