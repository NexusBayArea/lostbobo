from __future__ import annotations

from pydantic import BaseModel


class ProtocolContext(BaseModel):
    tenant_id: str
    trace_id: str
    replay_id: str | None = None
    dag_id: str | None = None
    node_id: str | None = None
    plugin_name: str | None = None
