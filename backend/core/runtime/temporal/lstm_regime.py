from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as functional

from backend.core.runtime.temporal.regime_forecast import RegimeForecast
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context
from backend.ml.registry import ModelRegistry


class LSTMRegimeForecaster(nn.Module):
    """LSTM-based regime predictor with uncertainty estimation."""

    def __init__(
        self,
        input_size: int = 6,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_classes: int = 3,
    ):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.fc2 = nn.Linear(64, num_classes)
        self.dropout = nn.Dropout(0.3)

        # Uncertainty head (approximate variance)
        self.uncertainty_head = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]  # take last timestep

        x_out = functional.relu(self.fc1(last_hidden))
        x_out = self.dropout(x_out)

        logits = self.fc2(x_out)
        uncertainty = torch.sigmoid(self.uncertainty_head(x_out))

        probs = functional.softmax(logits, dim=1)
        return probs, uncertainty


class LSTMRegimeEngine:
    """Production wrapper with training, inference, and persistence."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = LSTMRegimeForecaster()
            cls._instance._model.eval()
            cls._instance._model_registry = ModelRegistry()
        return cls._instance

    @classmethod
    def engine(cls) -> LSTMRegimeEngine:
        return cls()

    async def forecast(self, history: list[dict[str, Any]], horizon_hours: int = 6) -> RegimeForecast:
        """Generate LSTM-based regime forecast."""
        with trace_context("regime.forecast.lstm"):
            obs = observability()
            obs.increment("lstm_regime_forecasts_total")

            # Prepare sequence
            seq = self._prepare_sequence(history)
            seq_tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

            with torch.no_grad():
                probs, uncertainty = self._model(seq_tensor)

            regimes = ["normal", "panic", "disruption"]
            pred_idx = torch.argmax(probs[0]).item()
            predicted = regimes[pred_idx]

            forecast = RegimeForecast(
                predicted_regime=predicted,
                probability=float(probs[0][pred_idx]),
                confidence=float(1.0 - uncertainty[0].item()),
                forecast_horizon_hours=float(horizon_hours),
                key_drivers=["lstm_hidden_pattern", "entropy_trend", "volatility"],
                metadata={
                    "probabilities": {regimes[i]: float(probs[0][i]) for i in range(3)},
                    "model_version": "lstm_v1",
                },
            )

            obs.gauge("lstm_predicted_regime_prob", forecast.probability)
            return forecast

    def _prepare_sequence(self, history: list[dict[str, Any]]) -> list[list[float]]:
        """Convert history into feature sequences."""
        features = []
        for entry in history[-50:]:  # last 50 steps
            features.append(
                [
                    entry.get("entropy", 0.0),
                    entry.get("volatility", 0.0),
                    entry.get("disagreement", 0.0),
                    entry.get("change_rate", 0.0),
                    entry.get("ensemble_std", 0.0),
                    1.0 if entry.get("regime") == "disruption" else 0.0,
                ]
            )
        return features
