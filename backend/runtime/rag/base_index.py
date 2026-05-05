from abc import ABC, abstractmethod


class BaseIndex(ABC):
    def __init__(self, domain: str = "general"):
        self.domain = domain

    @abstractmethod
    async def search(self, query: str, tenant_id: str = "public", limit: int = 8) -> list[dict]: ...
