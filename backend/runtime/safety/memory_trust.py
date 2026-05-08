from typing import Any


class MemoryTrustWeights:
    def __init__(self, kernel):
        self.kernel = kernel

    async def validate_write(self, payload: dict[str, Any]):
        pass
