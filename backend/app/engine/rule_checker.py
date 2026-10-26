from typing import Tuple, Dict, List

class RuleChecker:
    """
    Evaluates instant physical limits and flatlines before passing to AI.
    """
    def __init__(self):
        self.temp_range = (-10.0, 55.0)    # Celsius
        self.press_range = (900.0, 1100.0) # hPa
        self.hum_range = (0.0, 100.0)      # %

    def check_reading(self, current: Dict[str, float], recent_history: List[Dict[str, float]] = None) -> Tuple[str, str]:
        temp = current.get('temperature')
        press = current.get('pressure')
        hum = current.get('humidity')

        # 1. Hard Range Check
        if temp is None or not (self.temp_range[0] <= temp <= self.temp_range[1]):
            return "FAULTY", f"Temperature {temp}°C out of valid range {self.temp_range}"
        if press is None or not (self.press_range[0] <= press <= self.press_range[1]):
            return "FAULTY", f"Pressure {press} hPa out of valid range {self.press_range}"
        if hum is None or not (self.hum_range[0] <= hum <= self.hum_range[1]):
            return "FAULTY", f"Humidity {hum}% out of valid range {self.hum_range}"

        # 2. Frozen Value / Flatline Check
        if recent_history and len(recent_history) >= 4:
            temps = [r['temperature'] for r in recent_history] + [temp]
            if len(set(temps)) == 1:
                return "FAULTY", f"Sensor flatline detected: Temperature frozen at {temp}°C"

        return "GOOD", "All basic rule checks passed"