from fastapi import APIRouter

from backend.core.embedding.service import embedding_service

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/embed")
async def trigger_manual_embedding():
    """Manually trigger embedding of all unembedded chunks."""
    count = await embedding_service.process_unembedded_chunks(batch_size=100)
    return {
        "status": "success",
        "chunks_processed": count,
        "message": f"Embedding job completed — {count} chunks processed",
    }
