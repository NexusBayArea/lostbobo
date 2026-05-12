from __future__ import annotations

from pydantic import BaseModel


class FrozenSchemaRegistry:
    def __init__(self):
        # key: (contract_name, version), value: Pydantic model class
        self._schemas: dict[tuple[str, str], type[BaseModel]] = {}

    def register(self, contract_name: str, version: str, schema: type[BaseModel]):
        self._schemas[(contract_name, version)] = schema

    def get(self, contract_name: str, version: str) -> type[BaseModel]:
        return self._schemas.get((contract_name, version))
