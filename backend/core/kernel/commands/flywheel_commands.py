from dataclasses import dataclass


@dataclass
class IngestRunCommand:
    run_id: str
    tenant_id: str
    domain: str
    solver: str
    parameters: dict[str, float]
    convergence_achieved: bool
    convergence_iterations: int
    brier_score: float | None = None
    trust_score: float = 0.5
    certified: bool = False
    opt_in_global_pool: bool = True


@dataclass
class GetPriorsCommand:
    domain: str
    solver: str
    tenant_id: str | None = None
    min_confidence: float = 0.1


@dataclass
class SuggestSwarmCommand:
    domain: str
    solver: str
    tenant_id: str | None = None
    target_confidence: float = 0.85


@dataclass
class GetFlywheelSnapshotCommand:
    pass


@dataclass
class GetLeaderboardCommand:
    domain: str | None = None
    limit: int = 50
