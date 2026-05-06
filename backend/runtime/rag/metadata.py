"""Common RAG metadata and filtering utilities."""

from __future__ import annotations


def apply_tenant_filter(tenant_id: str = "public") -> dict[str, str]:
    """Return tenant filter clause."""
    return {"tenant_id": tenant_id}


def apply_metadata_filter(filters: dict) -> dict:
    """Apply metadata filters to query."""
    return filters