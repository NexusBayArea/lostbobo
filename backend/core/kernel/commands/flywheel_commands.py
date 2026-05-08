from dataclasses import dataclass

from pydantic import BaseModel

# ─────────────────────────────────────────────
# Command Models
# ─────────────────────────────────────────────


@dataclass
class IngestRunCommand:
    """Ingest a completed simulation run into the Flywheel."""

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
    """Retrieve priors for a simulation (used in pre-run hook)."""

    domain: str
    solver: str
    tenant_id: str | None = None
    min_confidence: float = 0.1


@dataclass
class SuggestSwarmCommand:
    """Get full swarm suggestion (used by intelligence layer)."""

    domain: str
    solver: str
    tenant_id: str | None = None
    target_confidence: float = 0.85


@dataclass
class GetFlywheelSnapshotCommand:
    """Get current flywheel health metrics."""

    pass


@dataclass
class GetLeaderboardCommand:
    """Get global discovery leaderboard."""

    domain: str | None = None
    limit: int = 50


# ─────────────────────────────────────────────
# Response Models (for type safety in handlers)
# ─────────────────────────────────────────────


class PriorSuggestion(BaseModel):
    parameter_key: str
    suggested_value: float
    suggested_range: list[float]
    confidence: float
    evidence_count: int
    convergence_rate: float
    mean_trust_score: float
    source: str


class SwarmSuggestionResponse(BaseModel):
    domain: str
    solver: str
    suggested_parameters: list[PriorSuggestion]
    suggested_perturbation_method: str
    suggested_num_runs: int
    suggested_random_seed: int
    prior_confidence: float
    evidence_count: int
    source_leaderboard_rank: int | None
    rationale: str


class FlywheelSnapshotResponse(BaseModel):
    total_runs_ingested: int
    total_domains: int
    total_parameter_priors: int
    mean_prior_confidence: float
    certified_run_fraction: float
    top_domain: str
    top_domain_run_count: int
    leaderboard_size: int
    flywheel_velocity: float
    moat_score: float
    status: str
