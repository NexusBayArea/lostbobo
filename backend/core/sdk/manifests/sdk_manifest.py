from __future__ import annotations

from pydantic import BaseModel


class SDKManifest(BaseModel):
    sdk_version: str
    kernel_abi_version: str
    supported_plugin_abi_versions: list[str]
    frozen_contracts: list[str]  # list of contract names, e.g., "event.v1", "dag.v1"
