from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.core.kernel.commands.compliance_commands import LogAuditCommand
from backend.core.kernel.kernel import Kernel as _Kernel
from backend.ml.inference.physics_api import (
    ModelSource,
    PhysicsInferenceRequest,
    get_physics_inference_api,
)
from backend.ml.registry import get_model_status
from backend.ml.training.exporter import QualityThresholds, TrainingDataExporter
from backend.ml.training.finetuner import FineTuningConfig, FinetuningPipeline

router = APIRouter(prefix="/ml", tags=["ml"])


class ExportRequest(BaseModel):
    quality_level: str = "production"
    domain: str | None = None
    max_examples: int = 100_000
    format: str = "openai"


class TrainRequest(BaseModel):
    base_model: str = "microsoft/phi-3-mini-4k-instruct"
    lora_r: int = 16
    num_epochs: int = 3
    learning_rate: float = 5e-4
    batch_size: int = 8


class InferenceRequest(BaseModel):
    task_type: str
    domain: str
    solver: str = "MFEM"
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024
    prefer_model: str = "simhpc_fine_tuned"


@router.get("/dataset/stats")
async def get_dataset_stats(domain: str | None = None):
    exporter = TrainingDataExporter()
    stats = await exporter.get_dataset_stats(domain=domain)
    return {"status": "ok", "data": stats}


@router.post("/export")
async def trigger_export(request: ExportRequest, background_tasks: BackgroundTasks):
    thresholds = (
        QualityThresholds.production() if request.quality_level == "production" else QualityThresholds.permissive()
    )
    exporter = TrainingDataExporter(thresholds=thresholds)

    async def export_task():
        try:
            await exporter.export(
                output_dir="./training_data",
                format=request.format,
                max_examples=request.max_examples,
                domain=request.domain,
            )
        except Exception as e:
            print(f"[ML Export] Failed: {e}")

    background_tasks.add_task(export_task)
    return {"status": "EXPORT_QUEUED", "message": "Training data export started."}


@router.post("/train")
async def trigger_training(request: TrainRequest, background_tasks: BackgroundTasks):
    config = FineTuningConfig(
        base_model=request.base_model,
        lora_r=request.lora_r,
        num_train_epochs=request.num_epochs,
        learning_rate=request.learning_rate,
        batch_size=request.batch_size,
    )

    async def training_task():
        try:
            pipeline = FinetuningPipeline(config)
            await pipeline.prepare_training_data()
            await pipeline.train()
            checkpoint = await pipeline.save_checkpoint()
            print(f"[ML Training] Completed: {checkpoint}")
        except Exception as e:
            print(f"[ML Training] Failed: {e}")

    background_tasks.add_task(training_task)
    return {"status": "TRAINING_QUEUED", "base_model": request.base_model}


@router.get("/model/status")
async def model_status():
    return await get_model_status()


@router.get("/model/benchmark")
async def model_benchmark():
    from backend.ml.registry import create_mock_benchmark, get_model_status

    status = await get_model_status()
    if status.get("status") == "NO_MODELS":
        mock = create_mock_benchmark("v0", 0)
        return {"status": "MOCK", "benchmark": mock.to_dict()}
    return status


@router.get("/model/compare")
async def compare_models(a: str, b: str):
    from backend.ml.registry import ModelRegistry

    registry = ModelRegistry()
    return await registry.compare_models(a, b)


@router.get("/models")
async def list_models():
    from backend.ml.registry import ModelRegistry

    registry = ModelRegistry()
    versions = await registry.list_versions()
    return {"versions": [asdict(v) for v in versions]}


@router.post("/models/{version_id}/activate")
async def activate_model(version_id: str):
    from backend.ml.registry import ModelRegistry

    registry = ModelRegistry()
    success = await registry.set_active_version(version_id)
    return {"success": success, "active_version": version_id}


@router.get("/inference/recent")
async def get_recent_inferences(limit: int | None = None):
    from backend.ml.inference.physics_api import get_physics_inference_api

    api = get_physics_inference_api()
    raw = api.get_recent_inferences(limit=limit or 15)
    return {"inferences": raw}


@router.post("/infer")
async def run_physics_inference(request: InferenceRequest, version: str | None = None):
    try:
        model_source = ModelSource(request.prefer_model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid model: {request.prefer_model}") from e

    api = get_physics_inference_api()
    inference_req = PhysicsInferenceRequest(
        task_type=request.task_type,
        domain=request.domain,
        solver=request.solver,
        prompt=request.prompt,
        prefer_model=model_source,
    )

    response = await api.infer(inference_req, version_id=version)
    kernel = _Kernel()
    await kernel.execute(
        LogAuditCommand(
            event_type="PHYSICS_INFERENCE",
            outcome="SUCCESS",
            tenant_id="system",
            user_id="system",
            user_email="system@simhpc.com",
            user_role="engineer",
            resource_type="physics_inference",
            resource_id=request.task_type,
            resource_classification="PUBLIC",
            action=f"Physics inference: {request.task_type}",
            details={"confidence": response.confidence_score, "model_used": response.model_used},
        )
    )
    return {
        "completion": response.completion,
        "confidence_score": response.confidence_score,
        "brier_score": response.brier_score,
        "model_used": response.model_used,
        "latency_ms": response.latency_ms,
        "tokens_generated": response.tokens_generated,
        "source_data_runs": response.source_data_runs,
        "fallback_used": response.fallback_used,
    }


@router.get("/health")
async def ml_health():
    status = await get_model_status()
    exporter = TrainingDataExporter()
    dataset = await exporter.get_dataset_stats()
    return {"status": "HEALTHY", "model": status, "dataset": dataset}
