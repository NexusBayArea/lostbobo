from abc import ABC, abstractmethod
from typing import Dict, Any

class PluginBase(ABC):
    @abstractmethod
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pass
