from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort

class LSTMEngine:
    def __init__(
        self,
        model_path: str | Path | None = None,
        scaler_path: str | Path | None = None,
    ):
        model_dir = Path(__file__).resolve().parents[2] / "models_store"
        model_path = Path(model_path) if model_path else model_dir / "lstm_v1.onnx"
        scaler_path = Path(scaler_path) if scaler_path else model_dir / "scaler.pkl"

        if model_path.is_file() and scaler_path.is_file():
            self.session = ort.InferenceSession(model_path)
            self.scaler = joblib.load(scaler_path)
            self.input_name = self.session.get_inputs()[0].name
            self.ready = True
        else:
            self.ready = False

    def predict_next(self, sequence_12_steps: list[list[float]]) -> dict[str, float]:
        """
        Takes 12 historical sequence steps [[temp, press, hum], ...]
        Predicts expected 13th reading using ONNX model.
        """
        if not self.ready:
            raise RuntimeError("LSTM ONNX model or Scaler not found in models_store.")

        # 1. Scale input sequence
        scaled_seq = self.scaler.transform(sequence_12_steps)
        input_tensor = np.expand_dims(scaled_seq, axis=0).astype(np.float32)

        # 2. Execute low-latency ONNX Inference
        outputs = self.session.run(None, {self.input_name: input_tensor})
        predicted_scaled = outputs[0][0]

        # 3. Inverse transform predictions back to physical units
        predicted_actual = self.scaler.inverse_transform([predicted_scaled])[0]

        return {
            "predicted_temperature": round(float(predicted_actual[0]), 2),
            "predicted_pressure": round(float(predicted_actual[1]), 2),
            "predicted_humidity": round(float(predicted_actual[2]), 2)
        }