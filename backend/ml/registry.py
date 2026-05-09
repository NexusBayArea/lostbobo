from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.core.supabase import get_supabase_client


@dataclass
class BenchmarkTask:
    task_name: str
    examples_count: int
    accuracy: float
    latency_ms: float
    tokens_per_second: float
    improvement_vs_base: float
    notes: str = ""


@dataclass
class ModelBenchmark:
    model_id: str
    version: str
    base_model: str
    created_at: str
    trained_on_runs: int
    training_domains: list[str]
    benchmark_date: str
    hypothesis_verification: BenchmarkTask
    parameter_prediction: BenchmarkTask
    uncertainty_quantification: BenchmarkTask
    sensitivity_analysis: BenchmarkTask
    mean_accuracy: float
    mean_latency_ms: float
    mean_improvement_vs_base: float
    model_size_mb: float
    inference_memory_mb: float
    inference_throughput: int

    def get_overall_score(self) -> float:
        return (
            0.5 * self.mean_accuracy
            + 0.3 * (1.0 - min(self.mean_latency_ms / 1000, 1.0))
            + 0.2 * min(self.mean_improvement_vs_base / 50, 1.0)
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModelVersion:
    """Full model version record with provenance."""

    version_id: str
    semver: str
    base_model: str
    created_at: str
    trained_on_runs: int
    training_data_hash: str
    lora_config: dict[str, Any]
    benchmark: ModelBenchmark
    overall_score: float
    status: str = "ACTIVE"
    notes: str = ""
    deployed_at: str | None = None
    deployed_by: str = "system"


class ModelRegistry:
    def __init__(self, registry_dir: str = "./model_registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._db = get_supabase_client()
        self._models: list[ModelBenchmark] = []
        self._versions: dict[str, ModelVersion] = {}

    async def register_version(
        self,
        benchmark: ModelBenchmark,
        lora_config: dict[str, Any],
        training_data_hash: str | None = None,
        notes: str = "",
    ) -> ModelVersion:
        """Register a new model version with full provenance."""
        version_id = f"v{datetime.now(UTC).strftime('%Y%m%d')}-{self._get_version_count() + 1:03d}"
        semver = f"0.{self._get_version_count() + 1}.0"

        if not training_data_hash:
            training_data_hash = "pending"

        version = ModelVersion(
            version_id=version_id,
            semver=semver,
            base_model=benchmark.base_model,
            created_at=datetime.now(UTC).isoformat(),
            trained_on_runs=benchmark.trained_on_runs,
            training_data_hash=training_data_hash,
            lora_config=lora_config,
            benchmark=benchmark,
            overall_score=benchmark.get_overall_score(),
            notes=notes,
        )

        version_dir = self.registry_dir / version_id
        version_dir.mkdir(parents=True, exist_ok=True)

        with open(version_dir / "version.json", "w") as f:
            json.dump(asdict(version), f, indent=2)

        if self._db:
            self._db.table("model_versions").upsert(
                {
                    "version_id": version.version_id,
                    "semver": version.semver,
                    "created_at": version.created_at,
                    "benchmark_data": asdict(benchmark),
                    "overall_score": version.overall_score,
                    "training_data_hash": version.training_data_hash,
                    "status": version.status,
                    "notes": version.notes,
                },
                on_conflict="version_id",
            ).execute()

        self._versions[version_id] = version
        return version

    async def get_version(self, version_id: str) -> ModelVersion | None:
        """Load specific model version."""
        if version_id in self._versions:
            return self._versions[version_id]

        if self._db:
            result = self._db.table("model_versions").select("*").eq("version_id", version_id).single().execute()
            if result.data:
                return ModelVersion(**result.data[0])

        return None

    async def get_active_version(self) -> ModelVersion | None:
        """Get the current active version."""
        if self._db:
            result = (
                self._db.table("model_versions")
                .select("*")
                .eq("status", "ACTIVE")
                .order("overall_score", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return ModelVersion(**result.data[0])
        return None

    async def list_versions(self, limit: int = 20) -> list[ModelVersion]:
        """List all versions with performance trend."""
        if self._db:
            result = self._db.table("model_versions").select("*").order("created_at", desc=True).limit(limit).execute()
            return [ModelVersion(**row) for row in (result.data or [])]
        return list(self._versions.values())

    async def set_active_version(self, version_id: str) -> bool:
        """Mark a version as active (archive all others)."""
        if not self._db:
            return False
        self._db.table("model_versions").update({"status": "ARCHIVED"}).neq("version_id", version_id).execute()
        self._db.table("model_versions").update({"status": "ACTIVE"}).eq("version_id", version_id).execute()
        return True

    def _get_version_count(self) -> int:
        if self._db:
            result = self._db.table("model_versions").select("version_id", count="exact").execute()
            return result.count or 0
        return len(self._versions)

    async def compute_training_data_hash(self, data_dir: str) -> str:
        """Deterministic SHA256 hash of training dataset for reproducibility."""
        hasher = hashlib.sha256()
        path = Path(data_dir)
        for file in sorted(path.glob("*.jsonl")):
            hasher.update(file.read_bytes())
        return hasher.hexdigest()

    async def auto_rollback_if_needed(self, threshold: float = 0.65) -> dict[str, Any]:
        """
        Automatic rollback if latest model score drops below threshold.
        Rolls back to the best previous version and logs the event.
        """
        versions = await self.list_versions(limit=10)
        if len(versions) < 2:
            return {"action": "NONE", "reason": "Not enough versions"}

        latest = versions[0]
        previous = max(versions[1:], key=lambda v: v.overall_score)

        if latest.overall_score < threshold:
            await self.set_active_version(previous.version_id)

            try:
                from backend.core.kernel.commands.compliance_commands import LogAuditCommand
                from backend.core.kernel.kernel import Kernel

                kernel = Kernel()
                await kernel.execute(
                    LogAuditCommand(
                        event_type="MODEL_ROLLBACK",
                        outcome="SUCCESS",
                        tenant_id="system",
                        user_id="system",
                        user_email="system@simhpc.com",
                        user_role="simhpc_admin",
                        resource_type="model",
                        resource_id=latest.version_id,
                        resource_classification="PUBLIC",
                        action=f"Auto-rollback from {latest.version_id} to {previous.version_id}",
                        details={
                            "old_score": latest.overall_score,
                            "new_score": previous.overall_score,
                            "threshold": threshold,
                            "reason": "Poor performance detected",
                        },
                    )
                )
            except Exception:
                pass

            return {
                "action": "ROLLBACK",
                "from_version": latest.version_id,
                "to_version": previous.version_id,
                "old_score": latest.overall_score,
                "new_score": previous.overall_score,
            }

        return {"action": "NONE", "reason": "Performance within acceptable range"}

    async def get_latest_model(self) -> ModelBenchmark | None:
        if not self._models:
            await self._load_registry()

        if not self._models:
            return None

        self._models.sort(key=lambda m: m.get_overall_score(), reverse=True)
        return self._models[0]

    async def get_model_by_version(self, version: str) -> ModelBenchmark | None:
        if not self._models:
            await self._load_registry()
        return next((m for m in self._models if m.version == version), None)

    async def compare_models(self, model_a_version: str, model_b_version: str) -> dict[str, Any]:
        a = await self.get_model_by_version(model_a_version)
        b = await self.get_model_by_version(model_b_version)

        if not a or not b:
            return {"status": "ERROR", "reason": "Model not found"}

        return {
            "model_a": {
                "version": a.version,
                "mean_accuracy": a.mean_accuracy,
                "mean_latency_ms": a.mean_latency_ms,
                "overall_score": a.get_overall_score(),
            },
            "model_b": {
                "version": b.version,
                "mean_accuracy": b.mean_accuracy,
                "mean_latency_ms": b.mean_latency_ms,
                "overall_score": b.get_overall_score(),
            },
            "accuracy_difference": round(a.mean_accuracy - b.mean_accuracy, 4),
            "latency_difference_ms": round(a.mean_latency_ms - b.mean_latency_ms, 2),
            "winner": "A"
            if a.get_overall_score() > b.get_overall_score()
            else ("B" if b.get_overall_score() > a.get_overall_score() else "TIE"),
        }

    async def get_performance_trend(self) -> list[dict[str, Any]]:
        if not self._models:
            await self._load_registry()

        models_by_date = sorted(self._models, key=lambda m: m.created_at)

        return [
            {
                "version": m.version,
                "date": m.created_at,
                "trained_on_runs": m.trained_on_runs,
                "mean_accuracy": round(m.mean_accuracy, 4),
                "mean_improvement_vs_base": round(m.mean_improvement_vs_base, 2),
                "overall_score": round(m.get_overall_score(), 4),
            }
            for m in models_by_date
        ]

    async def _load_registry(self) -> None:
        for model_dir in self.registry_dir.glob("*"):
            bench_file = model_dir / "benchmark.json"
            if bench_file.exists():
                with open(bench_file) as f:
                    self._models.append(json.load(f))

        if self._db:
            result = (
                self._db.table("model_registry")
                .select("benchmark_data")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
            if result.data:
                for row in result.data:
                    if "benchmark_data" in row:
                        self._models.append(row["benchmark_data"])


def create_mock_benchmark(version: str, trained_on_runs: int) -> ModelBenchmark:
    base_accuracy = 0.60
    improvement_factor = min(1.0, trained_on_runs / 10000)
    accuracy_boost = 0.25 * improvement_factor

    return ModelBenchmark(
        model_id=f"simhpc-physics-{version}",
        version=version,
        base_model="phi-3-mini",
        created_at=datetime.now(UTC).isoformat(),
        trained_on_runs=trained_on_runs,
        training_domains=["structural", "thermal", "ev_battery"],
        benchmark_date=datetime.now(UTC).isoformat(),
        hypothesis_verification=BenchmarkTask(
            task_name="Hypothesis Verification",
            examples_count=500,
            accuracy=min(0.95, base_accuracy + accuracy_boost + 0.12),
            latency_ms=245,
            tokens_per_second=180,
            improvement_vs_base=15.0 + (trained_on_runs / 1000),
        ),
        parameter_prediction=BenchmarkTask(
            task_name="Parameter Prediction",
            examples_count=400,
            accuracy=min(0.92, base_accuracy + accuracy_boost + 0.10),
            latency_ms=320,
            tokens_per_second=160,
            improvement_vs_base=18.0 + (trained_on_runs / 500),
        ),
        uncertainty_quantification=BenchmarkTask(
            task_name="Uncertainty Quantification",
            examples_count=300,
            accuracy=min(0.88, base_accuracy + accuracy_boost + 0.08),
            latency_ms=280,
            tokens_per_second=170,
            improvement_vs_base=8.0 + (trained_on_runs / 2000),
        ),
        sensitivity_analysis=BenchmarkTask(
            task_name="Sensitivity Analysis",
            examples_count=350,
            accuracy=min(0.91, base_accuracy + accuracy_boost + 0.09),
            latency_ms=290,
            tokens_per_second=165,
            improvement_vs_base=15.0 + (trained_on_runs / 1000),
        ),
        mean_accuracy=round((0.70 + 0.75 + 0.68 + 0.72 + accuracy_boost * 4) / 4, 4),
        mean_latency_ms=283.75,
        mean_improvement_vs_base=round(14 + (trained_on_runs / 1000), 2),
        model_size_mb=3800,
        inference_memory_mb=6400,
        inference_throughput=12,
    )


async def get_model_status() -> dict[str, Any]:
    registry = ModelRegistry()
    latest = await registry.get_latest_model()
    trend = await registry.get_performance_trend()

    if not latest:
        return {
            "status": "NO_MODELS",
            "message": "No fine-tuned models yet. Run training pipeline.",
        }

    return {
        "status": "ACTIVE",
        "latest_model": {
            "version": latest.version,
            "created_at": latest.created_at,
            "trained_on_runs": latest.trained_on_runs,
            "mean_accuracy": latest.mean_accuracy,
            "overall_score": round(latest.get_overall_score(), 4),
        },
        "performance_trend": trend[-5:],
        "moat_strength": (
            "STRONG" if latest.trained_on_runs >= 5000 else "GROWING" if latest.trained_on_runs >= 1000 else "BUILDING"
        ),
        "next_training_recommended_at": latest.trained_on_runs + 1000,
    }
