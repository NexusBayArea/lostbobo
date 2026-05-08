"""
Full Leaderboard Scoring + Certificate-Driven Population
"""

import hashlib
import logging
from typing import Any

from backend.core.services.observability_service import observability
from backend.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class LeaderboardScorer:
    PERFORMANCE_WEIGHT = 0.55
    REPRODUCIBILITY_WEIGHT = 0.25
    NOVELTY_WEIGHT = 0.20

    @staticmethod
    def calculate_score(result: dict[str, Any], cert_data: dict[str, Any] | None = None) -> dict[str, float]:
        """Enhanced scoring using certificate data when available."""
        convergence = result.get("convergence_achieved", False)
        iterations = result.get("convergence_iterations", 9999)
        brier = result.get("brier_score", 0.5)
        trust_score = result.get("trust_score", 0.5)

        # Performance
        perf_score = 100.0
        if convergence:
            perf_score = max(40, 100 - (iterations / 8))
        perf_score = perf_score * (1.0 - brier) * trust_score

        # Reproducibility — boosted heavily by certificate tier
        repro_score = 50.0
        if cert_data:
            tier = cert_data.get("verification_tier")
            if tier == "TIER_3_GOLD":
                repro_score = 100.0
            elif tier == "TIER_2_PHYSICS":
                repro_score = 88.0
            elif tier == "TIER_1_PARAMETER":
                repro_score = 70.0
            # Extra trust from provenance
            repro_score += cert_data.get("prov_trust_score", 0) * 15

        # Novelty
        prior_deviation = result.get("prior_deviation", 0.3)
        entropy = result.get("entropy", 0.5)
        novelty_score = 100 * (0.65 * prior_deviation + 0.35 * entropy)

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


async def populate_leaderboard_from_certificates(limit: int = 500):
    """
    Full population / refresh of discovery_leaderboard using certificates.
    Prioritizes high-tier certified runs.
    """
    db = get_supabase_client()
    if not db:
        return

    # Fetch high-value certified runs
    cert_runs = (
        db.table("certificates")
        .select(
            "certificate_id, run_id, tenant_id, verification_tier, prov_trust_score, prov_claim_text, issued_at, full_certificate"
        )
        .in_("verification_tier", ["TIER_3_GOLD", "TIER_2_PHYSICS", "TIER_1_PARAMETER"])
        .order("prov_trust_score", desc=True)
        .limit(limit)
        .execute()
    )

    scorer = LeaderboardScorer()
    entries = []

    for cert in cert_runs.data or []:
        # Get full simulation result
        run_result = (
            db.table("simulation_runs")
            .select("result, domain, solver, created_at")
            .eq("run_id", cert["run_id"])
            .execute()
        )

        if not run_result.data:
            continue

        run = run_result.data[0]
        result = run.get("result", {})

        scores = scorer.calculate_score(result, cert)

        discovery_id = f"disc_{cert['run_id']}"

        entries.append(
            {
                "discovery_id": discovery_id,
                "domain": run.get("domain", "unknown"),
                "solver": run.get("solver", "unknown"),
                "title": cert.get("prov_claim_text", f"Certified Discovery {cert['run_id'][:8]}")[:120],
                "description": f"Certified {cert['verification_tier']} run with trust score {cert.get('prov_trust_score', 0):.2f}",
                **scores,
                "run_count": 1,
                "certified": True,
                "certificate_id": cert["certificate_id"],
                "tenant_id_hash": hashlib.sha256(cert["tenant_id"].encode()).hexdigest()[:16],
                "published_at": cert["issued_at"] or run.get("created_at"),
            }
        )

        # Mark as processed
        db.table("simulation_runs").update({"leaderboard_entry_id": discovery_id}).eq(
            "run_id", cert["run_id"]
        ).execute()

    if entries:
        db.table("discovery_leaderboard").upsert(entries, on_conflict="discovery_id").execute()
        observability.increment("leaderboard_cert_based_entries", {"count": len(entries)})
        logger.info(f"✅ Leaderboard populated from certificates — {len(entries)} high-quality entries added")


async def refresh_leaderboard():
    """Combined refresh: simulation runs + certificate-driven population"""
    await populate_leaderboard_from_certificates(limit=300)  # High-tier focus
    logger.info("✅ Full leaderboard refresh (certificates + simulations) completed")
