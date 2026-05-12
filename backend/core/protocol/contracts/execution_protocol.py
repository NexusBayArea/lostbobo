from __future__ import annotations

import traceback

from backend.core.execution.models import ExecutionPriority, ExecutionRequest
from backend.core.protocol.bus.protocol_envelope import ProtocolEnvelope
from backend.core.protocol.bus.protocol_response import ProtocolResponse
from backend.core.protocol.contracts.base_protocol import BaseProtocol


class ExecutionProtocol(BaseProtocol):
    protocol_name = "execution"

    async def handle(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        action = envelope.action
        payload = envelope.payload

        if action == "submit":
            return await self._handle_submit(envelope, payload)
        elif action == "cancel":
            return await self._handle_cancel(envelope, payload)
        elif action == "status":
            return await self._handle_status(envelope, payload)
        else:
            return ProtocolResponse(
                success=False,
                error=f"Unknown execution action: {action}",
            )

    async def _handle_submit(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            request = ExecutionRequest(
                tenant_id=envelope.tenant_id,
                plugin_name=envelope.source,
                dag_id=payload.get("dag_id"),
                capability=payload.get("capability", ""),
                inputs=payload.get("inputs", {}),
                priority=ExecutionPriority(payload.get("priority", "simulation")),
                timeout_seconds=payload.get("timeout_seconds", 3600),
                checkpoint_enabled=payload.get("checkpoint_enabled", True),
            )

            executor = getattr(self, "_kernel_services", {}).get("simulation_executor")
            if executor is None:
                return ProtocolResponse(
                    success=False,
                    error="SimulationExecutor not available",
                )

            future = await executor.submit(request)
            return ProtocolResponse(
                success=True,
                payload=future.model_dump(),
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Execution submit failed: {e}",
                payload={"traceback": traceback.format_exc()},
            )

    async def _handle_cancel(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            execution_id = payload.get("execution_id")
            if not execution_id:
                return ProtocolResponse(
                    success=False,
                    error="execution_id required",
                )

            executor = getattr(self, "_kernel_services", {}).get("simulation_executor")
            if executor is None:
                return ProtocolResponse(
                    success=False,
                    error="SimulationExecutor not available",
                )

            cancelled = await executor.cancel(execution_id)
            return ProtocolResponse(
                success=cancelled,
                payload={"execution_id": execution_id, "cancelled": cancelled},
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Execution cancel failed: {e}",
            )

    async def _handle_status(self, envelope: ProtocolEnvelope, payload: dict) -> ProtocolResponse:
        try:
            execution_id = payload.get("execution_id")
            if not execution_id:
                return ProtocolResponse(
                    success=False,
                    error="execution_id required",
                )

            executor = getattr(self, "_kernel_services", {}).get("simulation_executor")
            if executor is None:
                return ProtocolResponse(
                    success=False,
                    error="SimulationExecutor not available",
                )

            status = await executor.get_status(execution_id)
            return ProtocolResponse(
                success=True,
                payload={
                    "execution_id": execution_id,
                    "status": status.value if status else "unknown",
                },
            )
        except Exception as e:
            return ProtocolResponse(
                success=False,
                error=f"Execution status failed: {e}",
            )
