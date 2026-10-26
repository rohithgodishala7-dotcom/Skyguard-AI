import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

const normalIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const anomalyIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function StationMap({ stations }) {
  const center = [17.3850, 78.4866];

  return (
    <div style={{ height: '320px', width: '100%', borderRadius: '0.5rem', overflow: 'hidden', border: '1px solid #334155' }}>
      <MapContainer center={center} zoom={6} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {stations && stations.map((st) => (
          <Marker
            key={st.station_id}
            position={[st.latitude, st.longitude]}
            icon={st.has_anomaly ? anomalyIcon : normalIcon}
          >
            <Popup>
              <div style={{ color: '#0f172a', fontFamily: 'sans-serif' }}>
                <strong style={{ fontSize: '0.875rem', borderBottom: '1px solid #cbd5e1', display: 'block', paddingBottom: '0.25rem' }}>{st.station_id}</strong>
                <p style={{ fontSize: '0.75rem', margin: '0.25rem 0' }}>Temp: <strong>{st.temperature}°C</strong></p>
                <p style={{ fontSize: '0.75rem', margin: '0.25rem 0' }}>Pressure: <strong>{st.pressure} hPa</strong></p>
                <p style={{ fontSize: '0.75rem', margin: '0.25rem 0' }}>Humidity: <strong>{st.humidity}%</strong></p>
                <p style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
                  Status: <span style={{ color: st.has_anomaly ? '#dc2626' : '#16a34a', fontWeight: 'bold' }}>
                    {st.has_anomaly ? "ANOMALY DETECTED" : "NOMINAL"}
                  </span>
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}