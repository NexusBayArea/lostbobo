import asyncio
import logging

from backend.core.kernel.commands.flywheel_commands import GetFlywheelSnapshotCommand
from backend.core.kernel.kernel import get_kernel
from backend.runtime.flywheel.engine import get_flywheel

logger = logging.getLogger(__name__)


class FlywheelScheduler:
    def __init__(self):
        self._kernel = get_kernel()
        self._task: asyncio.Task | None = None
        self._is_running = False

    async def start(self):
        """Start background scheduler."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("🚀 Flywheel background scheduler started")

    async def stop(self):
        """Graceful shutdown."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("🛑 Flywheel scheduler stopped")

    async def _scheduler_loop(self):
        """Main loop: runs every 5 minutes."""
        while True:
            try:
                await self._run_decay_and_refresh()
            except Exception as e:
                logger.error("Flywheel scheduler error", exc_info=e)
                # observability.increment("flywheel_scheduler_errors_total")

            await asyncio.sleep(300)  # 5 minutes

    async def _run_decay_and_refresh(self):
        """Apply decay + refresh leaderboard + log snapshot."""
        flywheel = get_flywheel()

        # Apply global decay
        flywheel._apply_global_decay()
        await flywheel._persist_priors("global", "all")  # persist decay changes

        # Log snapshot
        snapshot_cmd = GetFlywheelSnapshotCommand()
        snapshot = await self._kernel.execute(snapshot_cmd)

        logger.info(
            f"[Flywheel Scheduler] Decay applied | "
            f"Total runs: {snapshot['total_runs_ingested']} | "
            f"Mean confidence: {snapshot['mean_prior_confidence']:.1%} | "
            f"Moat: {snapshot.get('moat_score', 0):.1%}"
        )

        # observability.gauge("flywheel_mean_confidence", snapshot["mean_prior_confidence"])


# Singleton
_scheduler: FlywheelScheduler | None = None


def get_flywheel_scheduler() -> FlywheelScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = FlywheelScheduler()
    return _scheduler
