from __future__ import annotations

from pydantic import BaseModel


class DeprecationNotice(BaseModel):
    contract_name: str
    deprecated_in: str  # kernel ABI version
    removed_in: str  # kernel ABI version
    replacement: str | None = None
