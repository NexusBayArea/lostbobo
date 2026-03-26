from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import os
import json
from app.rag import query_rag
from vllm import LLM, SamplingParams

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


# Preload LLM (Worker Boot)
# Note: Using small model for Alpha efficiency. Point to your network volume.
MODEL_PATH = os.getenv("MODEL_PATH", "/workspace/models/mistral-7b-v0.1")
print(f"Loading vLLM model from {MODEL_PATH}...")

# Check if model exists before loading to prevent crash during setup
if os.path.exists(MODEL_PATH):
    llm = LLM(model=MODEL_PATH, trust_remote_code=True)
else:
    print(f"CRITICAL: Model not found at {MODEL_PATH}")
    llm = None


class ChatRequest(BaseModel):
    question: str
    max_tokens: int = 300
    temperature: float = 0.2


class HealthCheckRequest(BaseModel):
    check_health_only: bool = False
