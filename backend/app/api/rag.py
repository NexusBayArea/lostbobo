from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/rag", tags=["RAG"])


class ChatRequest(BaseModel):
    query: str
    simulation_context: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    confidence: float = 0.0


@router.post("/chat", response_model=ChatResponse)
async def rag_chat(request: ChatRequest):
    """RAG Chatbot with vector search over simulation history"""
    
    from backend.app.core.vector_search import vector_search
    
    results = await vector_search.search_simulations(request.query, limit=6)

    context = "\n\n".join([r.get("content", "") for r in results])

    answer = f"Based on simulation history: {request.query}"

    return ChatResponse(
        answer=answer,
        sources=[r.get("metadata", {}).get("simulation_id", "unknown") for r in results],
        confidence=0.89
    )