from typing import Any

from backend.core.kernel.commands.compliance_commands import LogAuditCommand
from backend.services.compliance.audit_log import get_audit_log
from backend.services.compliance.models import AuditEventType, AuditOutcome


async def handle_log_audit(kernel: Any, cmd: LogAuditCommand) -> dict[str, Any]:
    audit = get_audit_log()
    await audit.log(
        event_type=AuditEventType(cmd.event_type),
        outcome=AuditOutcome(cmd.outcome),
        tenant_id=cmd.tenant_id,
        user_id=cmd.user_id,
        user_email=cmd.user_email,
        user_role=cmd.user_role,
        resource_type=cmd.resource_type,
        resource_id=cmd.resource_id,
        resource_classification=cmd.resource_classification,
        action=cmd.action,
        details=cmd.details or {},
        source_ip="0.0.0.0",
        user_agent="simhpc-kernel",
        session_id="system",
        request_id="system",
    )
    return {"status": "logged"}
