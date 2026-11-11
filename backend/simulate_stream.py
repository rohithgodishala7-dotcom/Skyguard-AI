import json
from urllib.request import urlopen

API_URL = "http://127.0.0.1:8000/api/v1/live-surrounding-stations"


def fetch_live_stations() -> None:
    with urlopen(API_URL, timeout=30) as response:
        payload = json.load(response)

    for station in payload["stations"]:
        print(
            f"{station['station_id']}: "
            f"{station['temperature']}°C, "
            f"{station['pressure']} hPa, "
            f"{station['humidity']}% RH "
            f"({station['repair_method']})"
        )


if __name__ == "__main__":
    fetch_live_stations()
