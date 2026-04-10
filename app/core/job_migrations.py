import logging
from typing import Dict, Any
from app.models.version import CURRENT_JOB_SCHEMA_VERSION

logger = logging.getLogger(__name__)


def migrate_job(data: Dict[str, Any]) -> Dict[str, Any]:
    version = data.get("schema_version", 0)

    if version < 1:
        data = migrate_v0_to_v1(data)
        version = 1

    data["schema_version"] = version

    if version != CURRENT_JOB_SCHEMA_VERSION:
        raise RuntimeError(f"Unsupported schema version after migration: {version}")

    return data


def migrate_v0_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    if "progress" not in data:
        data["progress"] = {"percent": 0}

    if "retries" not in data:
        data["retries"] = 0

    if "schema_version" not in data:
        data["schema_version"] = 1

    logger.info(f"Migrated job {data.get('id', 'unknown')} from v0 to v1")
    return data
