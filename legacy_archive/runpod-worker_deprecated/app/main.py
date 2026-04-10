from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os
from app.rag import query_rag

app = FastAPI(title="SimHPC Alpha LLM Service")

# Security: API Key Middleware
API_KEY = os.getenv("SIMHPC_KEY", "alpha-secret-key")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Missing API Key")
    # Handle both "Bearer <key>" and raw "<key>"
    token = api_key.replace("Bearer ", "") if "Bearer " in api_key else api_key
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return token


# Model Config
MODEL_PATH = os.getenv("MODEL_PATH", "/workspace/models/mistral-7b-v0.1")
_llm = None

def get_llm():
    """Lazy-load the vLLM engine."""
    global _llm
    if _llm is None:
        if os.path.exists(MODEL_PATH):
            from vllm import LLM
            print(f"Loading vLLM model from {MODEL_PATH}...")
            _llm = LLM(model=MODEL_PATH, trust_remote_code=True)
        else:
            print(f"CRITICAL: Model not found at {MODEL_PATH}")
    return _llm


class ChatRequest(BaseModel):
    question: str
    max_tokens: int = 300
    temperature: float = 0.2


@app.post("/chat", dependencies=[Depends(get_api_key)])
def chat(req: ChatRequest):
    llm = get_llm()
    if llm is None:
        raise HTTPException(
            status_code=503, detail=f"LLM engine not initialized (model missing at {MODEL_PATH})"
        )

    # 1. RAG Context Retrieval
    context = query_rag(req.question)

    # 2. Prompt Engineering
    prompt = f"""[INST] You are the SimHPC Engineering Assistant. Use the provided context to answer the question accurately.

Context:
{context}

Question:
{req.question} [/INST]"""

    # 3. vLLM Generation
    from vllm import SamplingParams
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens, temperature=req.temperature
    )

    outputs = llm.generate([prompt], sampling_params)
    answer = outputs[0].outputs[0].text

    return {
        "answer": answer,
        "model": MODEL_PATH.split("/")[-1],
        "context_used": len(context) > 0,
    }


@app.post("/runsync", dependencies=[Depends(get_api_key)])
async def runsync(input_data: dict):
    """
    RunPod runsync endpoint handler.
    Supports metadata-only health check to avoid GPU costs.
    """
    inputs = input_data.get("input", {})

    # Alpha Health Check Guard (Metadata-Only Ping)
    if inputs.get("check_health_only"):
        return {
            "status": "ready",
            "worker_id": os.environ.get("RUNPOD_POD_ID", "unknown"),
        }

    # Simulation placeholder
    return {
        "status": "complete",
        "result": "Simulation complete - placeholder",
        "worker_id": os.environ.get("RUNPOD_POD_ID", "unknown"),
    }


@app.get("/health")
def health():
    return {"status": "ready", "llm_loaded": _llm is not None}
