from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    @abstractmethod
    async def run(self, params: dict[str, Any]) -> dict[str, Any]:
        pass
