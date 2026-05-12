from pydantic import BaseModel


class ReplayCheckpoint(BaseModel):
    checkpoint_id: str
    snapshot_id: str
    replay_hash: str
    scheduler_hash: str
    dag_hash: str
    created_at: float
