from dataclasses import dataclass
from typing import Any


@dataclass
class LogAuditCommand:
    event_type: str
    outcome: str
    tenant_id: str
    user_id: str
    user_email: str
    user_role: str
    resource_type: str
    resource_id: str
    resource_classification: str
    action: str
    details: dict[str, Any] | None = None


@dataclass
class VerifyAuditChainCommand:
    tenant_id: str
    start_date: str | None = None
    end_date: str | None = None
