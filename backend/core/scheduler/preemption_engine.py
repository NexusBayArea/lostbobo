from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.scheduler.scheduler_models import Workload


class PreemptionEngine:
    def select_victim(self, incoming: Workload, running: list) -> int | None:
        """
        running: list of tuples (index, workload) of currently scheduled jobs.
        Returns index of victim if any, else None.
        """
        priority_map = {"critical": 4, "high": 3, "normal": 2, "low": 1}
        incoming_prio = priority_map[incoming.priority.value]
        for idx, wl in running:
            if incoming_prio > priority_map[wl.priority.value]:
                return idx
        return None
