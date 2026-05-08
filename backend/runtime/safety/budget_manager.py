from typing import Any


class RetryBudgetManager:
    def __init__(self, kernel):
        self.kernel = kernel

    async def check(self, payload: dict[str, Any]) -> Any:
        return type("obj", (object,), {"safe": True})()
