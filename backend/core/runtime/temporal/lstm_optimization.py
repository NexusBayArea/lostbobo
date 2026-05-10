from __future__ import annotations

import time
from typing import Any, Dict

import optuna
import torch
from backend.core.ml.registry import ModelRegistry
from backend.core.runtime.temporal.lstm_regime import LSTMRegimeForecaster
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class LSTMHyperparameterOptimizer:
    """Automated hyperparameter tuning for LSTM regime forecaster."""

    def __init__(self):
        self.model_registry = ModelRegistry()
        self.study = None

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna objective function."""
        params = {
            "hidden_size": trial.suggest_int("hidden_size", 64, 256, step=32),
            "num_layers": trial.suggest_int("num_layers", 1, 4),
            "dropout": trial.suggest_float("dropout", 0.1, 0.5),
            "learning_rate": trial.suggest_float("lr", 1e-5, 1e-2, log=True),
            "weight_decay": trial.suggest_float("weight_decay", 1e-6, 1e-3, log=True),
        }

        # Build model with trial params
        model = LSTMRegimeForecaster(
            hidden_size=params["hidden_size"],
            num_layers=params["num_layers"],
            dropout=params["dropout"],
        )

        # Training loop (placeholder — replace with actual training data loader)
        val_loss = self._train_and_evaluate(model, params)

        # Log to Optuna + Observability
        observability().gauge("lstm_trial_val_loss", val_loss)

        return val_loss

    def _train_and_evaluate(self, model: LSTMRegimeForecaster, params: Dict[str, Any]) -> float:
        """Single train + validation run."""
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=params["learning_rate"],
            weight_decay=params["weight_decay"],
        )
        # ... actual training loop with early stopping ...
        # Return best validation loss (mocked for now)
        return 0.042

    async def optimize(self, n_trials: int = 50, timeout: int = 3600) -> Dict[str, Any]:
        """Run full hyperparameter search."""
        with trace_context("lstm.hyperparam.optimize"):
            obs = observability()
            obs.increment("lstm_optimization_runs_total")

            self.study = optuna.create_study(
                direction="minimize",
                sampler=optuna.samplers.TPESampler(seed=42),
                pruner=optuna.pruners.MedianPruner(),
            )

            self.study.optimize(self.objective, n_trials=n_trials, timeout=timeout)

            best_params = self.study.best_params
            best_value = self.study.best_value

            # Save best model configuration
            await self.model_registry.register_version(
                model_type="lstm_regime_forecaster",
                weights=None,  # weights saved separately
                metadata={
                    "best_params": best_params,
                    "best_val_loss": best_value,
                    "n_trials": n_trials,
                    "optimization_timestamp": time.time(),
                },
            )

            obs.gauge("lstm_best_val_loss", best_value)

            return {
                "best_params": best_params,
                "best_value": best_value,
                "study": self.study,
            }
