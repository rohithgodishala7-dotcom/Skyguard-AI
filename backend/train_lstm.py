import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler

# 1. Ensure models store directory exists
os.makedirs("models_store", exist_ok=True)

# 2. Generate 90 Days of Synthetic Weather Data (2,160 hours)
print("Generating 90-day synthetic weather dataset...")
np.random.seed(42)
time_steps = 24 * 90  

t = np.arange(time_steps)
# Diurnal rhythm curves + realistic variance
temp = 25 + 8 * np.sin(2 * np.pi * t / 24) + np.random.normal(0, 0.5, time_steps)
press = 1013 - 3 * np.sin(2 * np.pi * t / 24) + np.random.normal(0, 0.3, time_steps)
hum = 60 - 20 * np.sin(2 * np.pi * t / 24) + np.random.normal(0, 1.0, time_steps)

df = pd.DataFrame({"temperature": temp, "pressure": press, "humidity": hum})

# 3. Feature Scaling (MinMaxScaler [0, 1])
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df)
joblib.dump(scaler, "models_store/scaler.pkl")
print("Saved scaler to models_store/scaler.pkl")

# 4. Sliding Window Sequences (12 hours history -> predict 13th hour)
def create_sequences(data, seq_length=12):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i:i+seq_length])
        ys.append(data[i+seq_length])
    return np.array(xs), np.array(ys)

SEQ_LEN = 12
X, y = create_sequences(scaled_data, SEQ_LEN)

X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# 5. PyTorch Multivariate LSTM Architecture
class WeatherLSTM(nn.Module):
    def __init__(self, input_size=3, hidden_size=32, num_layers=1):
        super(WeatherLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, input_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

model = WeatherLSTM()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# 6. Train PyTorch Model
print("Training PyTorch LSTM Model...")
epochs = 20
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()
    outputs = model(X_tensor)
    loss = criterion(outputs, y_tensor)
    loss.backward()
    optimizer.step()
    if (epoch + 1) % 5 == 0:
        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.6f}")

# 7. Export Model to ONNX Format
model.eval()
dummy_input = torch.randn(1, SEQ_LEN, 3, dtype=torch.float32)
onnx_path = "models_store/lstm_v1.onnx"

torch.onnx.export(
    model,
    dummy_input,
    onnx_path,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    dynamo=False  # <--- Forces built-in legacy exporter (no onnxscript needed!)
)
print(f"ONNX Model successfully saved to {onnx_path}")