from __future__ import annotations

from pydantic import BaseModel


class DAGNodeContract(BaseModel):
    node_id: str
    capability: str
    inputs: dict
    outputs: dict
    dependencies: list[str]
