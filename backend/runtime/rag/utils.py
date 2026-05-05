from typing import Any


def get_tenant_from_context() -> str:
    """Logic to extract tenant_id from request context or global state."""
    return "public"


async def embed_text(text: str) -> list[float]:
    """Shared embedding helper. Currently a placeholder returning 1536 zeros."""
    # TODO: Implement real embedding logic (OpenAI, HuggingFace, etc.)
    return [0.0] * 1536


def combine_results(results: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Flatten and deduplicate results from multiple sources."""
    combined = []
    seen = set()
    for batch in results:
        if not batch or not isinstance(batch, list):
            continue
        for item in batch:
            # Try multiple common ID keys
            key = item.get("id") or item.get("chunk_id") or item.get("hash")
            if key and key not in seen:
                seen.add(key)
                combined.append(item)
    return combined
