import time
import uuid

from backend.core.world.fabric.causality import CausalityResolver
from backend.core.world.fabric.event_log import WorldEvent
from backend.core.world.fabric.immutable_store import AbstractWorldStore, InMemoryWorldStore
from backend.core.world.fabric.probabilistic_merge import ProbabilisticMergeEngine
from backend.core.world.fabric.state_diff import StateDiff
from backend.core.world.fabric.temporal_branch import TemporalBranch
from backend.core.world.fabric.uncertainty import UncertaintyEnvelope
from backend.core.world.fabric.world_snapshot import WorldSnapshot


class WorldStateFabric:
    def __init__(self, store: AbstractWorldStore = None, lineage_syscall=None):
        self.store = store or InMemoryWorldStore()
        self.causality = CausalityResolver()
        self.merger = ProbabilisticMergeEngine()
        self.events: list[WorldEvent] = []
        self.branches: dict[str, TemporalBranch] = {}
        self.lineage = lineage_syscall

    async def _emit_lineage(self, event_type: str, payload: dict):
        if self.lineage:
            await self.lineage.write_lineage(
                {"source": "world_state_fabric", "event": event_type, "payload": payload, "timestamp": time.time()}
            )

    async def create_snapshot(
        self,
        tenant_id: str,
        branch_id: str,
        state: dict,
        parent_snapshot_id: str | None = None,
        uncertainty: dict = None,
    ) -> WorldSnapshot:
        snapshot = WorldSnapshot(
            snapshot_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            timestamp=time.time(),
            branch_id=branch_id,
            parent_snapshot_id=parent_snapshot_id,
            state=state,
            uncertainty=uncertainty or {},
        )
        self.store.write_snapshot(snapshot)
        await self._emit_lineage("snapshot.created", {"snapshot_id": snapshot.snapshot_id})
        return snapshot

    def append_event(self, event: WorldEvent):
        self.events.append(event)

    async def process_events(self, up_to_event_id: str | None = None) -> WorldSnapshot:
        relevant = self.causality.resolve(self.events)
        if up_to_event_id:
            idx = next((i for i, e in enumerate(relevant) if e.event_id == up_to_event_id), len(relevant))
            relevant = relevant[: idx + 1]

        current_state = {}
        current_uncertainty = {}

        for event in relevant:
            if event.event_type == "state_diff":
                diff = StateDiff(**event.payload)
                snapshot = self.store.get_snapshot(diff.snapshot_id)
                base_state = snapshot.state if snapshot else current_state
                base_unc = snapshot.uncertainty if snapshot else current_uncertainty
                new_state = dict(base_state)
                new_uncertainty = dict(base_unc)
                for key, value in diff.changes.items():
                    new_state[key] = value
                    new_uncertainty[key] = UncertaintyEnvelope(confidence=diff.confidence)

                snapshot = await self.create_snapshot(
                    tenant_id=event.tenant_id,
                    branch_id="main",
                    state=new_state,
                    parent_snapshot_id=diff.snapshot_id,
                    uncertainty=new_uncertainty,
                )
                current_state = snapshot.state
                current_uncertainty = snapshot.uncertainty

        return await self.create_snapshot(
            tenant_id="default", branch_id="main", state=current_state, uncertainty=current_uncertainty
        )

    async def apply_diff(self, snapshot_id: str, diff: StateDiff, confidence: float = 1.0) -> WorldSnapshot:
        snapshot = self.store.get_snapshot(snapshot_id)
        if not snapshot:
            raise KeyError(f"Snapshot {snapshot_id} not found")
        merged_state = dict(snapshot.state)
        new_uncertainty = dict(snapshot.uncertainty)
        for key, value in diff.changes.items():
            if key in merged_state and isinstance(value, (int, float)) and isinstance(merged_state[key], (int, float)):
                old_val = merged_state[key]
                blended = old_val * (1 - confidence) + value * confidence
                old_unc = new_uncertainty.get(key, UncertaintyEnvelope())
                new_uncertainty[key] = UncertaintyEnvelope(
                    confidence=old_unc.confidence * confidence,
                    entropy=old_unc.entropy + (1 - confidence),
                    variance=old_unc.variance + (value - blended) ** 2,
                )
                merged_state[key] = blended
            else:
                merged_state[key] = value
                new_uncertainty[key] = UncertaintyEnvelope(confidence=confidence)
        return await self.create_snapshot(
            tenant_id=snapshot.tenant_id,
            branch_id=snapshot.branch_id,
            state=merged_state,
            parent_snapshot_id=snapshot_id,
            uncertainty=new_uncertainty,
        )

    async def probabilistic_merge(self, snapshot_a_id: str, snapshot_b_id: str, confidence: float) -> WorldSnapshot:
        a = self.store.get_snapshot(snapshot_a_id)
        b = self.store.get_snapshot(snapshot_b_id)
        if not a or not b:
            raise KeyError("Snapshot not found")
        merged_state, merged_unc = self.merger.merge(a.state, b.state, confidence, a.uncertainty, b.uncertainty)
        return await self.create_snapshot(
            tenant_id=a.tenant_id,
            branch_id=a.branch_id,
            state=merged_state,
            parent_snapshot_id=a.snapshot_id,
            uncertainty=merged_unc,
        )

    async def create_branch(self, created_by: str, parent_branch_id: str | None = None) -> TemporalBranch:
        branch = TemporalBranch(
            branch_id=str(uuid.uuid4()),
            parent_branch_id=parent_branch_id,
            created_by=created_by,
            created_at=time.time(),
        )
        self.branches[branch.branch_id] = branch
        await self._emit_lineage("branch.created", {"branch_id": branch.branch_id})
        return branch

    async def checkpoint(
        self, snapshot_id: str, replay_hash: str, scheduler_hash: str = "", dag_hash: str = ""
    ) -> ReplayCheckpoint:
        cp = ReplayCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            snapshot_id=snapshot_id,
            replay_hash=replay_hash,
            scheduler_hash=scheduler_hash,
            dag_hash=dag_hash,
            created_at=time.time(),
        )
        await self._emit_lineage("checkpoint.created", cp.dict())
        return cp
