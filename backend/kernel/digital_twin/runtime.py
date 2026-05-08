from typing import Any

import structlog

from backend.kernel.kernel import Kernel

log = structlog.get_logger(__name__)


class DigitalTwinRuntime:
    """Persistent live digital twin with synchronization and forecasting."""

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.state: dict[str, Any] = {}

    async def ingest_telemetry(self, telemetry: dict[str, Any]):
        self.state.update(telemetry)
        await self.kernel.services["telemetry"].publish(
            {"simulation_id": telemetry.get("simulation_id"), "metric": "twin_update", "value": len(telemetry)}
        )

    async def forecast(self, horizon: float = 3600) -> dict[str, Any]:
        result = await self.kernel.command_bus.execute(
            "SIMULATION_RUN", {"initial_state": self.state, "duration": horizon}
        )
        return result

    async def synchronize(self, real_data: dict[str, Any]):
        corrected = await self.kernel.services["kalman"].update(self.state, real_data)
        self.state = corrected
        await self.kernel.supabase_job_store.record_event("twin_synchronized", {"state_size": len(self.state)})
