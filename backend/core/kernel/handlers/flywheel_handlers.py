"""
Flywheel Command Handlers — Kernel Integration
"""

import logging
from typing import Any

from backend.core.kernel.commands.flywheel_commands import (
    GetFlywheelSnapshotCommand,
    GetLeaderboardCommand,
    GetPriorsCommand,
    IngestRunCommand,
    SuggestSwarmCommand,
)
from backend.core.supabase import get_supabase_client
from backend.runtime.flywheel.engine import FlywheelEngine

logger = logging.getLogger(__name__)


async def handle_ingest_run(kernel: Any, cmd: IngestRunCommand) -> dict[str, Any]:
    """Handler for IngestRunCommand"""
    flywheel: FlywheelEngine = kernel.services["flywheel"]
    await flywheel.update(domain=cmd.domain, solver=cmd.solver, values=cmd.parameters)
    return {"status": "ingested", "run_id": cmd.run_id}


async def handle_get_priors(kernel: Any, cmd: GetPriorsCommand) -> list[dict[str, Any]]:
    """Handler for GetPriorsCommand"""
    flywheel: FlywheelEngine = kernel.services["flywheel"]
    return [flywheel.get_prior(cmd.domain, cmd.solver)]


async def handle_suggest_swarm(kernel: Any, cmd: SuggestSwarmCommand) -> dict[str, Any]:
    """Handler for SuggestSwarmCommand"""
    return {"status": "suggested"}


async def handle_get_snapshot(kernel: Any, cmd: GetFlywheelSnapshotCommand) -> dict[str, Any]:
    """Handler for snapshot"""
    return {"status": "snapshot"}


async def handle_get_leaderboard(kernel: Any, cmd: GetLeaderboardCommand) -> dict[str, Any]:
    """Handler for leaderboard"""
    db = get_supabase_client()
    if not db:
        return {"leaderboard": [], "total": 0}

    query = db.table("discovery_leaderboard").select("*").order("score", desc=True).limit(cmd.limit)
    if cmd.domain:
        query = query.eq("domain", cmd.domain)

    result = query.execute()
    return {
        "leaderboard": result.data or [],
        "total": len(result.data or []),
    }


FLYWHEEL_HANDLERS = {
    IngestRunCommand: handle_ingest_run,
    GetPriorsCommand: handle_get_priors,
    SuggestSwarmCommand: handle_suggest_swarm,
    GetFlywheelSnapshotCommand: handle_get_snapshot,
    GetLeaderboardCommand: handle_get_leaderboard,
}
