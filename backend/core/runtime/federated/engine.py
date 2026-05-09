from __future__ import annotations

from typing import Any

from backend.core.runtime.entity_graph.federated import FederatedGNNEngine
from backend.core.runtime.event_fabric.log import EventLogService
from backend.core.runtime.event_fabric.schema import SimHPCEvent
from backend.core.runtime.federated.algorithms import FederatedAlgorithms
from backend.core.runtime.state_registry.service import StateRegistryService
from backend.core.services.observability_service import observability
from backend.core.tracing import trace_context


class FederatedEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def engine(cls) -> FederatedEngine:
        return cls()

    async def run_round(
        self, participants: list[str], algorithm: str = "temporal_fedavg", rounds: int = 1
    ) -> dict[str, Any]:
        """Orchestrate one or more federated rounds."""
        with trace_context("federated.run_round", {"algorithm": algorithm}):
            obs = observability()
            obs.increment("federated_rounds_total")

            state = await StateRegistryService.registry().get_current()
            all_updates = []

            for _ in range(rounds):
                round_updates = []
                for pid in participants:
                    local_update = await self._collect_local_update(pid, state)
                    round_updates.append(local_update)
                all_updates.extend(round_updates)

            # Dispatch to chosen algorithm
            if algorithm == "temporal_fedavg":
                result = await FederatedAlgorithms.algorithms().temporal_fedavg(all_updates, state)
            elif algorithm == "scaffold":
                result = await FederatedAlgorithms.algorithms().scaffold(all_updates, {})
            else:
                result = await FederatedAlgorithms.algorithms().fedavg(all_updates)

            # Publish global model update event
            await EventLogService.event_log().publish(
                SimHPCEvent(
                    event_type="federated.round_completed",
                    source_plugin="kernel",
                    payload={"algorithm": algorithm, "participants": participants},
                )
            )

            return result

    async def _collect_local_update(self, participant_id: str, state: Any) -> dict[str, Any]:
        return await FederatedGNNEngine.federated().local_update(participant_id, None, state)
