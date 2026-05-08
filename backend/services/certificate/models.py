from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Certificate:
    certificate_id: str
    run_id: str
    tenant_id: str
    certificate_hash: str
    signature: str
    public_key_fingerprint: str
    full_certificate: dict[str, Any]
    issued_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__
