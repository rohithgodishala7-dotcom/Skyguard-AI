import axios from 'axios';

export interface BackendHealth {
  status: string;
  onnx_lstm_ready: boolean;
  database: string;
}

export interface StationReading {
  station_id: string;
  name?: string;
  latitude: number;
  longitude: number;
  temperature: number;
  pressure: number;
  humidity: number;
  raw_temperature: number;
  repaired_temperature: number;
  has_anomaly: boolean;
  qc_flag: string;
  flag_reason: string;
  repair_method: string;
  timestamp: string;
}

export interface StationCollection {
  stations: StationReading[];
}

export interface RepairObservationRequest {
  station_id: string;
  latitude: number;
  longitude: number;
  temperature: number;
  pressure: number;
  humidity: number;
}

export interface RepairObservationResponse {
  observation: StationReading;
}

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, ''),
});

export async function getBackendHealth(): Promise<BackendHealth> {
  const { data } = await api.get<BackendHealth>('/health');
  return data;
}

export async function getLiveStations(
  latitude: number,
  longitude: number,
  count = 6,
): Promise<StationCollection> {
  const { data } = await api.get<StationCollection>('/live-surrounding-stations', {
    params: { lat: latitude, lon: longitude, count },
  });
  return data;
}

export async function repairObservation(
  request: RepairObservationRequest,
): Promise<RepairObservationResponse> {
  const { data } = await api.post<RepairObservationResponse>(
    '/anomalies/repair',
    request,
  );
  return data;
}
