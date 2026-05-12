from __future__ import annotations

from pydantic import BaseModel


class DAGNodeContract(BaseModel):
    """
    FROZEN DAG node external contract v1.0.0.
    Used for serialisation/deserialisation between kernel and plugins.
    """

    node_id: str
    capability: str
    inputs: dict
    outputs: dict
    dependencies: list[str]
