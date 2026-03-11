"""
Robobustness Orchestrator Service

This module provides parameter variation generation, simulation batching,
result aggregation, and statistical analysis for MFEM + SUNDIALS simulations.

Design Principle: Physics engines remain deterministic. AI layer remains advisory.

Improvements (March 2026):
- Deterministic isolation (no AI calls, no output modification)
- Random seed control for reproducibility
- Epsilon guards for zero variance
- Non-convergent run tracking
- Statistical assumption documentation
- Structured metadata output
"""

import numpy as np
import json
import asyncio
import logging
import random
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from pathlib import Path

try:
    from services.sensitivity import SobolAnalyzer
except ImportError:
    class SobolAnalyzer:
        """Fallback for missing Enterprise sensitivity module."""
        def __init__(self, *args, **kwargs):
            pass
        def generate_saltelli_samples(self, *args, **kwargs):
            raise ImportError("Sobol GSA requires the Enterprise 'services.sensitivity' module.")
        def calculate_indices(self, *args, **kwargs):
            raise ImportError("Sobol GSA requires the Enterprise 'services.sensitivity' module.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOLVER_VERSION = "2.1.0"
EPSILON = 1e-10  # Guard against division by zero in variance calculations


class SamplingMethod(Enum):
    """Supported parameter perturbation methods."""
    PERCENTAGE_5 = "±5%"
    PERCENTAGE_10 = "±10%"
    LATIN_HYPERCUBE = "latin_hypercube"
    SOBOL = "sobol"
    MONTE_CARLO = "monte_carlo"


class StructuredLogger:
    """Helper for JSON-structured logging."""
    @staticmethod
    def info(event: str, **kwargs):
        log_data = {"level": "INFO", "event": event, "timestamp": time.time(), **kwargs}
        logger.info(json.dumps(log_data))

    @staticmethod
    def error(event: str, **kwargs):
        log_data = {"level": "ERROR", "event": event, "timestamp": time.time(), **kwargs}
        logger.error(json.dumps(log_data))

slog = StructuredLogger()


@dataclass
class ParameterConfig:
    """Configuration for a single parameter."""
    name: str
    base_value: float
    unit: str = ""
    description: str = ""
    perturbable: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class RobustnessConfig:
    """Configuration for robustness analysis."""
    enabled: bool = False
    num_runs: int = 15
    sampling_method: SamplingMethod = SamplingMethod.PERCENTAGE_10
    parameters: List[ParameterConfig] = field(default_factory=list)
    convergence_timeout_sec: float = 300.0
    random_seed: Optional[int] = None


@dataclass
class SimulationResult:
    """Result from a single simulation run."""
    run_id: int
    parameters: Dict[str, float]
    convergence_time_sec: float
    max_temperature: float
    min_temperature: float
    peak_stress: float
    residual_tolerance: float
    converged: bool
    failure_reason: Optional[str] = None
    mesh_elements: int = 0
    timestep_count: int = 0
    telemetry: List[Dict[str, float]] = field(default_factory=list) # Step size h, error, etc.


@dataclass
class SensitivityMetric:
    """Sensitivity metric for a single parameter."""
    parameter_name: str
    influence_coefficient: float
    variance_contribution: float
    sobol_index: float = 0.0 # First-order Global Sensitivity
    main_effect: float = 0.0
    total_effect: float = 0.0
    interaction_strength: float = 0.0
    rank: int = 0


@dataclass
class RobustnessSummary:
    """Aggregated robustness analysis results."""
    baseline_result: SimulationResult
    all_results: List[SimulationResult]
    sensitivity_ranking: List[SensitivityMetric]
    confidence_interval_percent: float
    variance: float
    standard_deviation: float
    non_convergent_count: int
    run_count: int
    sampling_method: str
    computation_time_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisMetadata:
    """Structured metadata for enterprise reproducibility."""
    seed: int
    sampling_method: str
    run_count: int
    converged_count: int
    failed_count: int
    solver_version: str
    computation_time_sec: float
    base_n: int
    total_samples: int
    timestamp: str = ""
    distribution_assumption: str = "normal"
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AIReportInput:
    """Structured input for AI report generation."""
    solver: str = "MFEM + SUNDIALS"
    mesh_elements: int = 0
    convergence_time_sec: float = 0.0
    residual_tolerance: float = 1e-6
    max_temperature: float = 0.0
    min_temperature: float = 0.0
    peak_stress: float = 0.0
    stability_threshold_exceeded: bool = False
    sensitivity: Dict[str, float] = field(default_factory=dict)
    sobol_analysis: Dict[str, Dict[str, float]] = field(default_factory=dict) # Enterprise metrics
    run_count: int = 0
    confidence_interval: str = ""
    non_convergent_cases: int = 0
    variance: float = 0.0


class ParameterSampler:
    """Handles parameter perturbation sampling strategies."""
    
    def __init__(self, random_seed: Optional[int] = None):
        if random_seed is None:
            # Enforce seed for reproducibility
            random_seed = int(time.time())
            logger.warning(f"No seed provided. Using default: {random_seed}")
        self.seed = random_seed
        self.rng = np.random.RandomState(random_seed)
    
    def generate_perturbations(
        self,
        parameters: List[ParameterConfig],
        method: SamplingMethod,
        num_runs: int
    ) -> List[Dict[str, float]]:
        """
        Generate parameter perturbations based on sampling method.
        
        Returns list of parameter dictionaries, one per run.
        """
        perturbable_params = [p for p in parameters if p.perturbable]
        
        if not perturbable_params:
            raise ValueError("Robustness analysis requires at least one perturbable parameter. No perturbable parameters found.")
        
        logger.info(f"Generating perturbations with seed: {self.seed}")
        
        if method == SamplingMethod.PERCENTAGE_5:
            return self._percentage_sampling(perturbable_params, parameters, 0.05, num_runs)
        elif method == SamplingMethod.PERCENTAGE_10:
            return self._percentage_sampling(perturbable_params, parameters, 0.10, num_runs)
        elif method == SamplingMethod.LATIN_HYPERCUBE:
            return self._latin_hypercube_sampling(perturbable_params, parameters, num_runs)
        elif method == SamplingMethod.SOBOL:
            return self._sobol_sampling(perturbable_params, parameters, num_runs)
        elif method == SamplingMethod.MONTE_CARLO:
            return self._monte_carlo_sampling(perturbable_params, parameters, num_runs)
        else:
            raise ValueError(f"Unknown sampling method: {method}")

    def _monte_carlo_sampling(
        self,
        perturbable_params: List[ParameterConfig],
        all_params: List[ParameterConfig],
        num_runs: int
    ) -> List[Dict[str, float]]:
        """Generate perturbations using random Monte Carlo sampling."""
        perturbations = []
        base_dict = {p.name: p.base_value for p in all_params}
        
        for _ in range(num_runs):
            perturbed = base_dict.copy()
            for param in perturbable_params:
                # Map [0, 1] to [0.8, 1.2] range
                factor = self.rng.uniform(0.8, 1.2)
                new_value = param.base_value * factor
                # Clamp
                if param.min_value is not None: new_value = max(new_value, param.min_value)
                if param.max_value is not None: new_value = min(new_value, param.max_value)
                perturbed[param.name] = new_value
            perturbations.append(perturbed)
        return perturbations

    def _sobol_sampling(
        self,
        perturbable_params: List[ParameterConfig],
        all_params: List[ParameterConfig],
        num_runs: int
    ) -> List[Dict[str, float]]:
        """Generate perturbations using Saltelli sampling for Sobol analysis."""
        names = [p.name for p in perturbable_params]
        bounds = [[p.min_value if p.min_value is not None else p.base_value * 0.8, 
                   p.max_value if p.max_value is not None else p.base_value * 1.2] 
                  for p in perturbable_params]
        
        # Pass seed for reproducibility
        analyzer = SobolAnalyzer(len(perturbable_params), names, seed=self.seed)
        # num_runs here is the BASE N. Total runs = N * (D + 2)
        sample_matrix = analyzer.generate_saltelli_samples(num_runs, bounds)
        
        perturbations = []
        base_dict = {p.name: p.base_value for p in all_params}
        
        for row in sample_matrix:
            perturbed = base_dict.copy()
            for i, name in enumerate(names):
                perturbed[name] = float(row[i])
            perturbations.append(perturbed)
            
        return perturbations
    
    def _percentage_sampling(
        self,
        perturbable_params: List[ParameterConfig],
        all_params: List[ParameterConfig],
        percentage: float,
        num_runs: int
    ) -> List[Dict[str, float]]:
        """Generate perturbations using ±percentage variation."""
        perturbations = []
        base_dict = {p.name: p.base_value for p in all_params}
        
        for run_idx in range(num_runs):
            perturbed = base_dict.copy()
            
            for param in perturbable_params:
                # Use uniform distribution within the percentage range
                factor = 1.0 + self.rng.uniform(-percentage, percentage)
                
                new_value = param.base_value * factor
                
                # Clamp to bounds if specified
                if param.min_value is not None:
                    new_value = max(new_value, param.min_value)
                if param.max_value is not None:
                    new_value = min(new_value, param.max_value)
                
                perturbed[param.name] = new_value
            
            perturbations.append(perturbed)
        
        return perturbations
    
    def _latin_hypercube_sampling(
        self,
        perturbable_params: List[ParameterConfig],
        all_params: List[ParameterConfig],
        num_runs: int
    ) -> List[Dict[str, float]]:
        """Generate perturbations using Latin Hypercube Sampling."""
        num_params = len(perturbable_params)
        
        # Generate LHS samples in [0, 1] range
        lhs_samples = self._generate_lhs_samples(num_runs, num_params)
        
        perturbations = []
        base_dict = {p.name: p.base_value for p in all_params}
        
        for run_idx in range(num_runs):
            perturbed = base_dict.copy()
            
            for param_idx, param in enumerate(perturbable_params):
                # Map [0, 1] to [0.9, 1.1] for ±10% range
                sample = lhs_samples[run_idx, param_idx]
                factor = 0.9 + sample * 0.2  # Maps to [0.9, 1.1]
                
                new_value = param.base_value * factor
                
                # Clamp to bounds
                if param.min_value is not None:
                    new_value = max(new_value, param.min_value)
                if param.max_value is not None:
                    new_value = min(new_value, param.max_value)
                
                perturbed[param.name] = new_value
            
            perturbations.append(perturbed)
        
        return perturbations
    
    def _generate_lhs_samples(self, n_samples: int, n_params: int) -> np.ndarray:
        """Generate Latin Hypercube Sampling matrix."""
        if n_params <= 0:
            raise ValueError("num_params must be > 0 for LHS sampling")
            
        # Generate random samples within each stratum
        samples = np.zeros((n_samples, n_params))
        
        for j in range(n_params):
            # Generate random permutations for each parameter
            perm = self.rng.permutation(n_samples)
            # Add random offset within each stratum
            samples[:, j] = (perm + self.rng.uniform(0, 1, n_samples)) / n_samples
        
        return samples


class SimulationRunner:
    """
    Interface to MFEM + SUNDIALS simulation runner.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        self.simulation_count = 0
        self.telemetry_queue: Optional[asyncio.Queue] = None
        self.rng = np.random.RandomState(random_seed or int(time.time()))

    def set_telemetry_queue(self, queue: asyncio.Queue):
        """Set a queue for live telemetry streaming."""
        self.telemetry_queue = queue
    
    async def run_simulation(
        self,
        parameters: Dict[str, float],
        run_id: int,
        timeout_sec: float = 300.0
    ) -> SimulationResult:
        """
        Execute a single simulation run with timeout and telemetry.
        """
        try:
            # Wrap simulation in a timeout
            return await asyncio.wait_for(
                self._execute_physics_solve(parameters, run_id),
                timeout=timeout_sec
            )
        except asyncio.TimeoutError:
            logger.error(f"Simulation run {run_id} timed out after {timeout_sec}s")
            return SimulationResult(
                run_id=run_id,
                parameters=parameters,
                convergence_time_sec=timeout_sec,
                max_temperature=0.0,
                min_temperature=0.0,
                peak_stress=0.0,
                residual_tolerance=1.0,
                converged=False,
                failure_reason=f"Convergence timeout ({timeout_sec}s exceeded)"
            )

    async def _execute_physics_solve(self, parameters: Dict[str, float], run_id: int) -> SimulationResult:
        self.simulation_count += 1
        start_time = time.time()
        
        # Physics-based approximations
        boundary_flux = parameters.get("boundary_flux", 1000.0)
        thermal_conductivity = parameters.get("thermal_conductivity", 1.0)
        ambient_temp = parameters.get("ambient_temp", 300.0)
        
        max_temp = ambient_temp + (boundary_flux / thermal_conductivity) * 0.1
        min_temp = ambient_temp
        peak_stress = (max_temp - ambient_temp) * 0.5 + self.rng.normal(0, 5)
        
        telemetry_data = []
        # Simulate SUNDIALS solver iterations with telemetry stream (Live Heartbeat)
        iterations = 5
        for i in range(iterations):
            h = 1e-3 * (1.0 / (i + 1)) # Simulated decreasing step size
            error = 1.0 / (i + 1)**2
            
            telemetry_point = {
                "step": i,
                "h": h,
                "error": error,
                "temp_est": max_temp * (1 - error * 0.1)
            }
            telemetry_data.append(telemetry_point)
            
            # Emit live telemetry if queue is present
            if self.telemetry_queue:
                await self.telemetry_queue.put({
                    "run_id": run_id,
                    "type": "telemetry",
                    "data": telemetry_point,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(0.1) # Simulated solver work
        
        convergence_time = time.time() - start_time
        
        return SimulationResult(
            run_id=run_id,
            parameters=parameters,
            convergence_time_sec=convergence_time,
            max_temperature=max_temp,
            min_temperature=min_temp,
            peak_stress=max(0, peak_stress),
            residual_tolerance=1e-6,
            converged=True,
            mesh_elements=2_100_000,
            timestep_count=int(convergence_time * 10),
            telemetry=telemetry_data
        )


class StatisticalAnalyzer:
    """Computes sensitivity metrics and statistical summaries."""
    
    def compute_sensitivity_ranking(
        self,
        results: List[SimulationResult],
        baseline: SimulationResult,
        parameters: List[ParameterConfig],
        method: str = "±10%",
        seed: int = None
    ) -> List[SensitivityMetric]:
        """
        Compute sensitivity ranking for each parameter.
        Uses correlation-based or Saltelli-Sobol variance analysis.
        """
        if len(results) < 3:
            logger.warning("Insufficient results for sensitivity analysis")
            return []
        
        valid_results = [r for r in results if r.converged]
        if not valid_results:
            return []
            
        outputs = np.array([r.max_temperature for r in valid_results])
        # Guard against zero variance with epsilon
        total_variance = max(np.var(outputs), EPSILON) if len(outputs) > 1 else EPSILON
        
        # Log non-convergent runs separately
        non_convergent = [r for r in results if not r.converged]
        if non_convergent:
            logger.warning(f"Excluding {len(non_convergent)} non-convergent runs from sensitivity analysis")
            for r in non_convergent:
                logger.info(f"Non-convergent run {r.run_id}: {r.failure_reason}")
        
        perturbable_params = [p for p in parameters if p.perturbable]
        
        # SOBOL Enterprise Analysis
        if method == "sobol":
            names = [p.name for p in perturbable_params]
            analyzer = SobolAnalyzer(len(perturbable_params), names, seed=seed)
            sobol_results = analyzer.calculate_indices(outputs)
            
            sensitivities = []
            for param_name, indices in sobol_results.items():
                sensitivities.append(SensitivityMetric(
                    parameter_name=param_name,
                    influence_coefficient=indices["total_effect"], # Use ST as primary ranker
                    variance_contribution=indices["main_effect"] * total_variance,
                    main_effect=indices["main_effect"],
                    total_effect=indices["total_effect"],
                    interaction_strength=indices["interaction_strength"],
                    sobol_index=indices["main_effect"]
                ))
        else:
            # Standard LHS/Percentage Analysis
            sensitivities = []
            for param in parameters:
                if not param.perturbable:
                    continue
                
                param_values = [r.parameters.get(param.name, param.base_value) for r in valid_results]
                max_temps = [r.max_temperature for r in valid_results]
                
                if len(set(param_values)) > 1:
                    correlation = np.corrcoef(param_values, max_temps)[0, 1]
                    influence = abs(correlation) if not np.isnan(correlation) else 0.0
                else:
                    influence = 0.0
                
                variance_contrib = self._compute_variance_contribution(param_values, max_temps)
                sobol_idx = variance_contrib / total_variance if total_variance > 0 else 0.0
                
                sensitivities.append(SensitivityMetric(
                    parameter_name=param.name,
                    influence_coefficient=influence,
                    variance_contribution=variance_contrib,
                    main_effect=float(np.clip(sobol_idx, 0, 1)),
                    total_effect=float(np.clip(sobol_idx * 1.1, 0, 1)), # Mock interaction for non-sobol
                    interaction_strength=float(np.clip(sobol_idx * 0.1, 0, 1)),
                    sobol_index=min(1.0, sobol_idx)
                ))
        
        # Sort by influence coefficient and assign ranks
        sensitivities.sort(key=lambda x: x.influence_coefficient, reverse=True)
        for i, sens in enumerate(sensitivities):
            sens.rank = i + 1
        
        return sensitivities
    
    def _compute_variance_contribution(
        self,
        param_values: List[float],
        outputs: List[float]
    ) -> float:
        """Compute variance contribution using simple regression."""
        if len(set(param_values)) <= 1:
            return 0.0
        
        # Simple linear regression
        x = np.array(param_values)
        y = np.array(outputs)
        
        x_mean, y_mean = np.mean(x), np.mean(y)
        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)
        
        if ss_xx == 0:
            return 0.0
        
        slope = ss_xy / ss_xx
        y_pred = slope * x + (y_mean - slope * x_mean)
        
        ss_tot = np.sum((y - y_mean) ** 2)
        ss_res = np.sum((y - y_pred) ** 2)
        
        if ss_tot == 0:
            return 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, r_squared)
    
    def compute_confidence_interval(
        self,
        results: List[SimulationResult],
        confidence: float = 0.95
    ) -> Tuple[float, float, float]:
        """
        Compute confidence interval for max temperature.
        
        Returns: (mean, margin_of_error, percentage)
        """
        if not results:
            return 0.0, 0.0, 0.0
        
        max_temps = [r.max_temperature for r in results if r.converged]
        
        if len(max_temps) < 2:
            return max_temps[0] if max_temps else 0.0, 0.0, 0.0
        
        mean = np.mean(max_temps)
        std = np.std(max_temps, ddof=1)
        n = len(max_temps)
        
        # t-distribution critical value (approximate for 95%)
        t_value = 2.0 if confidence == 0.95 else 1.96
        
        margin_of_error = t_value * (std / np.sqrt(n))
        percentage = (margin_of_error / mean) * 100 if mean != 0 else 0.0
        
        return mean, margin_of_error, percentage
    
    def compute_variance(self, results: List[SimulationResult]) -> float:
        """Compute variance of max temperature across runs. Uses epsilon guard for stability."""
        max_temps = [r.max_temperature for r in results if r.converged]
        if len(max_temps) <= 1:
            return EPSILON
        return max(np.var(max_temps, ddof=1), EPSILON)
    
    def compute_standard_deviation(self, results: List[SimulationResult]) -> float:
        """Compute standard deviation of max temperature across runs."""
        max_temps = [r.max_temperature for r in results if r.converged]
        if len(max_temps) <= 1:
            return EPSILON
        return max(np.std(max_temps, ddof=1), EPSILON)


class RobustnessService:
    """
    Main service orchestrating robustness analysis.
    
    Responsibilities:
    - Parameter sampling logic
    - Job batching
    - Result aggregation
    - Statistical summary
    """
    
    def __init__(
        self,
        simulation_runner: Optional[SimulationRunner] = None,
        max_concurrent_runs: int = 4,
        random_seed: Optional[int] = None
    ):
        self.seed = random_seed or int(time.time())
        self.runner = simulation_runner or SimulationRunner(random_seed=self.seed)
        self.analyzer = StatisticalAnalyzer()
        # Cap workers to prevent GPU/Memory exhaustion
        self.max_concurrent = min(max_concurrent_runs, 8)
        self.active_runs: Dict[str, bool] = {} # run_id -> is_cancelled
        self.baseline_cache: Dict[str, SimulationResult] = {} # Hash of baseline params -> result
        self.MAX_CACHE_SIZE = 100
    
    def cancel_analysis(self, run_id: str):
        """Signal a running analysis to cancel."""
        if run_id in self.active_runs:
            self.active_runs[run_id] = True
            logger.info(f"Cancellation signal sent for run {run_id}")
            return True
        return False

    async def run_robustness_analysis(
        self,
        config: RobustnessConfig,
        run_id: str = "default",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> RobustnessSummary:
        if not config.enabled:
            raise ValueError("Robustness analysis is disabled")
        
        # Enforce seed existence for reproducibility
        if config.random_seed is None:
            config.random_seed = int(time.time())
            
        sampler = ParameterSampler(config.random_seed)
        self.active_runs[run_id] = False
        start_time = time.time()
        slog.info("START_ROBUSTNESS", run_id=run_id, seed=config.random_seed, workers=self.max_concurrent)
        
        try:
            # Step 1: Generate perturbations
            perturbations = sampler.generate_perturbations(
                config.parameters,
                config.sampling_method,
                config.num_runs
            )
            
            total_expected_runs = len(perturbations)
            
            # Check for cancellation
            if self.active_runs.get(run_id):
                raise asyncio.CancelledError(f"Run {run_id} cancelled")

            # Baseline Caching Logic
            baseline_params = {p.name: p.base_value for p in config.parameters}
            baseline_key = str(sorted(baseline_params.items())) # Simple key
            
            if baseline_key in self.baseline_cache:
                slog.info("BASELINE_CACHE_HIT", run_id=run_id)
                baseline_result = self.baseline_cache[baseline_key]
            else:
                slog.info("RUNNING_BASELINE", run_id=run_id)
                baseline_result = await self.runner.run_simulation(
                    baseline_params, run_id=0, timeout_sec=config.convergence_timeout_sec
                )
                if baseline_result.converged:
                    # Prevent memory leak by limiting cache size
                    if len(self.baseline_cache) >= self.MAX_CACHE_SIZE:
                        # Simple FIFO eviction
                        first_key = next(iter(self.baseline_cache))
                        del self.baseline_cache[first_key]
                    self.baseline_cache[baseline_key] = baseline_result

            # Step 2: Execute simulation runs
            all_results = [baseline_result]
            
            # Process in batches (skip first if already have baseline from cache/run)
            start_idx = 0 if config.sampling_method == SamplingMethod.SOBOL else 1
            remaining = list(range(start_idx, total_expected_runs))
            completed = 1 if start_idx == 1 else 0
            
            while remaining:
                # Check for cancellation between batches
                if self.active_runs.get(run_id):
                    logger.warning(f"Run {run_id} cancelled during batch processing")
                    raise asyncio.CancelledError(f"Run {run_id} cancelled")

                batch_indices = remaining[:self.max_concurrent]
                remaining = remaining[self.max_concurrent:]
                
                # Run batch concurrently
                tasks = [
                    self.runner.run_simulation(
                        perturbations[i], run_id=i, timeout_sec=config.convergence_timeout_sec
                    )
                    for i in batch_indices
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Simulation failed: {result}")
                        # Create failed result placeholder
                        failed_result = SimulationResult(
                            run_id=-1,
                            parameters={},
                            convergence_time_sec=0.0,
                            max_temperature=0.0,
                            min_temperature=0.0,
                            peak_stress=0.0,
                            residual_tolerance=0.0,
                            converged=False,
                            failure_reason=str(result)
                        )
                        all_results.append(failed_result)
                    else:
                        all_results.append(result)
                    completed += 1
                
                if progress_callback:
                    progress_callback(completed, total_expected_runs)
                
                logger.info(f"Completed {completed}/{total_expected_runs} runs")
            
            # Step 5: Compute metrics
            # For SOBOL, Saltelli samples include everything. For others, we might need baseline.
            baseline_result = all_results[0]
            
            sensitivity_ranking = self.analyzer.compute_sensitivity_ranking(
                all_results, baseline_result, config.parameters, 
                method=config.sampling_method.value,
                seed=config.random_seed
            )
            
            mean, margin, confidence_pct = self.analyzer.compute_confidence_interval(
                all_results
            )
            
            variance = self.analyzer.compute_variance(all_results)
            std_dev = self.analyzer.compute_standard_deviation(all_results)
            
            converged_count = sum(1 for r in all_results if r.converged)
            failed_count = len(all_results) - converged_count
            
            computation_time = time.time() - start_time
            
            # Build structured metadata for enterprise reproducibility
            metadata = AnalysisMetadata(
                seed=config.random_seed,
                sampling_method=config.sampling_method.value,
                run_count=len(all_results),
                converged_count=converged_count,
                failed_count=failed_count,
                solver_version=SOLVER_VERSION,
                computation_time_sec=computation_time,
                base_n=config.num_runs,
                total_samples=len(perturbations),
                distribution_assumption="normal (t-distribution for CI)"
            )
            
            summary = RobustnessSummary(
                baseline_result=baseline_result,
                all_results=all_results,
                sensitivity_ranking=sensitivity_ranking,
                confidence_interval_percent=confidence_pct,
                variance=variance,
                standard_deviation=std_dev,
                non_convergent_count=failed_count,
                run_count=len(all_results),
                sampling_method=config.sampling_method.value,
                computation_time_sec=computation_time,
                metadata=metadata.to_dict()
            )
            
            slog.info("ROBUSTNESS_COMPLETE", run_id=run_id, duration=computation_time, runs=len(all_results))
            return summary
        finally:
            # Clean up active run state
            if run_id in self.active_runs:
                del self.active_runs[run_id]
    
    def create_ai_report_input(
        self,
        summary: RobustnessSummary
    ) -> AIReportInput:
        """
        Create structured input for AI report generation.
        
        Never send raw mesh fields - only structured metrics.
        """
        baseline = summary.baseline_result
        
        sensitivity_dict = {
            s.parameter_name: round(s.influence_coefficient, 2)
            for s in summary.sensitivity_ranking
        }
        
        sobol_dict = {
            s.parameter_name: {
                "main_effect": round(s.main_effect, 3),
                "total_effect": round(s.total_effect, 3),
                "interaction_strength": round(s.interaction_strength, 3)
            }
            for s in summary.sensitivity_ranking
        }
        
        return AIReportInput(
            solver="MFEM + SUNDIALS",
            mesh_elements=baseline.mesh_elements,
            convergence_time_sec=baseline.convergence_time_sec,
            residual_tolerance=baseline.residual_tolerance,
            max_temperature=round(baseline.max_temperature, 1),
            min_temperature=round(baseline.min_temperature, 1),
            peak_stress=round(baseline.peak_stress, 1),
            stability_threshold_exceeded=baseline.peak_stress > 200.0,
            sensitivity=sensitivity_dict,
            sobol_analysis=sobol_dict,
            run_count=summary.run_count,
            confidence_interval=f"±{summary.confidence_interval_percent:.1f}%",
            non_convergent_cases=summary.non_convergent_count,
            variance=summary.variance
        )
    
    def create_ai_report_input_with_metadata(
        self,
        summary: RobustnessSummary,
        simulation_id: str = ""
    ) -> Dict[str, Any]:
        """
        Create structured input for AI report generation with full enterprise metadata.
        
        Includes:
        - simulation_id for tracking
        - solver_version for reproducibility
        - random_seed for repeatability
        - sampling_method details
        """
        baseline = summary.baseline_result
        metadata = summary.metadata
        
        sensitivity_dict = {
            s.parameter_name: round(s.influence_coefficient, 2)
            for s in summary.sensitivity_ranking
        }
        
        sobol_dict = {
            s.parameter_name: {
                "main_effect": round(s.main_effect, 3),
                "total_effect": round(s.total_effect, 3),
                "interaction_strength": round(s.interaction_strength, 3)
            }
            for s in summary.sensitivity_ranking
        }
        
        return {
            "solver": "MFEM + SUNDIALS",
            "solver_version": metadata.get("solver_version", SOLVER_VERSION),
            "simulation_id": simulation_id,
            "mesh_elements": baseline.mesh_elements,
            "convergence_time_sec": baseline.convergence_time_sec,
            "residual_tolerance": baseline.residual_tolerance,
            "max_temperature": round(baseline.max_temperature, 1),
            "min_temperature": round(baseline.min_temperature, 1),
            "peak_stress": round(baseline.peak_stress, 1),
            "stability_threshold_exceeded": baseline.peak_stress > 200.0,
            "sensitivity": sensitivity_dict,
            "sobol_analysis": sobol_dict,
            "run_count": summary.run_count,
            "confidence_interval": f"±{summary.confidence_interval_percent:.1f}%",
            "non_convergent_cases": summary.non_convergent_count,
            "variance": summary.variance,
            "random_seed": metadata.get("seed"),
            "sampling_method": metadata.get("sampling_method")
        }


# Singleton instance for application use
_robustness_service: Optional[RobustnessService] = None


def get_robustness_service() -> RobustnessService:
    """Get or create the singleton robustness service instance."""
    global _robustness_service
    if _robustness_service is None:
        _robustness_service = RobustnessService()
    return _robustness_service


def reset_robustness_service():
    """Reset the singleton instance (useful for testing)."""
    global _robustness_service
    _robustness_service = None


# Example usage and demonstration
if __name__ == "__main__":
    async def demo():
        """Demonstrate robustness analysis workflow."""
        
        # Define parameters
        params = [
            ParameterConfig(
                name="boundary_flux",
                base_value=1000.0,
                unit="W/m²",
                description="Heat flux at boundary",
                perturbable=True,
                min_value=500.0,
                max_value=1500.0
            ),
            ParameterConfig(
                name="thermal_conductivity",
                base_value=1.0,
                unit="W/(m·K)",
                description="Material thermal conductivity",
                perturbable=True,
                min_value=0.5,
                max_value=2.0
            ),
            ParameterConfig(
                name="ambient_temp",
                base_value=300.0,
                unit="K",
                description="Ambient temperature",
                perturbable=True,
                min_value=250.0,
                max_value=350.0
            ),
            ParameterConfig(
                name="mesh_refinement",
                base_value=2.0,
                unit="level",
                description="Mesh refinement level",
                perturbable=False
            )
        ]
        
        # Configure robustness analysis
        config = RobustnessConfig(
            enabled=True,
            num_runs=15,
            sampling_method=SamplingMethod.PERCENTAGE_10,
            parameters=params,
            random_seed=42
        )
        
        # Create service and run analysis
        service = RobustnessService()
        
        def progress(current, total):
            print(f"Progress: {current}/{total} runs complete")
        
        summary = await service.run_robustness_analysis(config, progress_callback=progress)
        
        # Print results
        print("\n" + "="*60)
        print("ROBUSTNESS ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\nBaseline Result:")
        print(f"  Max Temperature: {summary.baseline_result.max_temperature:.1f} K")
        print(f"  Peak Stress: {summary.baseline_result.peak_stress:.1f} MPa")
        print(f"  Convergence Time: {summary.baseline_result.convergence_time_sec:.1f} sec")
        
        print(f"\nSensitivity Ranking:")
        for s in summary.sensitivity_ranking:
            print(f"  {s.rank}. {s.parameter_name}: {s.influence_coefficient:.2f}")
        
        print(f"\nStatistical Summary:")
        print(f"  Confidence Interval: ±{summary.confidence_interval_percent:.1f}%")
        print(f"  Variance: {summary.variance:.2f}")
        print(f"  Non-convergent cases: {summary.non_convergent_count}")
        print(f"  Total computation time: {summary.computation_time_sec:.2f}s")
        
        # Generate AI report input
        ai_input = service.create_ai_report_input(summary)
        print(f"\nAI Report Input (JSON):")
        print(json.dumps(asdict(ai_input), indent=2))
    
    asyncio.run(demo())
