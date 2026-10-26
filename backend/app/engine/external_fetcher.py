import requests
from typing import Dict

class LiveWeatherFetcher:
    def __init__(self):
        # Open-Meteo free endpoint (e.g., Hyderabad coordinates)
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_live_station_data(self, lat: float = 17.3850, lon: float = 78.4866, station_id: str = "AWS_HYD_LIVE") -> Dict:
        """Fetches live real-world T, P, and RH values from Open-Meteo."""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "surface_pressure"],
            "timezone": "auto"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json().get("current", {})

            return {
                "station_id": station_id,
                "temperature": data.get("temperature_2m", 26.0),
                "pressure": data.get("surface_pressure", 1012.0),
                "humidity": data.get("relative_humidity_2m", 60.0),
                "latitude": lat,
                "longitude": lon
            }
        except Exception as e:
            # Fallback mock reading if internet/API fails
            return {
                "station_id": station_id,
                "temperature": 26.5,
                "pressure": 1012.5,
                "humidity": 55.0,
                "latitude": lat,
                "longitude": lon,
                "error": str(e)
            }