from pydantic import BaseModel


class TemporalBranch(BaseModel):
    branch_id: str
    parent_branch_id: str | None = None
    created_at: float = 0.0
    created_by: str
    replayable: bool = True
