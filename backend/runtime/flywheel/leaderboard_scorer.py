"""
Full Leaderboard Scoring Engine
Weights: Performance 55% | Reproducibility 25% | Novelty 20%
"""

import logging
from typing import Any

from backend.core.services.observability_service import observability
from backend.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class LeaderboardScorer:
    """Calculates discovery scores from simulation results + certificates."""

    PERFORMANCE_WEIGHT = 0.55
    REPRODUCIBILITY_WEIGHT = 0.25
    NOVELTY_WEIGHT = 0.20

    @staticmethod
    def calculate_score(result: dict[str, Any], certificate_tier: str | None = None) -> dict[str, float]:
        """Compute all sub-scores and final weighted score."""

        # 1. Performance Score (0–100)
        convergence = result.get("convergence_achieved", False)
        iterations = result.get("convergence_iterations", 9999)
        brier = result.get("brier_score", 0.5)

        perf_score = 100.0
        if convergence:
            perf_score = max(30, 100 - (iterations / 10))  # faster = better
        perf_score *= 1.0 - brier  # lower brier = better

        # 2. Reproducibility Score (0–100)
        repro_score = 40.0
        if certificate_tier == "TIER_3_GOLD":
            repro_score = 100.0
        elif certificate_tier == "TIER_2_PHYSICS":
            repro_score = 85.0
        elif certificate_tier == "TIER_1_PARAMETER":
            repro_score = 65.0

        # Bonus for multiple certified runs on same discovery
        run_count = result.get("run_count", 1)
        repro_score = min(100.0, repro_score + (run_count - 1) * 5)

        # 3. Novelty Score (0–100)
        # Higher if result deviates from current priors (entropy)
        prior_deviation = result.get("prior_deviation", 0.0)  # 0–1 normalized
        entropy = result.get("entropy", 0.5)
        novelty_score = 100 * (0.6 * prior_deviation + 0.4 * entropy)

        # 4. Final Weighted Score
        final_score = (
            LeaderboardScorer.PERFORMANCE_WEIGHT * perf_score
            + LeaderboardScorer.REPRODUCIBILITY_WEIGHT * repro_score
            + LeaderboardScorer.NOVELTY_WEIGHT * novelty_score
        )

        return {
            "performance_score": round(perf_score, 2),
            "reproducibility": round(repro_score, 2),
            "novelty_score": round(novelty_score, 2),
            "score": round(final_score, 2),
        }


async def refresh_leaderboard():
    """Full refresh: score all recent discoveries and update leaderboard table."""
    db = get_supabase_client()
    if not db:
        return

    # Fetch recent completed runs that are not yet on leaderboard
    runs = (
        db.table("simulation_runs")
        .select("run_id, tenant_id, domain, solver, result, created_at, certificate_id")
        .eq("status", "COMPLETED")
        .is_("leaderboard_entry_id", None)
        .limit(200)
        .execute()
    )

    scorer = LeaderboardScorer()
    updates = []

    for run in runs.data or []:
        result = run.get("result", {})
        cert_tier = None
        if run.get("certificate_id"):
            cert = (
                db.table("certificates")
                .select("verification_tier")
                .eq("certificate_id", run["certificate_id"])
                .execute()
            )
            cert_tier = cert.data[0]["verification_tier"] if cert.data else None

        scores = scorer.calculate_score(result, cert_tier)
        discovery_id = f"disc_{run['run_id']}"

        updates.append(
            {
                "discovery_id": discovery_id,
                "domain": run["domain"],
                "solver": run["solver"],
                "title": f"Discovery from {run['domain']} run {run['run_id'][:8]}",
                "description": f"Auto-generated from simulation run {run['run_id']}",
                **scores,
                "run_count": 1,
                "certified": bool(run.get("certificate_id")),
                "certificate_id": run.get("certificate_id"),
                "tenant_id_hash": "SHA256_PLACEHOLDER",  # hashed in ingest
                "published_at": run["created_at"],
            }
        )

        # Mark run as processed
        db.table("simulation_runs").update({"leaderboard_entry_id": discovery_id}).eq("run_id", run["run_id"]).execute()

    if updates:
        db.table("discovery_leaderboard").upsert(updates, on_conflict="discovery_id").execute()
        observability.increment("leaderboard_entries_updated", {"count": len(updates)})
        logger.info(f"✅ Leaderboard refreshed — {len(updates)} new entries")
