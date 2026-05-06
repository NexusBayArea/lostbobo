"""Example Skills — Simulation + Policy examples."""

from backend.core.models.hypothesis import Hypothesis
from backend.core.simulation.runner import SimulationRunner
from backend.core.skills.registry import Skill, SkillRegistry

registry = SkillRegistry()


async def run_pricing_elasticity(inputs: dict):
    runner = SimulationRunner()
    hyp = Hypothesis()
    hyp.sim_params = inputs
    result = await runner.run(hyp)
    return result


registry.register(
    Skill(
        name="pricing_elasticity",
        kind="simulation",
        description="Bayesian model of price elasticity and revenue impact",
        inputs={"base_price": float, "elasticity_range": list},
        outputs={"revenue_uplift": dict, "confidence_interval": list},
        execute=run_pricing_elasticity,
        success_metrics=["revenue_uplift", "confidence_interval_width"],
    )
)


async def budget_allocation_policy(inputs: dict):
    hyp = Hypothesis()
    hyp.claim = {"budget": inputs.get("total_budget"), "candidates": inputs.get("candidates")}
    return hyp


registry.register(
    Skill(
        name="budget_allocation",
        kind="policy",
        description="Optimize budget allocation under ROI constraints",
        inputs={"total_budget": float, "candidates": list},
        outputs={"recommended_allocation": dict, "expected_roi": float},
        execute=budget_allocation_policy,
    )
)
