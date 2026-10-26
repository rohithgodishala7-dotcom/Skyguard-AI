import requests
import time
import random

API_URL = "http://127.0.0.1:8000/api/v1/telemetry"

def generate_mock_history():
    """Generates 12 historical sequence steps for the LSTM model."""
    history = []
    base_t, base_p, base_h = 26.0, 1012.0, 60.0
    for i in range(12):
        history.append([
            round(base_t + random.uniform(-0.5, 0.5), 2),
            round(base_p + random.uniform(-0.2, 0.2), 2),
            round(base_h + random.uniform(-1.0, 1.0), 2)
        ])
    return history

def run_simulation():
    print("--- Starting SkyGuard AI Telemetry Stream Simulator ---")
    
    # 1. Normal Reading Test
    normal_payload = {
        "station_id": "AWS_HYD_01",
        "temperature": 26.5,
        "pressure": 1012.3,
        "humidity": 61.2,
        "latitude": 17.3850,
        "longitude": 78.4866,
        "history_12_steps": generate_mock_history()
    }
    
    print("\n[Sending Normal Telemetry...]")
    res = requests.post(API_URL, json=normal_payload)
    print("Response:", res.json())

    time.sleep(2)

    # 2. Injected Anomaly Test (MoES Hackathon Example: Sudden 55°C Spike)
    anomaly_payload = {
        "station_id": "AWS_HYD_01",
        "temperature": 55.0,  # Extreme spike
        "pressure": 1012.3,
        "humidity": 61.2,
        "latitude": 17.3850,
        "longitude": 78.4866,
        "history_12_steps": generate_mock_history()
    }

    print("\n[Injecting 55°C Anomaly Spike...]")
    res = requests.post(API_URL, json=anomaly_payload)
    print("Response:", res.json())

if __name__ == "__main__":
    run_simulation()