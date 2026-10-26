import onnxruntime as ort
import numpy as np
import joblib
import os

class LSTMEngine:
    def __init__(self, model_path="models_store/lstm_v1.onnx", scaler_path="models_store/scaler.pkl"):
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.session = ort.InferenceSession(model_path)
            self.scaler = joblib.load(scaler_path)
            self.ready = True
        else:
            self.ready = False

    def predict_next(self, sequence_12_steps: list) -> dict:
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
        outputs = self.session.run(None, {"input": input_tensor})
        predicted_scaled = outputs[0][0]

        # 3. Inverse transform predictions back to physical units
        predicted_actual = self.scaler.inverse_transform([predicted_scaled])[0]

        return {
            "predicted_temperature": round(float(predicted_actual[0]), 2),
            "predicted_pressure": round(float(predicted_actual[1]), 2),
            "predicted_humidity": round(float(predicted_actual[2]), 2)
        }