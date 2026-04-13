"""DAG Orchestrator with Adaptive Learning."""
import logging
from collections import deque
from typing import Any, Dict, List, Optional

# Assuming these sub-modules exist or will be created/merged
from app.core.dag.adaptive_scheduler import AdaptiveScheduler
from app.core.dag.autoscaler import AutoscalingOptimizer
from app.core.dag.metrics import SystemLoad
from app.core.dag.job import DAGJob
from app.core.dag.scale_executor import scale_executor

logger = logging.getLogger(__name__)

# FIX: cap history to avoid unbounded memory growth in long-running processes
_HISTORY_MAXLEN = 1_000


class AdaptiveDAGOrchestrator:
    """
    Main control plane with adaptive learning.
    """

    def __init__(self, history_maxlen: int = _HISTORY_MAXLEN):
        self.scheduler = AdaptiveScheduler()
        self.autoscaler = AutoscalingOptimizer()
        # FIX: use deque with maxlen instead of an unbounded list
        self.decision_history: deque = deque(maxlen=history_maxlen)

    def run_cycle(self, jobs: List[DAGJob], system_metrics: SystemLoad) -> Dict[str, Any]:
        """Run single orchestration cycle."""
        # 1. Schedule with learned policy
        scheduling_decisions = self.scheduler.schedule(jobs, system_metrics)

        # 2. Autoscale
        scale_actions = self.autoscaler.decide(system_metrics)

        # 3. Execute scaling actions
        scale_executor.apply_actions(scale_actions)

        result = {
            "decisions": scheduling_decisions,
            "scale_actions": scale_actions,
            "metrics": system_metrics,
            "policy_stats": self.scheduler.get_policy_stats(),
        }

        self.decision_history.append(result)
        return result

    def report_outcome(self, route: str, outcome: Any) -> bool:
        """
        Report execution outcome for learning.

        Args:
            route: The route identifier that was executed.
            outcome: The observed outcome to feed back into the scheduler policy.

        Returns:
            True if the feedback was accepted and applied, False otherwise.
        """
        return self.scheduler.apply_feedback(route, outcome)

    def get_stats(self) -> Dict[str, Any]:
        """Get full system stats including scheduler and autoscaler state."""
        return {
            "scheduler": self.scheduler.get_policy_stats(),
            # FIX: include autoscaler stats so callers can observe its state
            "autoscaler": self.autoscaler.get_stats(),
            "history_size": len(self.decision_history),
        }
