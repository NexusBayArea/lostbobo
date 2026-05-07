# SimHPC Chaos Engineering Playbook

> **Purpose**: Systematically validate resilience of swarm tasks, agents, orchestrators, BeamOrchestrator, and world model under real Kubernetes failures.
> **Scope**: App-level (Python) + K8s-level (Chaos Mesh) experiments.
> **Last Updated**: May 7, 2026

## Principles
- **Hypothesis-driven**: Every experiment starts with a clear hypothesis (e.g., "SwarmCoordinator will recover from 30% pod kills via retries + circuit breaker within 45s").
- **Blast Radius Control**: Use `mode: one` / `fixed-percent: 20` and label selectors limited to test tenants or `chaos: enabled`.
- **Observability First**: All experiments log to structured logs + Prometheus + Grafana.
- **Automated Recovery**: Leverage existing `SwarmResilience` (retries, circuit breakers, timeouts).
- **Safe by Default**: Chaos disabled in prod; enabled only via `CHAOS_ENABLED=true` + explicit namespace.

## Component-Specific Hypotheses & Experiments

Every experiment follows this template:
- **Hypothesis**: Expected resilient behavior
- **Chaos Experiments**: Recommended K8s + app-level injections
- **Success Criteria**: Measurable outcomes
- **Metrics to Watch**: Prometheus + Grafana panels
- **Run Command**: `make chaos-run EXPERIMENT=...`

---

### 1. Multi-Layer RAG (RAGRouter + DocumentIndex / StructuredIndex / ExperimentIndex)

**Hypothesis**:
The RAG system will maintain >95% query success rate and <2s P95 latency even under 30% pod kills, 200ms network latency, and partial Redis/Supabase timeouts. Cross-layer deduplication and domain-aware routing will continue to function correctly. SpeculativeOrchestrator will early-exit on high-confidence partial results.

**Chaos Experiments**:
- `network-delay` (150–250ms + 20% jitter)
- `pod-kill-swarm` (target RAG pods + VectorRAGAgent pods)
- App-level: `chaos_monkey` with `PARTIAL_SUCCESS` + `EXCEPTION` on `embed_text()` and `combine_results()`
- `cpu-stress` on RAG worker pods

**Success Criteria**:
- All 3 RAG layers return results within timeout (no full cascade failure)
- `combine_results()` deduplicates correctly despite missing chunks
- Circuit breaker opens after 5 failures → fallback to cached ExperimentIndex
- Recovery within 45s

**Metrics**:
- `rag_query_latency_seconds`, `rag_layer_success_rate`, `rag_deduplication_ratio`
- `swarm_retry_count` (RAG-specific)

**Run**: `make chaos-run EXPERIMENT=rag-full-suite`

---

### 2. World Model (Probabilistic Digital Twin + WorldState / DepthAttentionRegistry)

**Hypothesis**:
The World Model will preserve causal graph integrity and uncertainty propagation under pod restarts and memory stress. `update()` and `query()` will recover via SupabaseJobStore retries. DepthAttentionRegistry will still provide relevant prior_context to Planner/Analyst agents. Observational Memory loop (Observer → Reflector) will not lose high-confidence observations.

**Chaos Experiments**:
- `memory-stress` (512MiB hog on world-model pods)
- `pod-kill-orchestrator` (target Kernel + WorldBrain pods)
- App-level: `chaos_monkey` with `TIMEOUT` + `CIRCUIT_TRIGGER` on `propagate_uncertainty()` and `DEPTH_QUERY`
- `network-packet-loss` (15% loss to Supabase)

**Success Criteria**:
- WorldState persisted and queryable within 30s after failure
- Uncertainty fields remain bounded (no NaN explosion)
- Depth registry returns ≥80% relevant entries post-recovery
- Reflector triggers correctly on restored observations

**Metrics**:
- `world_model_update_success_rate`, `world_model_query_latency`, `depth_registry_hit_rate`
- `uncertainty_propagation_error`

**Run**: `make chaos-run EXPERIMENT=world-model-stress`

---

### 3. Physics Engine (Multi-Physics Coupler + MaterialPropertyService + SimulationRunner + PhysicsValidation)

**Hypothesis**:
The Physics Engine will gracefully degrade (partial simulation results + validation warnings) under heavy CPU stress and pod kills. MaterialPropertyService will fallback to cached values via RAG. RobustnessCheck will catch drift, and BeamOrchestrator will retry failed Monte Carlo paths. No silent corruption of simulation outputs.

**Chaos Experiments**:
- `cpu-stress` (80% CPU on physics pods)
- `pod-kill-swarm` (target A40 simulation pods)
- App-level: `chaos_monkey` with `LATENCY` + `EXCEPTION` on `run_monte_carlo_simulation()` and coupler
- Combined workflow: pod-kill → network-delay → stress

**Success Criteria**:
- 90%+ of Monte Carlo paths complete (with retries)
- PhysicsValidation flags degraded results correctly
- MaterialPropertyService returns cached values when Supabase is unreachable
- Full simulation certificate issued within 90s (with partial data)

**Metrics**:
- `physics_simulation_success_rate`, `monte_carlo_path_recovery_rate`
- `material_property_cache_hit_rate`, `robustness_check_pass_rate`
- `simulation_latency_seconds` (under chaos)

**Run**: `make chaos-run EXPERIMENT=physics-engine-chaos`

---

## How to Run a Full Component Validation Suite

```bash
# Example: Validate RAG + World Model together
make chaos-suite components="RAG WORLD_MODEL" iterations=8
```

## Post-Mortem
(Template: Hypothesis, Actual vs Expected, Lessons, PRs)
