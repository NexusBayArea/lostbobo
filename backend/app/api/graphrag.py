import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.runtime.graphrag.graphrag_streamer import GraphRAGStreamer

router = APIRouter(prefix="/graphrag", tags=["GraphRAG"])

streamer = GraphRAGStreamer()


async def event_generator(question_id: str, query: str, category: str | None = None):
    async for update in streamer.stream_retrieve(question_id, query, category):
        yield f"data: {json.dumps(update)}\n\n"


@router.get("/stream")
async def stream_rag(
    question_id: str,
    query: str,
    category: str | None = None,
):
    return StreamingResponse(
        event_generator(question_id, query, category),
        media_type="text/event-stream",
    )
