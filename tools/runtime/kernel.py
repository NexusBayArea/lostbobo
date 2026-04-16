from __future__ import annotations

import sys
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set

from tools.runtime.contract import CONTRACT
from tools.runtime.capabilities import CAPABILITIES
from tools.runtime.trace import Trace


def get_state_handlers():
    from tools.runtime.capabilities import CAPABILITIES

    if not CAPABILITIES.get("state") or not CAPABILITIES["state"].enabled:
        return None, None

    try:
        from tools.runtime.state import load_state, save_state
        return load_state, save_state
    except ImportError:
        print("[WARN] state capability enabled but module missing")
        return None, None


CONTRACT.apply()

PYPROJECT = CONTRACT.root / "pyproject.toml"
LOCKFILE = CONTRACT.root / "requirements.lock"
MANIFEST = CONTRACT.root / "tools" / "ci_manifest.yml"


# ==============================
# Distributed Kernel (v2 Control Plane)
# ==============================

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
    last_error: Optional[str] = None
    lease: Optional[Lease] = None
    result: Any = None


class Queue:
    def push(self, task_id: str) -> None:
        raise NotImplementedError

    def pop(self) -> Optional[str]:
        raise NotImplementedError


class InMemoryQueue(Queue):
    def __init__(self):
        self.q = []

    def push(self, task_id: str) -> None:
        self.q.append(task_id)

    def pop(self) -> Optional[str]:
        if not self.q:
            return None
        return self.q.pop(0)


class Kernel:
    def __init__(self, queue: Queue | None = None, lease_ttl_s: int = 30):
        self.queue = queue or InMemoryQueue()
        self.lease_ttl_s = lease_ttl_s
        self.tasks: Dict[str, TaskState] = {}

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = TaskState(task=task)

    def _deps_ready(self, task: Task) -> bool:
        return all(
            dep in self.tasks and self.tasks[dep].status == "success"
            for dep in task.deps
        )

    def _enqueue_ready(self) -> None:
        for t in self.tasks.values():
            if t.status == "pending" and self._deps_ready(t):
                t.status = "queued"
                self.queue.push(t.task.id)

    def lease_task(self, worker_id: str) -> Optional[Task]:
        self._enqueue_ready()
        task_id = self.queue.pop()
        if not task_id:
            return None

        state = self.tasks[task_id]
        lease = Lease(
            task_id=task_id,
            worker_id=worker_id,
            lease_id=str(uuid.uuid4()),
            expires_at=time.time() + self.lease_ttl_s,
        )

        state.status = "leased"
        state.lease = lease
        state.attempt += 1

        return state.task

    def report_success(self, task_id: str, result: Any) -> None:
        state = self.tasks[task_id]
        state.status = "success"
        state.result = result

    def report_failure(self, task_id: str, error: str) -> None:
        state = self.tasks[task_id]
        state.last_error = error

        if state.attempt <= state.task.retries:
            state.status = "pending"
            self.queue.push(task_id)
        else:
            state.status = "failed"

    def snapshot(self) -> Dict[str, str]:
        return {k: v.status for k, v in self.tasks.items()}


class Worker:
    def __init__(self, worker_id: str, kernel: Kernel):
        self.worker_id = worker_id
        self.kernel = kernel

    def run_forever(self):
        while True:
            task = self.kernel.lease_task(self.worker_id)

            if not task:
                time.sleep(0.5)
                continue

            try:
                result = task.fn()
                self.kernel.report_success(task.id, result)

            except Exception as e:
                self.kernel.report_failure(task.id, str(e))


# ==============================
# Legacy DAG Kernel (v1 - kept for bootstrap)
# ==============================

def read_lock() -> set[str]:
    if not LOCKFILE.exists():
        raise RuntimeError("Missing requirements.lock")

    return {
        line.strip()
        for line in LOCKFILE.read_text().splitlines()
        if line.strip() and "==" in line
    }


def verify_capabilities():
    print("[KERNEL] capability validation")
    for cap in CAPABILITIES.values():
        if not cap.enabled:
            continue
        missing = [p for p in cap.required_files if not Path(p).exists()]
        if missing:
            print(f"[FAIL] capability '{cap.name}' missing files:")
            for m in missing:
                print(" ", m)
            sys.exit(1)
    print("[PASS] capabilities valid")


def validate_lock_format() -> bool:
    if not LOCKFILE.exists():
        print("[FAIL] requirements.lock not found")
        return False

    content = LOCKFILE.read_text()
    lines = content.splitlines()

    pinned = [line.strip() for line in lines if line.strip() and "==" in line]

    if not pinned:
        print("[FAIL] no pinned dependencies found in lockfile")
        return False

    unpinned = [line for line in pinned if "==" not in line]
    if unpinned:
        print(f"[FAIL] found {len(unpinned)} unpinned dependencies")
        return False

    print(f"[KERNEL] lockfile validated: {len(pinned)} pinned deps")
    return True


def validate_dependencies():
    print("[KERNEL] dependency validation")

    if not PYPROJECT.exists():
        print("[FAIL] pyproject.toml not found")
        sys.exit(1)

    if not validate_lock_format():
        sys.exit(1)

    print("[PASS] dependency kernel clean")


def validate_import(path: str) -> bool:
    p = Path(path)
    if p.exists():
        return True
    alt = CONTRACT.root / path
    if alt.exists():
        return True
    print(f"[FAIL] missing module: {path}")
    return False


def load_manifest():
    import yaml

    return yaml.safe_load(MANIFEST.read_text())


def run_node(name: str, node: dict, trace: Trace) -> int:
    path = node.get("path", "")

    if not validate_import(path):
        trace.start_node(name)
        trace.end_node(name, False)
        return 1

    trace.start_node(name)

    cmd = [sys.executable, path]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    trace.end_node(name, result.returncode == 0, result)

    return result.returncode


def execute_dag(manifest: dict, trace: Trace):
    nodes = manifest.get("nodes", {})

    executed = set()

    def run(name: str) -> int:
        if name in executed:
            return 0

        node = nodes[name]

        for dep in node.get("depends_on", []):
            if run(dep) != 0:
                return 1

        rc = run_node(name, node, trace)
        executed.add(name)
        return rc

    for name in nodes:
        if run(name) != 0:
            return 1

    return 0


def self_heal():


def validate_contract():
    print("[KERNEL] contract validation")
    required_attrs = ["root", "paths"]
    for attr in required_attrs:
        if not hasattr(CONTRACT, attr):
            print(f"[FAIL] contract missing attribute: {attr}")
            sys.exit(1)
    print("[PASS] contract valid")
    print("[KERNEL] self-heal phase")

    required = [
        "tools/deps/verify_fingerprint.py",
        "tools/deps/dependency_scan.py",
        "tools/ci_gates/system_contract.py",
    ]

    missing = [p for p in required if not Path(p).exists()]

    if missing:
        print("[FAIL] missing kernel modules:")
        for m in missing:
            print(" ", m)
        sys.exit(1)

    print("[PASS] kernel integrity complete")


def main():
    print("[KERNEL] boot sequence start")

    trace = Trace()
    verify_capabilities()
    validate_dependencies()
    self_heal()
    validate_contract()

    manifest = load_manifest()
    rc = execute_dag(manifest, trace)
    trace.save()

    if rc != 0:
        print(f"[FAIL] DAG execution failed with code {rc}")
        sys.exit(rc)

    print("[KERNEL] boot sequence complete")


if __name__ == "__main__":
    main()