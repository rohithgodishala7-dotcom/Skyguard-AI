import numpy as np
from typing import List, Dict, Tuple

class SpatialKNNChecker:
    def __init__(self, max_distance_km: float = 25.0, max_temp_diff: float = 5.0):
        self.max_distance_km = max_distance_km
        self.max_temp_diff = max_temp_diff

    def calculate_haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates distance in kilometers between two GPS coordinates."""
        R = 6371.0  # Earth radius in kilometers
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat / 2.0)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    def evaluate_spatial_consistency(
        self, target_station: Dict, neighbor_stations: List[Dict]
    ) -> Tuple[bool, str, float]:
        """
        Compares target station reading with nearby neighbors.
        Returns (is_anomaly, reason, weighted_neighbor_avg).
        """
        valid_neighbors = []
        weights = []

        for station in neighbor_stations:
            dist = self.calculate_haversine_distance(
                target_station["latitude"], target_station["longitude"],
                station["latitude"], station["longitude"]
            )
            if 0 < dist <= self.max_distance_km:
                # Inverse distance weighting
                weight = 1.0 / dist
                valid_neighbors.append(station["temperature"])
                weights.append(weight)

        if not valid_neighbors:
            return False, "NO_NEARBY_NEIGHBORS", target_station["temperature"]

        # Calculate spatial weighted average
        weighted_avg = float(np.average(valid_neighbors, weights=weights))
        temp_diff = abs(target_station["temperature"] - weighted_avg)

        if temp_diff > self.max_temp_diff:
            return True, f"SPATIAL_ANOMALY: Diff of {temp_diff:.1f}°C from neighbors (Avg: {weighted_avg:.1f}°C)", round(weighted_avg, 2)

        return False, "SPATIAL_VALIDATED", round(weighted_avg, 2)