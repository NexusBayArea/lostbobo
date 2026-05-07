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

## Experiment Catalog (K8s-Level via Chaos Mesh)

### PodChaos
- **pod-kill-swarm.yaml** — Kills swarm/agent pods.
- **pod-kill-orchestrator.yaml** — Targets BeamOrchestrator / CPU nodes.

### NetworkChaos
- **network-delay.yaml** — 50-200ms latency + jitter.
- **network-packet-loss.yaml** — 10-30% loss.

### StressChaos
- **cpu-stress.yaml** — 80% CPU on selected pods.
- **memory-stress.yaml** — 512MiB memory hog.

## Running Experiments
```bash
# 1. Install Chaos Mesh (one-time)
make chaos-mesh-install

# 2. Run a specific experiment
make chaos-run EXPERIMENT=pod-kill-swarm

# 3. Cleanup
make chaos-cleanup
```

## Observability
- Dashboard: `grafana-dashboards/chaos/chaos-engineering.json`
- Key Metrics: `swarm_tasks_total`, `swarm_tasks_failed`, `swarm_retry_count`, `swarm_circuit_breaker_open`, `chaos_experiments_total`, `chaos_failures_injected`.

## Post-Mortem
(Template: Hypothesis, Actual vs Expected, Lessons, PRs)
