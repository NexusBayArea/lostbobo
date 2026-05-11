from fastapi import APIRouter

from backend.app.core.supabase import get_supabase_client
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


@router.post("/embed/reprocess-dead-letter")
async def reprocess_dead_letter(max_retries: int = 3):
    """
    Reprocess chunks from the dead-letter queue.
    """
    count = await embedding_service.reprocess_dead_letter(max_retries=max_retries)
    return {
        "status": "success",
        "chunks_reprocessed": count,
        "message": f"Reprocessed {count} chunks from dead-letter queue",
    }


@router.get("/embed/dead-letter-stats")
async def get_dead_letter_stats():
    sb = get_supabase_client()
    if not sb:
        return {"total": 0, "retry_0": 0, "retry_1": 0, "retry_2plus": 0}

    # Simple stats query
    resp = sb.table("document_chunks_dead_letter").select("retry_count, last_attempt").execute()
    data = resp.data or []
    counts = [r["retry_count"] for r in data]

    return {
        "total": len(counts),
        "retry_0": counts.count(0),
        "retry_1": counts.count(1),
        "retry_2plus": sum(1 for c in counts if c >= 2),
        "last_attempt": max((r.get("last_attempt") for r in data), default=None),
    }
