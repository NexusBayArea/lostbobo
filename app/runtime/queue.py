"""
Task Queue — Simple in-memory queue for distributed-ready execution

Provides backpressure and decoupled execution foundation.
"""

from collections import deque
from typing import Any, Optional


class TaskQueue:
    def __init__(self):
        self.q = deque()

    def push(self, task: Any) -> None:
        self.q.append(task)

    def pop(self) -> Optional[Any]:
        if self.q:
            return self.q.popleft()
        return None

    def empty(self) -> bool:
        return len(self.q) == 0

    def __len__(self) -> int:
        return len(self.q)
