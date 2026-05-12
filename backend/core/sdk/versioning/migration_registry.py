from __future__ import annotations

from collections.abc import Callable


class MigrationRegistry:
    def __init__(self):
        self._migrations: dict[tuple[str, str], Callable] = {}

    def register(self, from_version: str, to_version: str, migration_fn: Callable):
        self._migrations[(from_version, to_version)] = migration_fn

    def migrate(self, payload: dict, from_version: str, to_version: str):
        fn = self._migrations.get((from_version, to_version))
        if not fn:
            raise KeyError(f"No migration from {from_version} to {to_version}")
        return fn(payload)
