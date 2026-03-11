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

@app.post("/chat", dependencies=[Depends(get_api_key)])
def chat(req: ChatRequest):
    if llm is None:
        raise HTTPException(status_code=503, detail="LLM engine not initialized (model missing)")

    # 1. RAG Context Retrieval
    context = query_rag(req.question)

    # 2. Prompt Engineering
    prompt = f"""[INST] You are the SimHPC Engineering Assistant. Use the provided context to answer the question accurately.

Context:
{context}

Question:
{req.question} [/INST]"""

    # 3. vLLM Generation
    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    
    outputs = llm.generate([prompt], sampling_params)
    answer = outputs[0].outputs[0].text

    return {
        "answer": answer,
        "model": MODEL_PATH.split("/")[-1],
        "context_used": len(context) > 0
    }

@app.get("/health")
def health():
    return {"status": "ready", "llm_loaded": llm is not None}
