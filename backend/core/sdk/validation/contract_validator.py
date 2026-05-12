from __future__ import annotations

from pydantic import BaseModel


class ContractValidator:
    @staticmethod
    def validate(payload: dict, schema: type[BaseModel]) -> BaseModel:
        """Validate a payload against a frozen schema and return a validated instance."""
        return schema.model_validate(payload)
