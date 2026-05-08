from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunSimulationCommand:
    """
    Main command for executing a full simulation run.
    Fully kernel-centered — all services (Physics, World Model, Trust, Flywheel)
    are orchestrated through this single entry point.
    """

    run_id: str
    tenant_id: str
    config: dict[str, Any]
    user_id: str | None = None
    priority: str = "normal"
    expected_duration_seconds: int = 300
    metadata: dict[str, Any] | None = field(default_factory=dict)


@dataclass
class CancelSimulationCommand:
    """Cancel a running simulation."""

    run_id: str
    tenant_id: str
    reason: str = "user_cancelled"


@dataclass
class GetSimulationStatusCommand:
    """Query status of a running or completed simulation."""

    run_id: str
    tenant_id: str
