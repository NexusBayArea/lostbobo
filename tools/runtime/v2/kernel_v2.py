from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set

from tools.runtime.v2.persistent_queue import PersistentQueue
from tools.runtime.v2.execution_log import ExecutionLog


@dataclass
class Task:
    id: str
    fn: Callable[..., Any]
    deps: Set[str] = field(default_factory=set)
    retries: int = 0


@dataclass
class Lease:
    task_id: str
    worker_id: str
    lease_id: str
    expires_at: float


@dataclass
class TaskState:
    task: Task
    status: str = "pending"
    attempt: int = 0
    result: Any = None
    error: Optional[str] = None
    lease: Optional[Lease] = None


class KernelV2:
    def __init__(self, lease_ttl_s: int = 30):
        self.queue = PersistentQueue()
        self.log = ExecutionLog()

        self.tasks: Dict[str, TaskState] = {}
        self.lease_ttl_s = lease_ttl_s

    # -------------------------
    # task registration
    # -------------------------
    def add_task(self, task: Task):
        self.tasks[task.id] = TaskState(task=task)
        self.log.log("task_registered", task.id)

    # -------------------------
    # dependency resolution
    # -------------------------
    def _deps_ready(self, task: Task) -> bool:
        return all(
            dep in self.tasks and self.tasks[dep].status == "success"
            for dep in task.deps
        )

    def _enqueue_ready(self):
        for state in self.tasks.values():
            if state.status == "pending" and self._deps_ready(state.task):
                state.status = "queued"
                self.queue.push(state.task.id)
                self.log.log("queued", state.task.id)

    # -------------------------
    # leasing
    # -------------------------
    def lease_task(self, worker_id: str) -> Optional[Task]:
        self._enqueue_ready()

        task_id = self.queue.pop()
        if not task_id:
            return None

        state = self.tasks[task_id]

        state.status = "leased"
        state.attempt += 1

        lease = Lease(
            task_id=task_id,
            worker_id=worker_id,
            lease_id=str(uuid.uuid4()),
            expires_at=time.time() + self.lease_ttl_s,
        )

        state.lease = lease
        self.log.log("leased", task_id, {"worker": worker_id})

        return state.task

    # -------------------------
    # completion
    # -------------------------
    def report_success(self, task_id: str, result: Any):
        state = self.tasks[task_id]
        state.status = "success"
        state.result = result
        self.log.log("success", task_id)

    def report_failure(self, task_id: str, error: str):
        state = self.tasks[task_id]
        state.error = error

        self.log.log("failure", task_id, {"error": error})

        if state.attempt <= state.task.retries:
            state.status = "pending"
            self.queue.push(task_id)
            self.log.log("retry", task_id)
        else:
            state.status = "failed"
            self.log.log("dead", task_id)

    # -------------------------
    # observability
    # -------------------------
    def snapshot(self) -> dict[str, str]:
        return {k: v.status for k, v in self.tasks.items()}

    def recover_unfinished(self):
        """
        Requeue tasks that were leased but not completed.
        Call on startup.
        """
        for task_id, state in self.tasks.items():
            if state.status == "leased":
                state.status = "pending"
                self.queue.push(task_id)
                self.log.log("recovered", task_id)
