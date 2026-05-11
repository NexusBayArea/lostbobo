"""
backend/runtime/flywheel/jobs/embed_chunks.py
────────────────────────────────────────────
Periodic embedding job — runs every 5 minutes.
"""

import logging

from backend.core.embedding.service import embedding_service

log = logging.getLogger(__name__)


async def run_embedding_job():
    """Main entry point called by Flywheel scheduler."""
    try:
        count = await embedding_service.process_unembedded_chunks(batch_size=80)
        if count > 0:
            log.info("Embedding job processed %d chunks", count)
        else:
            log.debug("Embedding job — no work needed")
    except Exception as e:
        log.error("Embedding job failed: %s", e)
