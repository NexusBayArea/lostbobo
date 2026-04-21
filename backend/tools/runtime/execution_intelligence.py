from __future__ import annotations

from dataclasses import dataclass

from tools.runtime.contract import CONTRACT
from tools.runtime.execution_log import ExecutionLog


@dataclass
class DAGNode:
    id: str
    deps: set[str]


class DAGValidator:
    def __init__(self, nodes: dict[str, DAGNode]):
        self.nodes = nodes

    def validate_no_missing_deps(self) -> list[tuple[str, str]]:
        missing = []

        for node_id, node in self.nodes.items():
            for dep in node.deps:
                if dep not in self.nodes:
                    missing.append((node_id, dep))

        return missing

    def validate_no_cycles(self) -> bool:
        visited = set()
        stack = set()

        def dfs(nid: str) -> bool:
            if nid in stack:
                return False
            if nid in visited:
                return True

            stack.add(nid)

            for dep in self.nodes[nid].deps:
                if dep in self.nodes:
                    if not dfs(dep):
                        return False

            stack.remove(nid)
            visited.add(nid)
            return True

        for n in self.nodes:
            if not dfs(n):
                return False

        return True


class ContractGuard:
    def validate_import(self, module: str) -> bool:
        return CONTRACT.is_allowed_import(module)

    def validate_root(self, path: str) -> bool:
        return CONTRACT.is_allowed_root(path)


class ReplayComparator:
    def __init__(self, log: ExecutionLog):
        self.log = log

    def expected_order(self, nodes: dict[str, DAGNode]) -> list[str]:
        """
        Topological expectation (simplified DFS order)
        """
        visited = set()
        order = []

        def visit(n):
            if n in visited:
                return
            visited.add(n)

            for d in nodes[n].deps:
                if d in nodes:
                    visit(d)

            order.append(n)

        return order

    def actual_order(self) -> list[str]:
        events = self.log.events

        return [e["task_id"] for e in events if e["type"] in ("queued", "leased", "success")]

    def detect_divergence(self, nodes: dict[str, DAGNode]):
        expected = self.expected_order(nodes)
        actual = self.actual_order()

        return {
            "expected": expected,
            "actual": actual,
            "divergence": expected != actual,
        }


class ExecutionIntelligence:
    def __init__(self, log: ExecutionLog):
        self.log = log
        self.guard = ContractGuard()

    def validate_dag(self, nodes: dict[str, DAGNode]):
        validator = DAGValidator(nodes)

        missing = validator.validate_no_missing_deps()
        cyclic = validator.validate_no_cycles()

        return {
            "missing_dependencies": missing,
            "acyclic": cyclic,
            "valid": len(missing) == 0 and cyclic,
        }

    def analyze_execution(self, nodes: dict[str, DAGNode]):
        comparator = ReplayComparator(self.log)

        dag_result = self.validate_dag(nodes)
        replay_result = comparator.detect_divergence(nodes)

        return {
            "dag": dag_result,
            "replay": replay_result,
            "contract": {
                "entrypoints": CONTRACT.entrypoints,
                "allowed_roots": list(CONTRACT.allowed_roots),
                "forbidden_prefixes": list(CONTRACT.forbidden_prefixes),
            },
        }
