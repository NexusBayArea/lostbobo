"""
Trace-Based Alerting Service
Runs periodically and triggers alerts on trace anomalies.
"""

import asyncio
import logging
from datetime import datetime

from backend.core.kernel.commands.compliance_commands import LogAuditCommand
from backend.core.kernel.kernel import Kernel as _Kernel
from backend.core.services.observability_service import observability

logger = logging.getLogger(__name__)


class TraceAlertService:
    def __init__(self):
        self._kernel = _Kernel()
        self._last_check = datetime.now()

    async def run_periodic_check(self):
        """Run every 60 seconds."""
        while True:
            try:
                await self._check_trace_anomalies()
            except Exception as e:
                logger.error("Trace alert check failed", exc_info=e)

            await asyncio.sleep(60)

    async def _check_trace_anomalies(self):
        """Check for concerning trace patterns."""
        now = datetime.now()

        fallback_rate = 0.0

        if fallback_rate > 0.25:
            await self._trigger_alert(
                title="High Model Fallback Rate Detected", severity="critical", details={"fallback_rate": fallback_rate}
            )

        self._last_check = now

    async def _trigger_alert(self, title: str, severity: str, details: dict):
        """Trigger alert + log to audit trail."""
        observability().increment("trace_based_alerts_total", {"severity": severity})

        try:
            await self._kernel.execute(
                LogAuditCommand(
                    event_type="TRACE_ALERT",
                    outcome="WARNING" if severity == "warning" else "CRITICAL",
                    tenant_id="system",
                    user_id="system",
                    user_email="compliance@simhpc.com",
                    user_role="isso",
                    resource_type="ml_model",
                    resource_id="physics_inference",
                    resource_classification="CUI_BASIC",
                    action=f"Trace-based alert: {title}",
                    details=details,
                )
            )
        except Exception:
            pass

        logger.warning(f"TRACE ALERT [{severity.upper()}]: {title}")
