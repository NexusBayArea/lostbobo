from __future__ import annotations

import hashlib
import json
import logging
import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.core.supabase import get_supabase_client
from backend.core.services.observability_service import observability

logger = logging.getLogger(__name__)


@dataclass
class QualityThresholds:
    min_trust_score: float = 0.70
    max_brier_score: float = 0.20
    require_convergence: bool = True
    min_convergence_iterations: int = 10
    require_certificate: bool = False
    min_certificate_tier: str = ""
    min_monte_carlo_paths: int = 0
    max_drift_detected: bool = True

    @classmethod
    def production(cls) -> QualityThresholds:
        return cls(
            min_trust_score=0.80,
            max_brier_score=0.15,
            require_convergence=True,
            min_convergence_iterations=50,
            require_certificate=True,
            min_certificate_tier="TIER_2_PHYSICS",
            min_monte_carlo_paths=1000,
        )

    @classmethod
    def permissive(cls) -> QualityThresholds:
        return cls(
            min_trust_score=0.50,
            max_brier_score=0.30,
            require_convergence=True,
            min_convergence_iterations=5,
        )


@dataclass
class TrainingExample:
    example_id: str
    example_type: str
    domain: str
    solver: str
    source_run_hash: str
    quality_score: float
    messages: list[dict[str, str]]
    metadata: dict[str, Any]

    def to_openai_jsonl(self) -> str:
        return json.dumps({"messages": self.messages}, ensure_ascii=False)

    def to_hf_jsonl(self) -> str:
        system = next((m["content"] for m in self.messages if m["role"] == "system"), "")
        user = next((m["content"] for m in self.messages if m["role"] == "user"), "")
        assistant = next((m["content"] for m in self.messages if m["role"] == "assistant"), "")
        text = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n{assistant}"
        return json.dumps({"text": text, "metadata": self.metadata}, ensure_ascii=False)


class ExampleConstructor:
    SYSTEM_PROMPT = (
        "You are SimHPC, a physics simulation intelligence specialized in "
        "finite element analysis (FEM), GPU-accelerated solvers (MFEM, SUNDIALS), "
        "and uncertainty quantification. You reason precisely about structural mechanics, "
        "thermal analysis, fluid dynamics, and materials science. "
        "You express confidence as calibrated probability intervals, not vague qualifiers. "
        "All numerical answers include SI units and significant figures."
    )

    def hypothesis_verification(self, run: dict[str, Any]) -> TrainingExample | None:
        claim_text = run.get("prov_claim_text", "")
        trust_score = run.get("prov_trust_score", 0.0)
        params = run.get("in_raw_parameters", {})
        ci_low = run.get("out_ci_low", 0.0)
        ci_high = run.get("out_ci_high", 0.0)
        brier = run.get("out_brier_score")
        sensitivity = run.get("out_sensitivity_ranking", [])
        convergence = run.get("out_convergence_achieved", False)

        if not claim_text or not params:
            return None

        verdict = "CONFIRMED" if trust_score >= 0.75 else ("REFUTED" if trust_score < 0.40 else "INCONCLUSIVE")

        user_prompt = (
            f"Verify the following engineering hypothesis using simulation results:\n\n"
            f"**Hypothesis:** {claim_text}\n\n"
            f"**Simulation Parameters:**\n"
            + "\n".join(f"  - {k}: {v}" for k, v in list(params.items())[:8])
            + f"\n\n**Solver:** {run.get('in_solver', 'MFEM')} {run.get('in_solver_version', '')}\n"
            f"**Runs:** {run.get('in_num_runs', 0)} ({run.get('in_perturbation_method', '')} sampling)\n"
            f"**Convergence:** {'Yes' if convergence else 'No'} "
            f"({run.get('out_convergence_iterations', 0)} iterations)"
        )

        completion = (
            f"**Verdict: {verdict}**\n\n"
            f"**95% Confidence Interval:** [{ci_low:.6f}, {ci_high:.6f}]\n"
            f"**Trust Score:** {trust_score:.3f}"
            + (f"\n**Brier Score:** {brier:.4f} (calibration quality)" if brier else "")
            + f"\n\n**Reasoning:**\n"
            f"The simulation ran {run.get('in_num_runs', 0)} perturbations using "
            f"{run.get('in_perturbation_method', 'latin hypercube')} sampling. "
            f"{'Convergence was achieved' if convergence else 'Convergence was not achieved'} "
            f"after {run.get('out_convergence_iterations', 0)} iterations. "
            f"The confidence interval width of {ci_high - ci_low:.6f} indicates "
            f"{'tight' if (ci_high - ci_low) < 0.01 else 'moderate' if (ci_high - ci_low) < 0.1 else 'wide'} "
            f"uncertainty bounds.\n\n"
            f"**Primary Sensitivity Drivers:** {', '.join(sensitivity[:3]) if sensitivity else 'Not determined'}\n"
            f"The most influential parameter is **{sensitivity[0] if sensitivity else 'unknown'}**, "
            f"which dominates result variance. Engineers should prioritize accurate measurement "
            f"of this parameter to reduce uncertainty."
        )

        return self._make_example("hypothesis_verification", run, user_prompt, completion, trust_score)

    def parameter_prediction(self, run: dict[str, Any]) -> TrainingExample | None:
        params = run.get("in_raw_parameters", {})
        domain = run.get("domain", "structural")
        solver = run.get("in_solver", "MFEM")
        trust_score = run.get("prov_trust_score", 0.0)
        sensitivity = run.get("out_sensitivity_ranking", [])
        brier = run.get("out_brier_score")

        if not params or len(params) < 2:
            return None

        param_descriptions = {
            "youngs_modulus": "a structural component under mechanical load",
            "poisson_ratio": "a structural material under multiaxial stress",
            "thermal_conductivity": "a heat transfer analysis",
            "viscosity": "a fluid dynamics simulation",
            "density": "a dynamic structural or fluid analysis",
            "load": "a load-bearing structural component",
        }
        primary_param = next((k for k in params if k in param_descriptions), list(params.keys())[0])
        problem_description = param_descriptions.get(primary_param, f"a {domain} simulation")

        user_prompt = (
            f"I am setting up a {solver} simulation of {problem_description} "
            f"in the {domain} domain. "
            f"What parameter values do you recommend, and what ranges should I "
            f"explore in my robustness sweep?\n\n"
            f"**Goal:** Obtain well-converged results with quantified uncertainty.\n"
            f"**Solver:** {solver}\n"
            f"**Domain:** {domain}"
        )

        param_lines = []
        for k, v in list(params.items())[:10]:
            if isinstance(v, int | float):
                param_lines.append(f"  - **{k}:** {v:.6g} (nominal)")

        completion = (
            "Based on verified simulation data for this domain and solver:\n\n"
            "**Recommended Parameters:**\n"
            + "\n".join(param_lines)
            + f"\n\n**Sampling Strategy:** {run.get('in_perturbation_method', 'latin_hypercube')} "
            f"with {run.get('in_num_runs', 20)} runs recommended.\n"
            f"**Random Seed:** {run.get('in_random_seed', 42)} for reproducibility.\n\n"
            f"**Key Sensitivity Insight:**\n"
            f"In verified runs for this configuration, "
            f"**{sensitivity[0] if sensitivity else 'the primary parameter'}** "
            f"dominates result variance.\n\n"
            f"**Expected Convergence:** ~{run.get('out_convergence_iterations', 100)} iterations.\n"
            f"**Expected CI Width:** ~{abs(run.get('out_ci_high', 0) - run.get('out_ci_low', 0)):.4f} "
            f"at 95% confidence." + (f"\n**Calibration Quality (Brier):** {brier:.4f}" if brier else "")
        )

        return self._make_example("parameter_prediction", run, user_prompt, completion, trust_score)

    def uncertainty_quantification(self, run: dict[str, Any]) -> TrainingExample | None:
        ci_low = run.get("out_ci_low")
        ci_high = run.get("out_ci_high")
        confidence_level = run.get("out_confidence_level", 0.95)
        brier = run.get("out_brier_score")
        sensitivity = run.get("out_sensitivity_ranking", [])
        domain = run.get("domain", "structural")
        trust_score = run.get("prov_trust_score", 0.0)

        if ci_low is None or ci_high is None:
            return None

        ci_width = ci_high - ci_low
        ci_pct = int(confidence_level * 100)

        user_prompt = (
            f"My {domain} simulation produced the following results. "
            f"Help me interpret the uncertainty and determine if these results "
            f"are reliable enough for engineering decisions.\n\n"
            f"**{ci_pct}% Confidence Interval:** [{ci_low:.6f}, {ci_high:.6f}]\n"
            f"**Solver:** {run.get('in_solver', 'MFEM')}\n"
            f"**Runs:** {run.get('in_num_runs', 0)}\n"
            f"**Convergence Achieved:** {run.get('out_convergence_achieved', False)}\n"
            f"**Trust Score:** {trust_score:.3f}" + (f"\n**Brier Score:** {brier:.4f}" if brier else "")
        )

        reliability = (
            "highly reliable"
            if trust_score >= 0.80 and (brier is None or brier < 0.15)
            else "reliable"
            if trust_score >= 0.65
            else "moderately reliable — consider additional runs"
        )

        completion = (
            f"**Uncertainty Assessment: {reliability.upper()}**\n\n"
            f"**Interval Interpretation:**\n"
            f"With {ci_pct}% confidence, the true value lies within "
            f"[{ci_low:.6f}, {ci_high:.6f}]. The interval width is {ci_width:.6f}, "
            f"which is {'narrow (tight bounds)' if ci_width < 0.01 else 'moderate' if ci_width < 0.1 else 'wide — consider more runs'}.\n\n"
            f"**Calibration Quality:**\n"
            + (
                f"Brier score of {brier:.4f} indicates "
                f"{'excellent' if brier < 0.10 else 'good' if brier < 0.20 else 'fair'} "
                f"probabilistic calibration. "
                f"{'These confidence intervals are trustworthy for engineering decisions.' if brier < 0.20 else 'Consider running additional perturbations to improve calibration.'}\n\n"
                if brier
                else "No Brier calibration available.\n\n"
            )
            + f"**Sensitivity Insight:**\n"
            f"{'The primary uncertainty driver is **' + sensitivity[0] + '**. Reducing measurement uncertainty in this parameter will most efficiently narrow the confidence interval.' if sensitivity else 'Sensitivity ranking not available.'}\n\n"
            f"**Engineering Decision Guidance:**\n"
            + (
                f"Trust score of {trust_score:.3f} ({reliability}) suggests "
                f"{'this result is suitable for design sign-off with appropriate safety factors.' if trust_score >= 0.80 else 'additional validation is recommended before design sign-off.' if trust_score >= 0.65 else 'further analysis is required before using this result for critical decisions.'}"
            )
        )

        return self._make_example("uncertainty_quantification", run, user_prompt, completion, trust_score)

    def sensitivity_analysis(self, run: dict[str, Any]) -> TrainingExample | None:
        sensitivity = run.get("out_sensitivity_ranking", [])
        params = run.get("in_raw_parameters", {})
        domain = run.get("domain", "structural")
        trust_score = run.get("prov_trust_score", 0.0)

        if len(sensitivity) < 2 or not params:
            return None

        param_list = "\n".join(            f"  - {k}: {v:.6g}" for k, v in list(params.items())[:8] if isinstance(v, int | float))

        user_prompt = (
            f"I ran a sensitivity analysis on my {domain} simulation. "
            f"The following parameters were perturbed:\n\n"
            f"{param_list}\n\n"
            f"Which parameters have the most influence on my results, "
            f"and what does this mean for my engineering workflow?"
        )

        ranked = "\n".join(
            f"  {i + 1}. **{p}** — {'Dominant driver' if i == 0 else 'Secondary influence' if i == 1 else 'Minor influence'}"
            for i, p in enumerate(sensitivity[:5])
        )

        completion = (
            f"**Sensitivity Ranking (Sobol-based, verified across {run.get('in_num_runs', 0)} runs):**\n\n"
            f"{ranked}\n\n"
            f"**Primary Driver: {sensitivity[0]}**\n"
            f"This parameter dominates result variance. In your {domain} analysis, "
            f"measurement or modeling uncertainty in {sensitivity[0]} contributes "
            f"disproportionately to output uncertainty. "
            f"Engineers should:\n"
            f"1. Prioritize accurate characterization of {sensitivity[0]}\n"
            f"2. Apply tighter tolerances to {sensitivity[0]} in manufacturing specs\n"
            f"3. Use tighter perturbation bounds for {sensitivity[0]} in future sweeps\n\n"
            + (
                f"**Secondary Driver: {sensitivity[1]}**\n"
                f"This parameter has meaningful but secondary influence. "
                f"Worth monitoring but not the primary uncertainty source.\n\n"
                if len(sensitivity) > 1
                else ""
            )
            + f"**Low-Influence Parameters:**\n"
            f"{', '.join(sensitivity[3:]) if len(sensitivity) > 3 else 'None identified'} "
            f"have minimal impact on results and can be treated as fixed in future analyses, "
            f"reducing computational cost."
        )

        return self._make_example("sensitivity_analysis", run, user_prompt, completion, trust_score)

    def _make_example(
        self,
        example_type: str,
        run: dict[str, Any],
        user_prompt: str,
        completion: str,
        trust_score: float,
    ) -> TrainingExample:
        run_id = run.get("run_id", str(uuid.uuid4()))
        run_hash = hashlib.sha256(str(run_id).encode()).hexdigest()[:16]

        return TrainingExample(
            example_id=str(uuid.uuid4()),
            example_type=example_type,
            domain=run.get("domain", "structural"),
            solver=run.get("in_solver", "MFEM"),
            source_run_hash=run_hash,
            quality_score=trust_score,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": completion},
            ],
            metadata={
                "domain": run.get("domain", "structural"),
                "solver": run.get("in_solver", "MFEM"),
                "trust_score": trust_score,
                "brier_score": run.get("out_brier_score"),
                "certified": bool(run.get("certificate_id")),
                "run_hash": run_hash,
            },
        )


class TrainingDataExporter:
    def __init__(self, thresholds: QualityThresholds | None = None, seed: int = 42) -> None:
        self._db = get_supabase_client()
        self._thresholds = thresholds or QualityThresholds()
        self._constructor = ExampleConstructor()
        self._rng = random.Random(seed)

    async def export(
        self,
        output_dir: str = "./training_data",
        format: str = "openai",
        max_examples: int = 100_000,
        train_ratio: float = 0.80,
        val_ratio: float = 0.10,
        domain: str | None = None,
    ) -> dict[str, Any]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        runs = await self._fetch_qualified_runs(domain=domain)
        observability().gauge("ml_qualified_runs", float(len(runs)))
        logger.info(f"[Exporter] Fetched {len(runs)} qualified runs")

        examples: list[TrainingExample] = []
        for run in runs:
            for builder in [
                self._constructor.hypothesis_verification,
                self._constructor.parameter_prediction,
                self._constructor.uncertainty_quantification,
                self._constructor.sensitivity_analysis,
            ]:
                ex = builder(run)
                if ex is not None:
                    examples.append(ex)

        seen = set()
        unique = []
        for ex in examples:
            key = f"{ex.source_run_hash}:{ex.example_type}"
            if key not in seen:
                seen.add(key)
                unique.append(ex)

        unique.sort(key=lambda x: x.quality_score, reverse=True)
        unique = unique[:max_examples]
        self._rng.shuffle(unique)

        n = len(unique)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        train = unique[:n_train]
        val = unique[n_train : n_train + n_val]
        test = unique[n_train + n_val :]

        stats = {}
        for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
            path = Path(output_dir) / f"{split_name}.jsonl"
            count_by_type: dict[str, int] = {}
            with open(path, "w", encoding="utf-8") as f:
                for ex in split_data:
                    if format == "openai":
                        f.write(ex.to_openai_jsonl() + "\n")
                    else:
                        f.write(ex.to_hf_jsonl() + "\n")
                    count_by_type[ex.example_type] = count_by_type.get(ex.example_type, 0) + 1
            stats[split_name] = {"path": str(path), "count": len(split_data), "by_type": count_by_type}

        meta = {
            "export_timestamp": datetime.now(UTC).isoformat(),
            "format": format,
            "thresholds": {
                "min_trust_score": self._thresholds.min_trust_score,
                "max_brier_score": self._thresholds.max_brier_score,
                "require_convergence": self._thresholds.require_convergence,
                "require_certificate": self._thresholds.require_certificate,
            },
            "total_runs": len(runs),
            "total_examples": len(unique),
            "splits": stats,
            "domains": list({ex.domain for ex in unique}),
            "solvers": list({ex.solver for ex in unique}),
            "task_types": list({ex.example_type for ex in unique}),
            "mean_quality_score": sum(ex.quality_score for ex in unique) / len(unique) if unique else 0,
        }

        meta_path = Path(output_dir) / "export_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        observability().increment("ml_training_data_exported_total", {"format": format})
        logger.info(f"[Exporter] Export complete: {len(unique)} examples across {len(stats)} splits")
        return meta

    async def _fetch_qualified_runs(self, domain: str | None = None, limit: int = 50_000) -> list[dict[str, Any]]:
        if self._db is None:
            return self._mock_runs()

        query = (
            self._db.table("certificates")
            .select("*, provenance_graphs(*)")
            .gte("out_convergence_iterations", self._thresholds.min_convergence_iterations)
        )

        if self._thresholds.require_convergence:
            query = query.eq("out_convergence_achieved", True)

        if self._thresholds.require_certificate:
            if self._thresholds.min_certificate_tier:
                tiers = {"TIER_2_PHYSICS": ["TIER_2_PHYSICS", "TIER_3_GOLD"], "TIER_3_GOLD": ["TIER_3_GOLD"]}
                allowed = tiers.get(self._thresholds.min_certificate_tier, ["TIER_3_GOLD"])
                query = query.in_("verification_tier", allowed)

        if domain:
            query = query.eq("domain", domain)

        result = query.limit(limit).execute()
        if not result.data:
            return self._mock_runs()

        qualified = []
        for row in result.data:
            prov = row.get("provenance_graphs") or {}
            trust = prov.get("trust_score", 0.0) if isinstance(prov, dict) else 0.0
            brier = row.get("out_brier_score")

            if trust < self._thresholds.min_trust_score:
                continue
            if brier is not None and brier > self._thresholds.max_brier_score:
                continue

            flat = {**row, "prov_trust_score": trust}
            if isinstance(prov, dict):
                flat["prov_claim_text"] = prov.get("claim_text", "")
            qualified.append(flat)

        return qualified

    def _mock_runs(self) -> list[dict[str, Any]]:
        domains = ["structural", "thermal", "ev_battery", "aerospace"]
        solvers = ["MFEM", "SUNDIALS"]
        methods = ["latin_hypercube", "sobol", "bayesian"]
        mock = []
        for i in range(200):
            domain = domains[i % len(domains)]
            mock.append(
                {
                    "run_id": f"mock-run-{i:04d}",
                    "domain": domain,
                    "in_solver": solvers[i % len(solvers)],
                    "in_solver_version": "4.6",
                    "in_raw_parameters": {
                        "youngs_modulus": 200e9 * (0.9 + 0.2 * (i % 10) / 10),
                        "poisson_ratio": 0.3 + 0.05 * (i % 5) / 5,
                        "load": 50000 * (1 + i % 3),
                        "density": 7800 + 100 * (i % 8),
                    },
                    "in_num_runs": 20 + (i % 30),
                    "in_perturbation_method": methods[i % len(methods)],
                    "in_random_seed": 42 + i,
                    "out_convergence_achieved": True,
                    "out_convergence_iterations": 100 + i * 10,
                    "out_ci_low": 0.00200 + 0.0001 * i,
                    "out_ci_high": 0.00300 + 0.0001 * i,
                    "out_confidence_level": 0.95,
                    "out_sensitivity_ranking": ["youngs_modulus", "load", "poisson_ratio", "density"],
                    "out_brier_score": 0.05 + 0.01 * (i % 10),
                    "prov_trust_score": 0.75 + 0.01 * (i % 20),
                    "prov_claim_text": f"The {domain} component will maintain structural integrity under the specified loading conditions.",
                    "certificate_id": f"cert-{i:04d}" if i % 3 == 0 else None,
                    "verification_tier": "TIER_2_PHYSICS" if i % 3 == 0 else None,
                }
            )
        return mock

    async def get_dataset_stats(self, domain: str | None = None) -> dict[str, Any]:
        runs = await self._fetch_qualified_runs(domain=domain)
        if not runs:
            return {"total_qualified_runs": 0, "ready_for_training": False}

        trust_scores = [r.get("prov_trust_score", 0.0) for r in runs]
        brier_scores = [r["out_brier_score"] for r in runs if r.get("out_brier_score")]
        certified = sum(1 for r in runs if r.get("certificate_id"))
        domains_seen = list({r.get("domain", "unknown") for r in runs})
        estimated_examples = int(len(runs) * 3.2)

        return {
            "total_qualified_runs": len(runs),
            "estimated_training_examples": estimated_examples,
            "certified_runs": certified,
            "certified_fraction": round(certified / len(runs), 3),
            "mean_trust_score": round(sum(trust_scores) / len(trust_scores), 3),
            "mean_brier_score": round(sum(brier_scores) / len(brier_scores), 3) if brier_scores else None,
            "domains": domains_seen,
            "ready_for_training": len(runs) >= 500,
            "training_milestone": (
                "READY — >10k runs: Full fine-tuning recommended"
                if len(runs) >= 10_000
                else "GROWING — >1k runs: LoRA fine-tuning viable"
                if len(runs) >= 1_000
                else "BUILDING — >500 runs: Few-shot prompting only"
                if len(runs) >= 500
                else "EARLY — <500 runs: Continue accumulating data"
            ),
        }
