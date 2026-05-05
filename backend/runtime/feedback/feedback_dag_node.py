"""Feedback loop DAG node."""

from __future__ import annotations

from backend.runtime.feedback.brier_engine import BrierEngine


class FeedbackDagNode:
    """DAG node for feedback loop processing."""

    def __init__(self):
        self.engine = BrierEngine()

    async def execute(self, context: dict) -> dict:
        """Execute feedback processing."""
        event = context.get("event")
        if not event:
            return {"status": "skipped", "reason": "no event"}

        result = await self.engine.process(event)
        return {
            "status": "success",
            "question_id": result.question_id,
            "ensemble_brier": result.ensemble_brier,
            "weights_updated": result.weights_updated,
        }