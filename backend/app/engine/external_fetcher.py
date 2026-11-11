import json
import math
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


class LiveWeatherFetcher:
    base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_live_station_data(
        self,
        lat: float,
        lon: float,
        station_id: str,
    ) -> dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,surface_pressure",
            "timezone": "auto",
        }

        url = f"{self.base_url}?{urlencode(params)}"
        with urlopen(url, timeout=10) as response:
            payload = json.load(response)

        if not isinstance(payload, dict):
            raise ValueError("Open-Meteo response has an invalid format.")

        current = payload.get("current")
        if not isinstance(current, dict):
            raise ValueError("Open-Meteo response has no current observation.")

        measurements = {
            "temperature": current.get("temperature_2m"),
            "pressure": current.get("surface_pressure"),
            "humidity": current.get("relative_humidity_2m"),
        }
        if any(value is None or not math.isfinite(float(value)) for value in measurements.values()):
            raise ValueError("Open-Meteo response is missing a valid weather measurement.")

        return {
            "station_id": station_id,
            **{key: float(value) for key, value in measurements.items()},
            "latitude": lat,
            "longitude": lon,
        }
