# SimHPC Progress

## Goal
- Complete full-stack SimHPC: backend DAG + frontend + auth + GraphRAG + Swarm forecasting with Vercel deployment

## Constraints & Preferences
- Do not push progress.md (internal log only)
- Use ruff for linting/formatting
- Canonical `backend.*` namespace throughout

## Progress
### Done
- Swarm forecasting: backend/runtime/swarm/{bayesian_aggregator.py, conformal_bridge.py, swarm_coordinator.py}
- Swarm UI: frontend/src/components/SwarmControlPanel.tsx, backend/app/api/swarm.py
- Feedback & calibration: backend/runtime/feedback/{brier_engine.py, calibration_dashboard.py, feedback_dag_node.py}
- Orchestrator: backend/runtime/orchestrator/{queue_router.py, cascade.py}
- Simulation cache: backend/runtime/cache/{simulation_cache.py, zfp.py}
- Environment replay: backend/runtime/replay/engine.py
- Plugin framework: backend/plugins/{base.py, registry.py, ev_battery/, market_trading/}
- Multi-layer RAG: backend/runtime/rag/{router.py, document_index.py, structured_index.py, experiment_index.py}
- Beam Orchestrator: backend/core/models/hypothesis.py, backend/core/orchestrator/beam_orchestrator.py
- Agent layer: backend/core/agents/{base_agent.py, reasoning_agent.py, rag_agent.py, simulation_agent.py}
- Redis streaming: backend/core/redis/{beam_streamer.py}
- Robustness check: backend/core/robustness/{check.py}
- Simulation runner: backend/core/simulation/{runner.py}
- Provenance graph: backend/core/provenance/{graph.py}
- Certificate service: backend/core/certificate/{service.py}
- Fat skills registry: backend/core/skills/{registry.py, examples.py}
- Memory layer: backend/core/memory/{schema.py, service.py, reconciliation.py}
- World Model layer: backend/core/world_model/{schema.py, service.py}
- Analyst + Planner agents: backend/core/agents/{analyst.py, planner.py, orchestrator.py}
- Agent API routes: backend/app/api/agent_routes.py
- API router consolidation: backend/app/api/api_router.py, skills routes
- Redis consumer workers: backend/core/workers/{consumer.py}
- BeamOrchestratorService: backend/core/services/{beam_orchestrator_service.py}
- Kernel (single source of truth): backend/core/kernel/{kernel.py, command_bus.py, state/memory_state.py}
- API routes wired to Kernel: all routes now use kernel.execute()
- WorldState + WorldService (probabilistic digital twin): backend/core/kernel/state/world_state.py, services/world_service.py
- Auto-Research Engine (closed-loop optimization): backend/core/kernel/auto_research/{engine.py, evaluation.py, memory.py}
- CI stabilization: backend/ci.sh (pip install ruff, ruff format && check)
- All workflows: ci.yml, ci-validation.yml, deploy.yml, pre-commit.yml now use bash ci.sh

### In Progress
- None - all CI green

### Blocked
- None - CI green

## Key Decisions
- Replaced Makefile with ci.sh script for reliable CI (pip install ruff, then ruff format/check)
- README/ added to .gitignore to prevent pre-commit EOF cycle
- All workflows call bash ci.sh instead of make targets

## Next Steps
- None currently

## Critical Context
- Git: https://github.com/nexusbayarea/lostbobo
- Vercel: https://vercel.com/nexusbayareas-projects/simhpc
- CI: All 4 workflows green
- test_beam_orchestrator.py available for testing

## Relevant Files
- backend/ci.sh: Stable CI script
- backend/core/models/hypothesis.py: Canonical Hypothesis model
- backend/core/orchestrator/beam_orchestrator.py: Beam control plane
- backend/core/redis/beam_streamer.py: Redis streaming layer
- backend/runtime/rag/router.py: Multi-layer RAG router
- backend/runtime/swarm/swarm_coordinator.py: 5-agent swarm
- backend/runtime/feedback/brier_engine.py: Brier scoring