from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class BranchType(str, Enum):
    MAIN = "main"
    EXPERIMENT = "experiment"
    SIMULATION = "simulation"
    WHAT_IF = "what_if"


@dataclass(frozen=True)
class StateSnapshot:
    snapshot_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_snapshot_id: str | None = None
    branch: str = BranchType.MAIN.value
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    state: dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.hash:
            object.__setattr__(self, "hash", self._compute_hash())

    def _compute_hash(self) -> str:
        canonical = json.dumps(self.state, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class StateDiff:
    from_snapshot_id: str
    to_snapshot_id: str
    added: dict[str, Any] = field(default_factory=dict)
    removed: dict[str, Any] = field(default_factory=dict)
    changed: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Branch:
    name: str
    branch_type: BranchType = BranchType.MAIN
    created_from_snapshot_id: str | None = None
    head_snapshot_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class MergeConflictError(Exception):
    pass


class WorldStateFabric:
    def __init__(self, supabase_client=None):
        self._snapshots: dict[str, StateSnapshot] = {}
        self._branches: dict[str, Branch] = {}
        self._timeline: list[str] = []
        self._lock = asyncio.Lock()
        self.supabase = supabase_client
        genesis = StateSnapshot(state={}, metadata={"event": "genesis"})
        self._snapshots[genesis.snapshot_id] = genesis
        self._branches["main"] = Branch(
            name="main",
            branch_type=BranchType.MAIN,
            head_snapshot_id=genesis.snapshot_id,
        )
        self._timeline.append(genesis.snapshot_id)

    async def create_snapshot(
        self,
        state: dict[str, Any],
        parent_snapshot_id: str | None = None,
        branch: str = "main",
        metadata: dict[str, Any] | None = None,
    ) -> StateSnapshot:
        async with self._lock:
            parent_id = parent_snapshot_id or self._branches[branch].head_snapshot_id
            snapshot = StateSnapshot(
                parent_snapshot_id=parent_id,
                branch=branch,
                state=copy.deepcopy(state),
                metadata=metadata or {},
            )
            self._snapshots[snapshot.snapshot_id] = snapshot
            self._branches[branch].head_snapshot_id = snapshot.snapshot_id
            self._timeline.append(snapshot.snapshot_id)
            return snapshot

    async def get_snapshot(self, snapshot_id: str) -> StateSnapshot | None:
        return self._snapshots.get(snapshot_id)

    async def get_latest_snapshot(self, branch: str = "main") -> StateSnapshot | None:
        b = self._branches.get(branch)
        if b and b.head_snapshot_id:
            return self._snapshots.get(b.head_snapshot_id)
        return None

    async def diff(self, from_snapshot_id: str, to_snapshot_id: str) -> StateDiff:
        f_snap = self._snapshots.get(from_snapshot_id)
        t_snap = self._snapshots.get(to_snapshot_id)
        if not f_snap or not t_snap:
            raise ValueError("Snapshot not found")
        added, removed, changed = {}, {}, {}
        all_keys = set(f_snap.state.keys()) | set(t_snap.state.keys())
        for key in all_keys:
            in_f = key in f_snap.state
            in_t = key in t_snap.state
            if not in_f and in_t:
                added[key] = t_snap.state[key]
            elif in_f and not in_t:
                removed[key] = f_snap.state[key]
            elif f_snap.state[key] != t_snap.state[key]:
                changed[key] = (f_snap.state[key], t_snap.state[key])
        return StateDiff(
            from_snapshot_id=from_snapshot_id,
            to_snapshot_id=to_snapshot_id,
            added=added,
            removed=removed,
            changed=changed,
        )

    async def apply_diff(self, base_snapshot_id: str, diff: StateDiff) -> StateSnapshot:
        base = await self.get_snapshot(base_snapshot_id)
        if not base:
            raise ValueError(f"Base snapshot {base_snapshot_id} not found")
        new_state = copy.deepcopy(base.state)
        for k, v in diff.added.items():
            new_state[k] = v
        for k in diff.removed:
            new_state.pop(k, None)
        for k, (_old, new) in diff.changed.items():
            new_state[k] = new
        return await self.create_snapshot(
            state=new_state,
            parent_snapshot_id=base_snapshot_id,
            metadata={"applied_diff": diff.to_snapshot_id},
        )

    async def create_branch(
        self,
        name: str,
        from_snapshot_id: str,
        branch_type: BranchType = BranchType.EXPERIMENT,
        metadata: dict[str, Any] | None = None,
    ) -> Branch:
        async with self._lock:
            if name in self._branches:
                raise ValueError(f"Branch '{name}' already exists")
            branch = Branch(
                name=name,
                branch_type=branch_type,
                created_from_snapshot_id=from_snapshot_id,
                head_snapshot_id=from_snapshot_id,
                metadata=metadata or {},
            )
            self._branches[name] = branch
            return branch

    async def merge_branches(
        self,
        source_branch: str,
        target_branch: str,
        strategy: str = "last_write_wins",
    ) -> StateSnapshot:
        source_head = await self.get_latest_snapshot(source_branch)
        target_head = await self.get_latest_snapshot(target_branch)
        if not source_head or not target_head:
            raise ValueError("Branch head not found")
        if strategy == "last_write_wins":
            merged = {**target_head.state, **source_head.state}
        elif strategy == "probabilistic":
            merged = await self._probabilistic_merge(source_head, target_head)
        elif strategy == "manual":
            conflicts = self._find_conflicts(source_head.state, target_head.state)
            if conflicts:
                raise MergeConflictError(f"Conflicts: {conflicts}")
            merged = {**target_head.state, **source_head.state}
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        return await self.create_snapshot(
            state=merged,
            parent_snapshot_id=target_head.snapshot_id,
            branch=target_branch,
            metadata={
                "merged_from_branch": source_branch,
                "merged_from_snapshot": source_head.snapshot_id,
                "strategy": strategy,
            },
        )

    async def _probabilistic_merge(self, source: StateSnapshot, target: StateSnapshot) -> dict[str, Any]:
        sw = source.metadata.get("confidence", 0.5)
        tw = target.metadata.get("confidence", 0.5)
        total = sw + tw
        merged: dict[str, Any] = {}
        for k in set(source.state.keys()) | set(target.state.keys()):
            if k in source.state and k in target.state:
                if isinstance(source.state[k], (int, float)) and isinstance(target.state[k], (int, float)):
                    merged[k] = (source.state[k] * sw + target.state[k] * tw) / total
                else:
                    merged[k] = source.state[k] if sw >= tw else target.state[k]
            elif k in source.state:
                merged[k] = source.state[k]
            else:
                merged[k] = target.state[k]
        return merged

    @staticmethod
    def _find_conflicts(s1: dict[str, Any], s2: dict[str, Any]) -> list[str]:
        return [k for k in set(s1) & set(s2) if s1[k] != s2[k]]

    def is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool:
        current = self._snapshots.get(descendant_id)
        while current:
            if current.snapshot_id == ancestor_id:
                return True
            current = self._snapshots.get(current.parent_snapshot_id) if current.parent_snapshot_id else None
        return False

    def common_ancestor(self, snapshot_a: str, snapshot_b: str) -> str | None:
        ancestors_a: set[str] = set()
        current = self._snapshots.get(snapshot_a)
        while current:
            ancestors_a.add(current.snapshot_id)
            current = self._snapshots.get(current.parent_snapshot_id) if current.parent_snapshot_id else None
        current = self._snapshots.get(snapshot_b)
        while current:
            if current.snapshot_id in ancestors_a:
                return current.snapshot_id
            current = self._snapshots.get(current.parent_snapshot_id) if current.parent_snapshot_id else None
        return None

    async def replay_from(self, snapshot_id: str, target_branch: str = "replay") -> Branch:
        snapshot = await self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        return await self.create_branch(
            name=f"{target_branch}_{uuid.uuid4().hex[:8]}",
            from_snapshot_id=snapshot_id,
            branch_type=BranchType.EXPERIMENT,
            metadata={
                "replay_of": snapshot_id,
                "original_timestamp": str(snapshot.timestamp),
            },
        )

    async def get_timeline(self, branch: str = "main", limit: int = 100) -> list[StateSnapshot]:
        b = self._branches.get(branch)
        if not b:
            return []
        snapshots: list[StateSnapshot] = []
        current_id = b.head_snapshot_id
        while current_id and len(snapshots) < limit:
            snap = self._snapshots.get(current_id)
            if snap:
                snapshots.append(snap)
                current_id = snap.parent_snapshot_id
            else:
                break
        return snapshots

    async def load_from_supabase(self) -> None:
        if not self.supabase:
            return
        response = await self.supabase.table("world_state_snapshots").select("*").order("timestamp").execute()
        for row in response.data:
            snapshot = StateSnapshot(
                snapshot_id=row["snapshot_id"],
                parent_snapshot_id=row.get("parent_snapshot_id"),
                branch=row.get("branch", "main"),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                state=json.loads(row["state"]),
                hash=row["hash"],
                metadata=json.loads(row["metadata"]),
            )
            self._snapshots[snapshot.snapshot_id] = snapshot
