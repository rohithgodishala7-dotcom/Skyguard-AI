from typing import Dict, Optional

class SelfHealingPipeline:
    def __init__(self):
        pass

    def repair_observation(
        self,
        raw_reading: Dict,
        is_anomaly: bool,
        anomaly_reason: str,
        lstm_predicted: Optional[Dict] = None,
        spatial_avg_temp: Optional[float] = None
    ) -> Dict:
        """
        Self-healing engine: Synthesizes a corrected observation if raw reading is anomalous.
        """
        repaired = raw_reading.copy()
        
        if not is_anomaly:
            repaired["is_repaired"] = False
            repaired["repair_method"] = "NONE"
            return repaired

        repaired["is_repaired"] = True

        # 1. Primary Repair: Spatial consensus
        if spatial_avg_temp is not None and "SPATIAL" in anomaly_reason:
            repaired["temperature"] = spatial_avg_temp
            repaired["repair_method"] = "SPATIAL_KNN_WEIGHTED_AVERAGE"
        # 2. Secondary Repair: ONNX LSTM time-series prediction
        elif lstm_predicted is not None:
            repaired["temperature"] = lstm_predicted.get("predicted_temperature", raw_reading["temperature"])
            repaired["pressure"] = lstm_predicted.get("predicted_pressure", raw_reading["pressure"])
            repaired["humidity"] = lstm_predicted.get("predicted_humidity", raw_reading["humidity"])
            repaired["repair_method"] = "LSTM_ONNX_INFERENCE"
        # 3. Fallback: Physical limit clamping
        else:
            repaired["temperature"] = max(-10.0, min(55.0, raw_reading["temperature"]))
            repaired["repair_method"] = "PHYSICAL_LIMIT_CLAMP"

        return repaired