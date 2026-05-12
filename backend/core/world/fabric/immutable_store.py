from abc import ABC, abstractmethod

from backend.core.world.fabric.world_snapshot import WorldSnapshot


class AbstractWorldStore(ABC):
    @abstractmethod
    def write_snapshot(self, snapshot: WorldSnapshot) -> None: ...

    @abstractmethod
    def get_snapshot(self, snapshot_id: str) -> WorldSnapshot | None: ...

    @abstractmethod
    def list_snapshots(self, tenant_id: str, branch_id: str) -> list[str]: ...


class InMemoryWorldStore(AbstractWorldStore):
    def __init__(self):
        self.snapshots: dict[str, WorldSnapshot] = {}

    def write_snapshot(self, snapshot: WorldSnapshot):
        self.snapshots[snapshot.snapshot_id] = snapshot

    def get_snapshot(self, snapshot_id: str) -> WorldSnapshot | None:
        return self.snapshots.get(snapshot_id)

    def list_snapshots(self, tenant_id: str, branch_id: str) -> list[str]:
        return [
            sid for sid, snap in self.snapshots.items() if snap.tenant_id == tenant_id and snap.branch_id == branch_id
        ]
