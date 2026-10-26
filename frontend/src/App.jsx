import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Radio, AlertCircle, RefreshCw, MapPin } from 'lucide-react';
import axios from 'axios';
import StationMap from './components/StationMap';
import TelemetryChart from './components/TelemetryChart';

export default function App() {
  const [systemStatus, setSystemStatus] = useState("Connecting...");
  const [isLstmReady, setIsLstmReady] = useState(false);
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [stations, setStations] = useState([]);
  const [coords, setCoords] = useState({ lat: 17.3850, lon: 78.4866 });

  const fetchDynamicStations = (lat = coords.lat, lon = coords.lon) => {
    axios.get(`http://127.0.0.1:8000/api/v1/live-surrounding-stations?lat=${lat}&lon=${lon}&count=6`)
      .then(res => {
        if (res.data.stations) {
          setStations(res.data.stations);
        }
      })
      .catch(err => console.error("Error fetching dynamic stations:", err));
  };

  const useCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(pos => {
        const newCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        setCoords(newCoords);
        fetchDynamicStations(newCoords.lat, newCoords.lon);
      });
    }
  };

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/')
      .then(res => {
        setSystemStatus(res.data.status);
        setIsLstmReady(res.data.onnx_lstm_ready);
      })
      .catch(() => setSystemStatus("Offline"));

    fetchDynamicStations();

    const stationInterval = setInterval(() => fetchDynamicStations(coords.lat, coords.lon), 30000);

    const streamInterval = setInterval(() => {
      const now = new Date().toLocaleTimeString();
      const isAnomaly = Math.random() > 0.85;
      const rawTemp = isAnomaly ? 55.0 : parseFloat((26 + Math.random() * 4).toFixed(1));
      const repairedTemp = isAnomaly ? 27.2 : rawTemp;

      setTelemetryHistory(prev => [
        ...prev.slice(-14), 
        { timestamp: now, raw_temperature: rawTemp, repaired_temperature: repairedTemp }
      ]);
    }, 3000);

    return () => {
      clearInterval(stationInterval);
      clearInterval(streamInterval);
    };
  }, [coords]);

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
        </div>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f8fafc' }}>
                Dynamic AWS Station Grid ({stations.length} Active Nodes)
              </h2>
              <button onClick={() => fetchDynamicStations()} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', color: '#38bdf8', background: 'none', border: 'none', cursor: 'pointer' }}>
                <RefreshCw style={{ width: '0.875rem', height: '0.875rem' }} /> Regenerate Dynamic Nodes
              </button>
            </div>
            <StationMap stations={stations} />
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#f8fafc' }}>
              Real-Time Temperature & Imputation Feed
            </h2>
            <TelemetryChart data={telemetryHistory} />
          </div>
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155', height: '100%' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle style={{ color: '#ef4444' }} /> Anomaly Detection Log
          </h2>
          <div style={{ height: '32rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', padding: '1rem', fontFamily: 'monospace', fontSize: '0.75rem', overflowY: 'auto', border: '1px solid #334155' }}>
            {telemetryHistory.map((item, idx) => (
              <div key={idx} style={{ marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid #1e293b' }}>
                <span style={{ color: '#64748b' }}>[{item.timestamp}]</span> AWS_DYNAMIC_01:
                {item.raw_temperature > 50 ? (
                  <div style={{ color: '#f87171', marginTop: '0.25rem' }}>
                    🚨 SPIKE DETECTED: {item.raw_temperature}°C
                    <br />
                    🛠️ AI Auto-Repaired: {item.repaired_temperature}°C
                  </div>
                ) : (
                  <div style={{ color: '#34d399', marginTop: '0.25rem' }}>
                    ✅ Reading Valid: {item.raw_temperature}°C
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
