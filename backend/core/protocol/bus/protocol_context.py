from __future__ import annotations

from pydantic import BaseModel


class ProtocolContext(BaseModel):
    tenant_id: str
    trace_id: str
    replay_id: Optional[str] = None
    dag_id: Optional[str] = None
    node_id: Optional[str] = None
    plugin_name: Optional[str] = None
