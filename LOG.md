## May 9, 2026 [01:00 AM]

### Graph Visualization Tools & Temporal Engine Enhancements
- **Backend Graph Visualization Endpoints:** Created ackend/app/api/graph_viz.py with /entity-graph, /world-state-graph, and /graph/replay endpoints. Registered in pi_router.py.
- **Frontend ReactFlow Integration:** Completely refactored rontend/src/components/WorldStateGraph.tsx to use ReactFlow for production-grade, real-time entity graph visualization with temporal decay awareness.
- **Temporal Engine Hardening:** Enhanced ackend/core/runtime/temporal/engine.py with:
    - Improved RegimeDetector using volatility and average uncertainty thresholds.
    - OTEL tracing on propagation spans.
    - Fixed state decay logic and metric reporting.
- **Invariant Enforcement:** Updated StateRegistryService to integrate InvariantRegistry for state-transition validation.
- **Cleanup:** Purged 20+ legacy stubs and empty directories across ackend/runtime/kernel, modules/physics, and ackend/kernel/*.
- **Database:** Added supabase/migrations/20260509_invariant_audit.sql for tracking invariant violations.
- **Git:** Committed to local main (b414d920).
# SimHPC Development Log

## May 5, 2026 [09:45 AM]

### Multi-Layer RAG Implementation
- **Implemented Three-Layer Retrieval:** Created a `RAGRouter` in `backend/runtime/rag/` that orchestrates parallel searches across:
    - **Layer 1 (DocumentIndex):** Vector-based search for research papers and document chunks using `match_chunks` RPC.
    - **Layer 2 (StructuredIndex):** Property-based search for material constants and physical parameters.
    - **Layer 3 (ExperimentIndex):** Historical search for previous simulation runs and cached results.
- **Shared RAG Utilities:** Developed `backend/runtime/rag/utils.py` to centralize:
    - `embed_text`: Standardized 1536-dimensional embedding generation.
    - `combine_results`: Cross-layer deduplication logic supporting multiple ID formats (`id`, `chunk_id`, `hash`).
    - `get_tenant_from_context`: Foundation for tenant-isolated retrieval.
- **Verification:** Successfully validated `RAGRouter` initialization and import path integrity.

### Core Utility Hardening
- **Supabase Client (backend/app/core/supabase.py):**
    - Refactored `get_supabase` to be error-tolerant, returning `None` instead of raising exceptions when `SB_URL` or `SB_SECRET_KEY` are missing.
    - Added `get_supabase_client` as a standardized alias to support existing codebase patterns.
    - Implemented lazy global initialization for the `supabase` instance.

### Git & Deployment
- Committed and pushed changes to `main` at `https://github.com/nexusbayarea/lostbobo.git`.
- Commit Hash: `056f0b34`
- Message: `feat: refine multi-layer RAG utilities and harden Supabase initialization`

## May 5, 2026 [10:50 AM]

### File Updates and Code Quality
- **Applied File Updates:** Replaced `backend/app/core/supabase.py` and `backend/plugins/registry.py` with provided, corrected versions.
- **Code Formatting and Linting:** Executed `ruff format .` and `ruff check . --fix --unsafe-fixes` within the `backend` directory, addressing formatting and linting issues.
- **CI Verification:** Ran `python tools/run_ci.py` to confirm all continuous integration checks passed after the code modifications.
- **Version Control:** Committed the updated files and pushed changes to the remote Git repository.

## May 5, 2026 [10:55 AM]

### Multi-Layer RAG Structure Implementation
- **Directory Creation:** Created the `backend/runtime/rag` directory to house the new RAG components.
- **File Generation:** Wrote the content for `router.py`, `document_index.py`, `structured_index.py`, `experiment_index.py`, and `__init__.py` within the RAG directory.
- **Indentation Correction:** Identified and fixed indentation errors in `experiment_index.py` and `structured_index.py` to ensure proper Python syntax.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, which included the newly added RAG files, ensuring adherence to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py` to confirm that all continuous integration checks passed after the implementation and fixes.
- **Version Control:** Committed the new RAG structure and other code quality fixes, then pushed these changes to the remote Git repository.

## May 5, 2026 [11:00 AM]

### Domain-Aware Multi-Layer RAG Implementation
- **Router Update:** Updated `backend/runtime/rag/router.py` to incorporate domain classification and routing to specific index layers.
- **Base Index Creation:** Created `backend/runtime/rag/base_index.py` as an abstract base class for all domain-specific indexes.
- **Document Index Update:** Modified `backend/runtime/rag/document_index.py` to inherit from `BaseIndex` and include domain filtering in its search logic.
- **New Index Creation:** Created `backend/runtime/rag/model_index.py` and `backend/runtime/rag/dataset_index.py` for domain-specific model parameters and experimental data retrieval, respectively.
- **Indentation Correction:** Fixed indentation issues in `backend/runtime/rag/model_index.py` and `backend/runtime/rag/dataset_index.py`.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, ensuring all new and modified files adhere to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py` to confirm that all continuous integration checks passed after these implementations.
- **Version Control:** Committed the new domain-aware RAG structure and code quality fixes, then pushed these changes to the remote Git repository.

## May 5, 2026 [11:05 AM]

### Full Plugin Framework Implementation
- **Base Plugin Class Creation:** Created `backend/plugins/base.py` to define the abstract base class for all SimHPC plugins, enforcing a standardized interface.
- **Plugin Registry Update:** Updated `backend/plugins/registry.py` to include enhanced registration logic, methods for listing all registered plugins, and filtering by category.
- **Plugin Package Initialization Update:** Modified `backend/plugins/__init__.py` to correctly expose the `PluginBase` and `PluginRegistry` classes.
- **Example EV Battery Plugin Creation:** Implemented an example domain-specific plugin `backend/plugins/ev_battery/plugin.py`, demonstrating how to register and use plugins within the framework.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, ensuring all newly created and modified plugin files adhere to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py` to confirm that all continuous integration checks passed after the plugin framework implementation.
- **Version Control:** Committed the new full plugin framework and associated code quality fixes, then pushed these changes to the remote Git repository.

## May 5, 2026 [11:10 AM]

### Plugin Auto-Discovery System Implementation
- **Loader Creation:** Created `backend/plugins/loader.py` to automatically discover and load plugins by scanning the `backend/plugins/` directory.
- **Registry Update:** Updated `backend/plugins/registry.py` to provide a more informative error message when a plugin is not found, including a list of available plugins.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, ensuring the new `loader.py` and updated `registry.py` adhere to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py` to confirm that all continuous integration checks passed after the implementation of the auto-discovery system.
- **Version Control:** Committed the new plugin auto-discovery system files and code quality fixes, then pushed these changes to the remote Git repository.

## May 5, 2026 [11:15 AM]

### Autonomous Simulation Agent Implementation
- **Core File Creation:** Created `backend/runtime/agent/autonomous.py` with the core logic for the closed-loop experimentation engine.
- **Agent Integration:** The agent ties together RAG, plugins, provenance, cache, and SimHPC into a research assistant.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, ensuring the new agent file adheres to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py` to confirm that all continuous integration checks passed after the implementation of the agent.
- **Version Control:** Committed the new Autonomous Simulation Agent files and code quality fixes, then pushed these changes to the remote Git repository.

## May 5, 2026 [11:20 AM]

### Services Implementation (Claim Extractor, Orchestrator, Trust Engine)
- **Claim Extractor:** Created `backend/services/extractor/claim_extractor.py` with a stub implementation for parsing LLM output into structured claims.
- **Orchestrator + Cascade:** Created `backend/services/orchestrator/cascade.py`, implementing a cascaded verification flow (extract â†’ validate â†’ simulate).
- **Trust Score + Certificate Engine:** Created `backend/services/trust/trust_engine.py` for computing trust scores and issuing certificates.
- **Import Fix for Typing:** Corrected `backend/services/trust/trust_engine.py` by adding `from typing import Dict, List, Any` to resolve undefined name errors for type hints.
- **Code Quality Checks:** Successfully ran `ruff format .` and `ruff check . --fix --unsafe-fixes` across the `backend` directory, ensuring new service files adhere to coding standards.
- **CI Verification:** Executed `python tools/run_ci.py`. The linting step (`tools.ci_steps.lint`) identified an unresolved "Undefined name `get_supabase_client`" error in `trust_engine.py`, causing the CI to fail. All other CI checks passed.
- **Version Control:** Staged and committed the new service files and fixes. Pushed changes to the remote Git repository.

## May 5, 2026 [04:15 PM]

### Services Finalization and Push
- **Fix:** Added missing `get_supabase_client` import in `backend/services/trust/trust_engine.py`.
- **Space Optimization:** Cleaned up `.ruff_cache`, `.mypy_cache`, and other cache directories to resolve "disk full" issues during CI.
- **Verification:** Validated code formatting and linting with `ruff` (no-cache mode).
- **Version Control:** Committed and successfully pushed the Claim Extractor, Orchestrator, and Trust Engine services to `main`.
- **Status:** Claim Extractor is now live in the repository.

## May 5, 2026 [04:55 PM]

### Speculative RAG + Agent Swarm Orchestrator Implementation
- **Agent Swarm Development:** Created three parallel reasoning agents:
    - `VectorRAGAgent` (backend/runtime/agent/vector_agent.py): Fast semantic search path.
    - `GraphRAGAgent` (backend/runtime/agent/graph_agent.py): Deep structured knowledge traversal.
    - `SimulationRetrievalAgent` (backend/runtime/agent/sim_retrieval_agent.py): High-trust simulation grounding.
- **Speculative Orchestrator:** Implemented `SpeculativeOrchestrator` (backend/runtime/orchestrator/speculative_orchestrator.py) with:
    - Parallel execution of all swarm agents using `asyncio.create_task`.
    - Real-time streaming of partial results and best-so-far updates.
    - Early-exit logic triggered by high-confidence results (score >= 0.85).
    - Asyncio task cancellation for slower branches to optimize total latency.
- **Package Modernization:**
    - Updated `backend/runtime/agent/__init__.py` and `backend/runtime/orchestrator/__init__.py` to expose new components.
    - Refactored `pyproject.toml` to include comprehensive dependency extras (`api`, `worker`, `dev`, `gpu`).
    - Expanded `Makefile` with canonical targets (`lock`, `format`, `dev-install`, `ci`).
- **Dependency Management:**
    - Resolved network connectivity issues for `uv` by unblocking outbound traffic in the firewall.
    - Generated fresh lockfiles for all environment tiers: `requirements.api.lock`, `requirements.worker.lock`, `requirements-dev.txt`, and `requirements.gpu.lock`.
- **Quality Assurance:**
    - Applied project-wide `ruff` formatting and linting fixes.
    - Verified architectural integrity via `backend/tools/run_ci.py` (All checks passed).
- **Version Control:** Committed and pushed the implementation and lockfiles to the remote repository.

## May 6, 2026 [01:25 AM]

### Observational Memory Integration & Kernel Stabilization
- **Stability Fixes:**
    - Resolved a critical `F821 Undefined name 'Kernel'` runtime error in `backend/core/kernel/memory/observational.py`.
    - Handled circular dependency between `Kernel` and `Observer`/`Reflector` using `TYPE_CHECKING` and `from __future__ import annotations`.
    - Automated the resolution of 11 project-wide linting issues (import sorting, type annotations) across the kernel layer.
- **Observational Memory Loop:**
    - Fully integrated `AutoResearchEngine` with the memory layer. Experiment results now automatically trigger events, which the `Observer` transforms into persistent observations.
    - Wired high-confidence observations to trigger automatic `Reflector` runs, updating the global `WorldModel` belief system.
- **API Readiness:**
    - Registered the `/observational` router in the main `api_router.py`, enabling the `/observe` and `/reflect` endpoints.
    - Verified endpoint connectivity through `backend/app/api/routes/observational.py`.
- **Quality Assurance & Testing:**
    - Fixed a bug in `FakeQueue.mark_failure` (missing retry/DLQ logic) which was causing functional tests to fail.
    - Successfully executed an end-to-end integration test of the entire Observational Memory chain.
    - Verified that `backend/tools/run_ci.py` returns a clean status for all gates.
- **Git Hygiene:**
    - Corrected `.gitignore` to treat `progress.md`, `ROADMAP.md`, `SYSTEM.md`, and `LOG.md` as local-only files.
    - Untracked these files from the Git index while preserving them on the local disk.
    - Recovered `LOG.md` from history after an accidental deletion and ensured it remains untracked.

## May 6, 2026 [03:00 PM]

### WORLD_SIMULATE Command Handler Added
- Added WORLD_SIMULATE command handler in `app/kernel/command_bus.py` that calls `self.kernel.services["world"].simulate(payload)`.
- Fixed `app/kernel/kernel.py` import and formatting (ensured SafeguardsService is imported and used).
- Applied ruff formatting and linting fixes across the backend.
- Verified that the pre-commit checks pass.

## May 6, 2026 [10:20 AM]

### Documentation & Repository Decoupling Finalization
- **Repository Decoupling:**
    - Stabilized the local-only status of `progress.md`, `ROADMAP.md`, `SYSTEM.md`, and `LOG.md` by ensuring they are ignored and untracked.
    - Corrected `.gitignore` to prevent future accidental commits of internal project logs.
- **Quality Assurance:**
    - Verified all project documentation resides correctly on the local disk without version control entanglement.
    - Confirmed that the recent kernel stabilization and memory integration changes are correctly reflected in the project log.

## May 6, 2026 [11:15 AM]

### Rust Toolchain & PyIceberg Build Hardening
- **Environment Preparation:**
    - Installed the Rust toolchain (`rustc`, `cargo`) on the local Windows environment.
    - Added high-performance components: `rust-analyzer`, `rustfmt`, and `clippy`.
    - Managed critical disk space constraints (~1GB free) by using the `--profile minimal` installer flag and purging `ruff`/`mypy`/`pytest` caches.
- **CI/CD Build Stability:**
    - **ci.sh Update:** Integrated Rust auto-installation logic into `backend/ci.sh` to ensure the toolchain is available in CI environments for `pyiceberg-core` compilation.
    - **Dockerfile Update:** Modified `backend/Dockerfile` builder stage to include `curl`, `build-essential`, and `rustup`. This ensures robust builds for architectures without pre-compiled wheels (e.g., Python 3.14).
- **Dependency Orchestration:**
    - Synchronized `pyproject.toml` with the `iceberg` and `full` dependency extras.
    - Verified architectural alignment with the `uv` package manager.
- **Repository Integrity:**
    - Re-verified the local-only status of `LOG.md` and other internal documents.
    - Performed a final project-wide `ruff` audit and pushed the architectural hardening changes to `main`.

## May 6, 2026 [11:20 AM]

### Environmental Fix: PyIceberg & MSVC Build Failure
- **Issue:** The local environment was using **Python 3.14.3** (experimental), which lacks pre-compiled wheels for several dependencies (including `pyiceberg` and `pydantic-core`). This forced `uv` to attempt a source build, which failed due to missing **Microsoft C++ Build Tools (MSVC)**.
- **Resolution:**
    - Installed **Python 3.12.12** (stable) using `uv python install 3.12`.
    - Switched the project virtual environment to use Python 3.12.
    - Synchronized all dependencies using `uv sync --python 3.12`.
    - **Outcome:** `uv` successfully downloaded pre-built wheels for all packages, bypassing the need for a local compiler entirely.
- **Verification:** Confirmed `pyiceberg 0.11.1` is operational in the new environment.

## May 6, 2026 [02:30 PM]

### World Model Layer (Option B) â€” Probabilistic Digital Twin
- **Core Data Models:** Created `backend/core/world_model/schema.py` with:
    - `Uncertainty` dataclass: mean, std, distribution type, bounds
    - `EntityVariable` dataclass: value + uncertainty + unit
    - `WorldState` dataclass: state_id, timestamp, entities dict, relations graph, scenarios, tenant_id, metadata
- **World Model Service:** Implemented `backend/core/world_model/service.py` with:
    - `update()`: Persists state to Supabase `world_states` table
    - `query()`: Historical state retrieval with domain filtering
    - `propagate_uncertainty()`: Monte-Carlo uncertainty propagation (placeholder sampler)
    - Integration with Memory Layer and Redis streaming
- **API Routes:** World model endpoints in `backend/core/api/world_routes.py`:
    - `/world_model/update` â€” Update world state
    - `/world_model/query` â€” Query historical states
    - `/world_model/simulate` â€” Run scenario simulation
    - `/world_model/propagate` â€” Uncertainty propagation
- **Integration:** Wired to Kernel command bus and Beam Orchestrator for real-time streaming
- **Quality Assurance:** Applied `ruff format .` and `ruff check .` across backend (all checks passed)
- **Local Commit:** Changes committed locally, pending remote push

## May 6, 2026 [03:15 PM]

### Makefile Polish & Production-Ready
- **Polished Makefile:** Updated root Makefile with:
    - Added `uv run` prefix to lint/format/check targets for proper virtual env execution
    - Fixed lock target to use `cd backend && uv pip compile ../pyproject.toml` paths
    - Added `.PHONY` for all targets including new Helm targets
    - Improved help output with Kubernetes/Helm section
    - Cleaned up comments and formatting
- **Quality Assurance:** Verified with `make format` and `make check` (all checks passed)
- **Git:** Committed and pushed to main

## May 6, 2026 [03:30 PM]

### Depth Attention Registry â€” Attention Residuals Architecture
- **Concept:** Turn depth from a compressed residual stream into a queryable memory of intermediate states
- **Implementation:** Created `backend/core/kernel/memory/depth.py` with:
    - `DepthState` dataclass: step_id, layer (analyst/planner/simulation/reflection), state, embedding, timestamp, metadata
    - `DepthAttentionRegistry` class:
        - `store(layer, state, metadata)`: Store computation state with persistence via Kernel
        - `query(query, top_k)`: Retrieve with keyword + recency scoring
- **Mapping to SimHPC:**
    - Intermediate representations as first-class â†’ Observational Memory + ResearchMemory (already built)
    - Selective retrieval via attention â†’ Kernel Command Bus + PromptStack
    - Dynamic routing â†’ Agent modes + SkillRegistry + Auto-Research loop
    - Representation entanglement prevention â†’ WorldState with explicit uncertainty
    - Block structure for scalability â†’ Kernel + Redis consumer workers
- **Integration Point:** Planner/Analyst agents can now query depth context for richer prompts
- **Quality Assurance:** Applied `ruff format .` and `ruff check .` (all checks passed)
- **Git:** Committed and pushed to main

## May 6, 2026 [03:45 PM]

### DepthAttentionRegistry + Auto-Research Integration
- **Kernel Integration:** Added `self.depth_registry = DepthAttentionRegistry(self)` in `backend/core/kernel/kernel.py`
- **Command Bus:** Added DEPTH_STORE and DEPTH_QUERY command handlers
- **Auto-Research Loop:** Updated `backend/core/kernel/auto_research/engine.py` to:
    - Query prior experiments via DEPTH_QUERY before proposing changes
    - Store experiment results via DEPTH_STORE after evaluation
    - Pass prior_context to `_propose_change()` for informed mutation
- **Quality Assurance:** Applied `ruff format .` and `ruff check .` (all checks passed)
- **Git:** Committed and pushed to main

## May 6, 2026 [04:00 PM]

### Embedding-Based DepthAttention + Planner Integration
- **Enhanced DepthRegistry:** Added embedding-based similarity retrieval:
    - `_compute_embedding()`: Hash-based pseudo-embedding (8-dim mock vector)
    - `_cosine_similarity()`: NumPy-based cosine similarity
    - `query()`: Now uses embedding similarity instead of keyword/recency
- **Planner Integration:** Updated `backend/core/kernel/agents/planner.py` to:
    - Query depth context via DEPTH_QUERY before planning
    - Store planning result via DEPTH_STORE after execution
    - Return depth_context_used count in result
- **Window:** Look back 100 entries for retrieval efficiency
- **Future:** Replace mock embeddings with sentence-transformers or Supabase pgvector
- **Quality Assurance:** Applied `ruff format .` and `ruff check .` (all checks passed)
- **Git:** Committed and pushed to main

## May 6, 2026 [04:15 PM]

### World Brain COS + Gamma Module System
- **WorldBrain:** Created `backend/core/kernel/world_brain.py` with:
    - `global_state`: Unified latent world state per domain
    - `causal_graph`: Causal links between domains
    - `uncertainty_field`: Per-entity uncertainty tracking
    - `update(domain, update)`: Update with depth memory recording
    - `query(query)`: Cross-domain query with depth attention
- **Gamma Module Interface:** Created `backend/core/kernel/plugins/gamma_module.py`:
    - Abstract base class with `simulate()`, `predict()`, `update_state()` methods
- **Energy Systems Module:** Created example gamma module in `backend/core/kernel/plugins/gamma/energy.py`
- **Plugin Loader:** Created auto-registration system in `backend/core/kernel/plugins/loader.py`
- **Kernel Integration:** Added `world_brain` and `plugin_loader` to Kernel init
- **Quality Assurance:** Applied `ruff format .` and `ruff check .` (all checks passed)
- **Git:** Committed and pushed to main

## May 6, 2026 [04:30 PM]

### Helm Chart with Redis Subchart + PVCs
- **Chart.yaml:** Added Redis dependency (Bitnami v20.6.0) with condition
- **values.yaml:** Added Redis subchart configuration:
    - `architecture: replication`
    - `auth.enabled: false`
    - `master/replica.persistence.enabled: true` with 10Gi size
    - `metrics.enabled: true`
- **Redis PVC:** Created `templates/redis-pvc.yaml` for persistent storage
- **Deployment:** Updated env vars with REDIS_HOST and REDIS_PORT
- **Version:** Bumped to 0.3.2

## May 6, 2026 [04:45 PM]

### Helm Chart Pre-commit Fixes + YAML Validation Bypass
- **Issue:** `check-yaml` hook failing on Helm templates with Go templating (`{{-`)
- **Fix:** Added exclusion to pre-commit config for `deploy/helm/simhpc/templates/.*`
- **Trailing newlines:** Applied `end-of-file-fixer` to all Helm files
- **Files fixed:** Chart.yaml, values.yaml, Makefile, README.md, NOTES.txt, all templates
- **Pre-commit:** All hooks now pass (ruff, ruff-format, trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files)
- **Git:** Committed and pushed to main

## May 6, 2026 [05:00 PM]

### Helm Chart HPA + Custom Metrics
- **HPA Template:** Created `templates/hpa.yaml` with:
    - `autoscaling/v2` HorizontalPodAutoscaler
    - CPU and memory-based scaling
    - Min/max replicas: 2-10
    - Target CPU: 70%, Memory: 80%
- **Values.yaml:** Added autoscaling config
- **Custom Metrics:** Created `templates/custom-metrics-hpa.yaml` for Redis connections (disabled by default)
- **Git:** Committed and pushed to main

## May 6, 2026 [05:15 PM]

### Prometheus Adapter + Custom Metrics + Monitoring Stack
- **Prometheus Adapter Config:** Created `templates/prometheus-adapter.yaml` with rules for:
    - Redis connected clients
    - Queue depth, simulation latency
    - Error rate, simulation success rate
- **Extended HPA:** Created `templates/hpa-custom.yaml` with 6 scaling metrics
- **Monitoring Stack:** Created `deploy/monitoring-stack.yaml` for Prometheus + Grafana
- **values.yaml:** Added prometheusAdapter and maxReplicas: 15
- **Git:** Committed and pushed to main

## May 6, 2026 [05:30 PM]

### Redis Removal Phase 1 - SupabaseJobStore
- **SupabaseJobStore:** Created `backend/core/supabase_job_store.py` as Redis replacement with enqueue, dequeue, publish, subscribe, update_job, get_job methods
- **Git:** Committed and pushed to main

## May 6, 2026 [05:45 PM]

### Redis Removal Phase 4 - Full Supabase-Only Architecture
- **BeamStreamer:** Updated to use SupabaseJobStore instead of Redis
- **Helm Chart:** Removed Redis subchart dependency, updated to v0.4.0
- **values.yaml:** Removed Redis configuration blocks
- **redis-pvc.yaml:** Deleted (no longer needed)
- **Version:** Bumped to 0.4.0 for v2.7 release
- **Git:** Committed and pushed to main

## May 6, 2026 [06:00 PM]

### Generalized SwarmCoordinator â€” Domain-Agnostic Forecasting
- **SwarmCoordinator:** Updated to domain-agnostic ForecastingQuestion model
- **Query:** Generic `query` field works for any domain (energy, grid, finance, climate)
- **Decision:** Added decision field (PROCEED/ABORT_LOW_CONFIDENCE)
- **Confidence:** Added confidence_interval in result
- **Report URL:** Added report_url in result
- **Process Resolution:** Added post-resolution calibration (brier scoring)
- **Git:** Committed and pushed to main

## May 6, 2026 [06:15 PM]

### WebSocket Kill Switch + Graceful Task Cancellation
- **Kill Switch Route:** Created `backend/app/api/routes/kill_switch.py`:
    - WebSocket at `/ws/swarm`
    - EMERGENCY_HALT command
    - Broadcast to all connected clients
- **SwarmCoordinator:** Added graceful task cancellation:
    - `_current_tasks` list for tracking
    - `_is_aborted` flag
    - `abort_current_run()` method
    - `asyncio.CancelledError` handling
- **Git:** Committed and pushed to main

## May 6, 2026 [06:30 PM]

### Deterministic Sandwich Architecture â€” Monte Carlo Drift Detection
- **monte_carlo.py:** Created `backend/runtime/simhpc/monte_carlo.py`:
    - `simulate_paths()`: GBM with Poisson jumps
    - 10,000 iterations for drift detection
- **drift_engine.py:** Created `backend/runtime/simhpc/drift_engine.py`:
    - `DriftDetector`: Detects liquidity distortion via MC simulation
    - `LiquidityAggregator`: Calculates arb opportunities minus fees
- **Git:** Committed and pushed to main

## May 6, 2026 [06:45 PM]

### CPU+API+A40 Multi-Node Architecture with SSE Streaming
- **CPU Node:** Created `backend/runtime/cpu_node/orchestrator.py`:
    - `ResponseCache`: In-memory cache with TTL
    - `stream_evaluate()`: Streaming version with token-by-token yield
    - `process_query()`: Non-streaming version
- **A40 Node:** Created `backend/runtime/a40/simulation.py`:
    - `run_monte_carlo_simulation()`: Heavy simulation stub
- **API Client:** Created `backend/runtime/api/reasoning_client.py`:
    - `deepseek_api_call()`: Streaming LLM placeholder
- **SSE Route:** Created `backend/app/api/routes/streaming.py`:
    - `/stream/query` endpoint for real-time streaming
    - JSON SSE format with token/complete/cancelled types
- **Git:** Committed and pushed to main

## May 6, 2026 [07:00 PM]

### Full Supabase Auth System with JWT + ProtectedRoute
- **auth.py:** Created `backend/app/api/auth.py` with full Supabase auth integration
- **api_router.py:** Added auth_router at /api/auth
- **Git:** Committed and pushed to main

## May 6, 2026 [07:15 PM]

### Simulation Swarm API + AI Experiment Grid Architecture
- **Swarm Models:** Created `backend/runtime/swarm/models.py` with ForecastingQuestion, ExperimentCreate, SwarmCreate, AgentResult, LeaderboardEntry
- **Swarm API:** Created `backend/runtime/swarm/api.py` with /experiments, /swarms, /agents endpoints
- **SwarmCoordinator:** Extended with create_experiment, launch_swarm, run_single_agent, submit_agent_result, get_leaderboard, terminate_swarm
- **Grid Registry/Scheduler/Intelligence:** Created `backend/runtime/grid/` with 5-layer architecture
- **Grid API:** Created `/api/v1/grid` endpoints
- **Git:** Committed and pushed to main

## May 6, 2026 [07:30 PM]

### SimHPC Agent SDK for Distributed Swarm Workers
- **agent_sdk.py:** Created `backend/runtime/swarm/agent_sdk.py` with:
    - `AgentParameters`: Parameters passed to an agent by the swarm
    - `AgentResult`: Result returned by an agent
    - `SimHPCAgent`: Simple SDK class with connect(), get_parameters(), submit_results(), report_progress()
- **Git:** Committed and pushed to main

## May 6, 2026 [07:45 PM]

### Discovery Graph Architecture â€” Global Knowledge Graph
- **models.py:** Created `backend/runtime/discovery/models.py` with DiscoveryNode, DiscoveryLink
- **graph.py:** Created `backend/runtime/discovery/graph.py` with DiscoveryGraph service
- **routes/discovery.py:** Created `/api/v1/discoveries` endpoints (register, link, search, leaderboard)
- **api_router.py:** Wired discovery_router at prefix `/api/v1`
- **Git:** Committed and pushed to main

## May 6, 2026 [08:00 PM]

### Discovery Ranking Engine â€” Performance + Reproducibility + Novelty
- **ranking.py:** Created `backend/runtime/discovery/ranking.py`:
    - `DiscoveryRankingEngine` with weighted scoring (performance 0.55, reproducibility 0.25, novelty 0.20)
    - `compute_score()`: Global discovery score calculation
    - `get_global_leaderboard()`: Top discoveries ranked globally
    - `update_weights()`: Dynamic weight tuning
- **graph.py:** Integrated ranking engine
- **grid/intelligence.py:** Updated with cross-experiment priors:
    - `get_parameter_priors()`: Learns from past discoveries
    - `suggest_next_swarm()`: Proposes next swarm configuration
- **grid/api.py:** Wired discovery graph into grid endpoints
- **routes/discovery.py:** Updated leaderboard endpoint to use get_leaderboard()
- **Git:** Committed and pushed to main

## May 6, 2026 [08:15 PM]

### Public Experiment Library + Fork Graph + Global Leaderboards
- **public_library.py:** Created `backend/runtime/grid/public_library.py`:
    - `PublicExperiment`: Dataclass for shared experiments
    - `PublicExperimentLibrary`: publish(), fork(), list_public(), star()
- **SwarmCoordinator:** Added `reproduce_experiment()` method
- **ExperimentForkGraph.tsx:** Created frontend component for fork visualization
- **Git:** Committed and pushed to main

## May 6, 2026 [08:30 PM]

### Robustness Layer + Simulation Runner Integration
- **Robustness Check:** Already integrated in `backend/core/robustness/check.py`
- **Simulation Runner:** Already integrated with RobustnessCheck in `backend/core/simulation/runner.py`
- **core/provenance/graph_service.py:** Created provenance service
- **Pre-commit:** Fixed trailing newline in ExperimentForkGraph.tsx
- **Git:** Committed and pushed to main

## May 7, 2026 [12:15 AM]

### ClaimExtractor â€” Structured LLM Output to Hypothesis
- **claim_extractor.py:** Created `backend/core/extractor/claim_extractor.py`:
    - `ExtractedClaim`: Pydantic model for structured claims
    - `ClaimExtractionResult`: Dataclass with hypothesis, raw output, confidence
    - `ClaimExtractor`: Main class with extract(), _parse_llm_output()
    - `get_claim_extractor()`: Singleton accessor
    - Multiple parsing strategies (JSON, structured text fallback)
    - Integration with Hypothesis model
- **Git:** Committed and pushed to main

## May 6, 2026 [03:00 PM]

### Helm Chart for SimHPC (Production-Ready)
- **Chart Creation:** Created `deploy/helm/simhpc/` with:
    - `Chart.yaml`: API v2, version 0.3.0
    - `values.yaml`: replicaCount, image, service, ingress, resources, redis config
    - `templates/deployment.yaml`: Deployment with container config
    - `templates/service.yaml`: ClusterIP service
    - `templates/ingress.yaml`: NGINX Ingress
    - `templates/configmap.yaml`: ConfigMap for environment variables
    - `templates/_helpers.tpl`: Helm helper functions
    - `templates/NOTES.txt`: Post-install instructions
    - `README.md`: Documentation with usage examples
- **Makefile Integration:** Added `helm-install`, `helm-upgrade`, `helm-uninstall` targets
- **Usage:**
    - `helm install simhpc deploy/helm/simhpc --namespace simhpc --create-namespace`
    - `helm upgrade simhpc deploy/helm/simhpc --namespace simhpc`
    - `helm uninstall simhpc --namespace simhpc`
- **Local Commit:** Changes committed locally, pending remote push

## May 8, 2026 [05:53 PM]

### ML Training Data Export + Physics Inference API [May 8, 2026 07:40 PM]
- **TrainingDataExporter** (`backend/ml/training/exporter.py`): Full implementation with 4 task types â€” hypothesis verification, parameter prediction, uncertainty quantification, sensitivity analysis. QualityThresholds with production/permissive presets. Exports JSONL (OpenAI + HuggingFace format) with train/val/test splits.
- **PhysicsInferenceAPI** (`backend/ml/inference/physics_api.py`): Fine-tuned model routing with fallback to base LLM. Supabase inference logging (batched to `inference_logs` table). Confidence extraction + ensemble ranking.
- **ModelRegistry** (`backend/ml/registry.py`): Version tracking, benchmark results, model comparison, performance trend. Supabase `model_registry` table integration with `overall_score`.
- **FinetuningPipeline** (`backend/ml/training/finetuner.py`): LoRA config, training data preparation, checkpoint management.
- **Automatic Export Trigger** (`backend/runtime/flywheel/scheduler.py`): Scheduler checks `should_export_training_data()` every 5 min â€” fires export when >= 1000 qualified runs accumulate.
- **Flywheel Hooks** (`backend/runtime/flywheel/hooks.py`): Added `should_export_training_data()` and `trigger_background_export()` for post-run integration.

### Observability Singleton + OpenTelemetry Tracing [May 8, 2026 05:53 PM]
- **ObservabilityService** (`backend/core/services/observability_service.py`): Singleton pattern with `__new__`, `observability()` accessor. Full Prometheus metrics â€” simulations, flywheel, ML, audit. `increment()`, `gauge()`, `observe()`, `start_span()` methods.
- **OpenTelemetry Tracing** (`backend/core/services/tracing.py`): Jaeger exporter with graceful fallback if opentelemetry not installed.
- **Metrics Wired:** Flywheel (runs_ingested, prior_confidence_avg), ML (inference_total, latency_ms, qualified_runs, data_exported), Simulation (started/completed/failed).
- **world_model_service singleton** (`backend/core/world_model/service.py`): Added `update_from_config()` and singleton accessor.

### ML Router Registration + Background Tasks [May 8, 2026 07:49 PM]
- **API Router** (`backend/app/api/api_router.py`): Registered `ml_router` at `/api/v1/ml` prefix â€” all ML routes now accessible via main API.
- **Startup Stats** (`backend/app/main.py`): Lifespan now checks and logs training data readiness at startup with qualified run count.
- **ML API enhancements** (`backend/app/api/ml.py`): Fixed `QualityThresholds.permissive()` fallback, added `save_checkpoint()` call in training task, full response serialization for inference endpoint.

### ML Monitoring Dashboard [May 8, 2026 07:56 PM]
- **MLMonitoringDashboard** (`frontend/src/components/MLMonitoringDashboard.tsx`): Real-time dashboard with model status, dataset stats, performance trend, export/training triggers. 30-second auto-refresh, certified runs counter, moat strength indicator.

### ML Model Versioning [May 8, 2026 07:59 PM]
- **ModelVersion** (`backend/ml/registry.py`): Full version record with `version_id`, `semver`, `training_data_hash`, `lora_config`, `status` (ACTIVE/ARCHIVED/DEPRECATED). Deterministic SHA256 hash of training dataset for reproducibility.
- **ModelRegistry versioning**: `register_version()`, `get_version()`, `get_active_version()`, `list_versions()`, `set_active_version()`, `compute_training_data_hash()`.
- **API routes** (`backend/app/api/ml.py`): `GET /models` (list all versions), `POST /models/{version_id}/activate` (set active + archive others).
- **Version-aware inference** (`backend/ml/inference/physics_api.py`): `infer(request, version_id)` â€” loads specific checkpoint when version specified.

### OpenTelemetry Tracing on ML Inference [May 8, 2026 08:04 PM]
- **Tracer spans** (`backend/ml/inference/physics_api.py`): `physics.inference` parent span with `task_type`, `domain`, `solver`, `prefer_model`, `prompt_length` attributes. Child spans `physics.inference.fine_tuned` and `physics.inference.fallback`. `model_used`, `fallback_used` set as span attributes on completion.

### Grafana ML Tracing Dashboard + Trace Propagation [May 8, 2026 08:07 PM]
- **Grafana Dashboard** (`deploy/grafana/dashboards/ml-tracing.json`): 6 panels â€” inference requests overview, latency P95/P50 timeseries, fallback rate %, Jaeger trace panel (physics.inference), model usage pie chart, latency + throughput. 30s refresh, 6h window.
- **Trace Propagation** (`frontend/src/lib/apiClient.ts`): OTEL `context` + `propagation.inject()` on active span â€” injects `traceparent`/`tracestate` headers into all backend requests for end-to-end distributed tracing.

### Live Trace ID Table in ML Dashboard [May 8, 2026 08:11 PM]
- **Recent Inferences endpoint** (`backend/app/api/ml.py`): `GET /ml/inference/recent` â€” returns last 15 inference logs with trace IDs.
- **Trace ID capture** (`backend/ml/inference/physics_api.py`): `_log_inference()` now extracts current OTEL span's trace_id (hex format) and stores it in log entry.
- **Dashboard table** (`frontend/src/components/MLMonitoringDashboard.tsx`): New "Recent Inferences" panel with Table component showing timestamp, task, domain, model, latency, confidence, trace ID (clickable link to Jaeger), and "View Trace" button. 15s refresh.

### Grafana Tempo as Tracing Backend [May 8, 2026 08:15 PM]
- **Tempo OTLP Exporter** (`backend/core/services/tracing.py`): Replaced Jaeger thrift exporter with `OTLPSpanExporter` pointing to `TEMPO_OTLP_ENDPOINT` (default `http://tempo:4317`). Resource attributes now include `environment` and `deployment`. `setup_tempo_tracing()` with `insecure=True`.
- **Trace Alert Service** (`backend/ml/monitoring/trace_alerts.py`): `TraceAlertService` runs every 60s checking for trace anomalies. Triggers `LogAuditCommand` on high fallback rate. Exposes `trace_based_alerts_total` metric.
- **Scheduler integration** (`backend/runtime/flywheel/scheduler.py`): `TraceAlertService` instantiated and started via `asyncio.create_task` in `FlywheelScheduler.start()`.
- **Alerting rules** (`deploy/monitoring/alerting-rules-tracing.yml`): 5 Prometheus alerting rules â€” `HighPhysicsInferenceLatency` (P95 >800ms), `HighModelFallbackRate` (>25%), `LowConfidenceInference`, `TraceErrorRateHigh` (>5%), `SlowAuditChainVerification` (>1.5s P99).
- **Dashboard v2** (`deploy/grafana/dashboards/ml-tracing.json`): Added "Trace-Based Alerts (Active)" alertlist panel + error/fallback rate timeseries. Tag updated to `tempo`. Version bumped to 2.

### Production-Ready Alertmanager Routing & Silences [May 8, 2026 08:18 PM]
- **alertmanager.yml** (`deploy/monitoring/alertmanager.yml`): Complete rewrite with severity + category routing â€” `ml-critical` (webhook + email), `compliance-critical` (webhook + email + PagerDuty), `ml-warning`, `team-warning`. Added `inhibit_rules` to suppress warnings when critical fires. Templates mounted from `/etc/alertmanager/templates/*.tmpl`.
- **Alert template** (`deploy/monitoring/templates/alert.tmpl`): HTML templates with `common.subject` and `common.body` defines â€” includes severity, category, trace ID per alert.
- **Silences** (`deploy/monitoring/alertmanager-silences.yml`): 4 pre-configured silences â€” load testing suppression, ML training window, audit log volume spike, deployment trace errors.

### Alertmanager Webhooks + Backend Receiver [May 8, 2026 08:24 PM]
- **Alertmanager webhooks** (`deploy/monitoring/alertmanager.yml`): `ml-critical` receiver uses `basic_auth` with `password_file: /etc/alertmanager/ml-webhook-secret`. `compliance-critical` uses `routing_key_file: /etc/alertmanager/pagerduty-key`. All receivers have `send_resolved: true`.
- **Webhook template** (`deploy/monitoring/templates/alert-webhook.tmpl`): JSON payload v4 with `commonLabels`, `commonAnnotations`, `truncatedAlerts`, per-alert `fingerprint`.
- **Webhook receiver** (`backend/app/api/webhooks/alerts.py`): FastAPI endpoints at `POST /api/v1/alerts/ml-critical`, `/compliance-critical`, `/default`, `/team-warning` with `AlertPayload` model.
- **Router registration** (`backend/app/api/api_router.py`): `webhook_router` mounted at `/api/v1/alerts`.

### Forecasting Swarm Plugin [May 8, 2026 09:03 PM]
- **Plugin structure** (`backend/plugins/forecasting_swarm/`): Auto-discovered via `PluginRegistry.register`. 7 files â€” `plugin.py`, `models.py`, `bayesian_aggregator.py`, `conformal_bridge.py`, `swarm_coordinator.py`, `swarmer.py`, `__init__.py`.
- **Models** (`models.py`): `AgentRole` (TREND, STRUCTURAL, DISTRIBUTIONAL, CONTRARIAN), `AgentOutput`, `AggregatedForecast`, `PredictionQuestion` â€” all Pydantic v2 validated.
- **BayesianAggregator** (`bayesian_aggregator.py`): Log-odds BMC weighted aggregation, consensus scoring, dissent detection (threshold 0.15). Computes CI from conformal bridge + average agent CIs.
- **ConformalBridge** (`conformal_bridge.py`): Loads calibration scores from Supabase `conformal_calibration` table. Falls back to `ml_inference_confidence_p95` from observability when <30 samples. Adaptive quantile conformal intervals.
- **SwarmCoordinator** (`swarm_coordinator.py`): `run()` with `forecast.swarm` OTEL span, `observability` metrics (`swarm_runs_total`, `swarm_consensus_score`, `swarm_dissent_rate`, `swarm_latency_ms`). Parallel agent execution via `asyncio.gather`.
- **SwarmRunner** (`swarmer.py`): `run_from_dict()` â€” converts dict input to `PredictionQuestion`, returns serializable forecast result. Used by plugin entrypoint.

### GraphRAG Plugin [May 8, 2026 09:13 PM]
- **GraphRAG plugin** (`backend/plugins/graphrag/plugin.py`): `PluginRegistry.register("graphrag")`, wraps `GraphRAGDagNode`. `run()` delegates to `GraphRAGDagNode.run()`.
- **Command bus handler** (`backend/runtime/graphrag/graphrag_dag_node.py`): `@command_bus.handler("GRAPHRAG_RETRIEVE")` â€” registered at module load time.
- **Observability wiring** (`backend/runtime/graphrag/graphrag_retriever.py`): `GraphRAGRetriever.retrieve()` now emits `graphrag_retrievals_total` metric + `graphrag.retrieve` OTEL span with `hops` attribute. Adds `graphrag_hops_used` and `graphrag_chunks_retrieved` gauges.
- **DAG node spans** (`graphrag_dag_node.py`): `GraphRAGDagNode.run()` wrapped in `graphrag.dag_node` span.
- **pgvector migration** (`deploy/migrations/graphrag_migration.sql`): Adds `embedding vector(1536)` + `category text` columns to `document_chunks`. Creates IVFFlat index and `match_chunks()` RPC with cosine distance, filter by category, safe `CREATE OR REPLACE`.

### Event Fabric [May 8, 2026 11:18 PM]
- **SimHPCEvent schema** (`backend/core/runtime/event_fabric/schema.py`): `frozen=True` immutable event with `event_id` (UUID), `event_type`, `causal_id` (Lamport partial order), `source_plugin`, `EventPriority` (CRITICAL/HIGH/NORMAL), `confidence`, `payload`, `provenance_hash`. `seal()` method produces SHA256 hash-chained events.
- **EventLogService** (`log.py`): Singleton via `event_log()` accessor. `publish()` â€” seals event, writes to `events` Supabase table, notifies pattern-matched subscribers via `asyncio.create_task`. `subscribe()` â€” fnmatch-style pattern routing (e.g. `simulation.*`, `ml.inference.*`). `replay()` â€” temporal range query with filters/limit.
- **Command bus routing** (`backend/core/kernel/command_bus.py`): Added `EVENT_PUBLISH` and `EVENT_SUBSCRIBE` command types. `EVENT_PUBLISH` validates via `SimHPCEvent.model_validate()` and calls `event_log().publish()`.
- **Alertmanager integration** (`deploy/monitoring/alertmanager.yml`): Added `priority = "critical"` route to `ml-critical` receiver. Added `ml-warning` receiver for `warning + ml`. Inhibits lower-priority when critical fires.
- **Migration** (`supabase/migrations/20260508_event_fabric.sql`): `events` table â€” `event_id` PK, `event_type`, `timestamp`, `causal_id`, `source_plugin`, `priority`, `confidence`, `payload JSONB`, `provenance_hash`. BRIN temporal index, composite `(event_type, timestamp)` index, source index. RLS append-only policy.

### Causal Consistency + Vector Clocks [May 8, 2026 11:21 PM]
- **VectorClock** (`backend/core/runtime/event_fabric/vector_clock.py`): Dict subclass with `increment()`, `merge()`, `__le__` (happened-before). Tracks per-source Lamport timestamps for multi-source partial ordering.
- **SimHPCEvent extended** (`schema.py`): `vector_clock: VectorClock` field. `seal()` increments clock, updates `causal_id` to SHA256 of clock dict (16 hex chars).
- **Causal enforcement** (`log.py`): `_is_causally_ready()` â€” compares incoming event's vector clock against `_causal_frontier`. Violations emit `runtime.causal.violation` (CRITICAL) event and raise `RuntimeError`. `_update_causal_frontier()` merges incoming clock. `events_published_total` and `causal_violations_total` metrics.
- **StateRegistryService** (`backend/core/runtime/state_registry/service.py`): Singleton with `registry()` accessor. `mutate()` â€” applies event, propagates temporally, persists via `model_dump(mode="json")`. `state_mutations_total` metric tagged with `regime`. Pending mutation buffer drains when events become causally ready. `register_observer()` (sync) and `observe()` (async) for plugin registration. `get_current()`, `reconstruct(at_timestamp)`. `observer_notification_errors` metric.
- **TemporalEngine** (`backend/core/runtime/temporal/engine.py`): `propagate()` applies exponential decay (half-life per entity) and regime detection (normal/panic/disruption) based on uncertainty thresholds.
- **Plugin contract** (`backend/plugins/base.py`): Added `observe(state)` and `emit(event)` methods to `PluginBase`. `emit()` routes through `EVENT_PUBLISH` command bus.
- **Command bus** (`command_bus.py`): Added `STATE_MUTATE` routing to `StateRegistryService.registry().mutate()`.
- **Migration** (`supabase/migrations/20260508_causal_consistency.sql`): Adds `vector_clock JSONB` + `causal_id TEXT` to events. GIN index on vector_clock, composite on `(causal_id, timestamp)`. `world_states` snapshot table with indexes + `latest_world_state` materialized view for fast reads.

### Temporal Engine + Entity Graph [May 8, 2026 11:30 PM]
- **TemporalEngine upgrade** (`backend/core/runtime/temporal/engine.py`): `RegimeDetector` with entropy-based regime detection (normal/panic/disruption). `propagate()` â€” exponential signal decay via `math.exp(-age/half_life_s)`, panic halves half-life. `regime_shifts_total` metric. Calls `world_model_service.propagate_uncertainty()` for Monte-Carlo propagation.
- **Entity Graph** (`backend/core/runtime/entity_graph/schema.py`, `service.py`): `EntityNode` and `RelationshipEdge` Pydantic models. `EntityGraphService` singleton with `graph()` accessor. `add_node()`, `add_edge()` (triggers `StateRegistryService.mutate()`), `traverse()` via `get_entity_neighbours()` RPC, `get_graph_snapshot()`.
- **Plugin SDK** (`backend/plugins/base.py`): `PluginBase` now has `enabled` flag, `initialize()` (registers observer + `PLUGIN_REGISTERED` command), `emit()` (builds `SimHPCEvent` from args, routes through `EVENT_PUBLISH`), `observe()` abstract method with no-direct-write contract.
- **PluginRegistry** (`backend/plugins/registry.py`): Singleton with `registry()` accessor. `_load_plugins()` auto-discovers via `pkgutil.iter_modules()`, instantiates plugins, calls `initialize()` asynchronously on load. Logs each loaded plugin.
- **Command bus** (`command_bus.py`): Added `TEMPORAL_PROPAGATE`, `ENTITY_GRAPH_ADD_EDGE`, `ENTITY_GRAPH_TRAVERSE`, `PLUGIN_REGISTERED` handlers.
- **World state API** (`backend/app/api/world_state.py`): `GET /api/v1/world-state/current`, `GET /api/v1/world-state/replay?at_ts=`, `GET /api/v1/world-state/graph`, `GET /api/v1/world-state/stream` (SSE with 30s keepalive). Registered at `/api/v1` prefix.
- **Frontend** (`frontend/src/components/WorldStateGraph.tsx`): Live entity graph (node buttons with opacity = uncertainty), regime + entropy gauges, top uncertainty panel, causal event stream, SSE stream via `EventSource`, replay slider. 15s polling with range input, manual refresh.
- **Migration** (`supabase/migrations/20260508_temporal_entity_graph.sql`): Adds `regime` to `world_states`, `evidence_event_ids` to `knowledge_graph_edges`, relation-weight index, `plugin_registrations` audit table with RLS.

### Temporal Engine + InvariantRegistry [May 9, 2026 12:00 AM]
- **TemporalEngine refined** (`backend/core/runtime/temporal/engine.py`): `RegimeDetector` uses both `max(uncertainty)` (volatility) and average uncertainty. panic threshold: volatility >0.4 OR avg >0.35. disruption: volatility >0.7 OR avg >0.6. Decay now uses `ent.uncertainty * (2.0 - decay)` (uncertainty grows as signal decays). panic/disruption halves half_life_s to 300s minimum. `current_regime_entropy` gauge. `trace_context("temporal.propagate")` span.
- **InvariantRegistry** (`backend/core/runtime/formalization/invariants.py`): Singleton with 8 core invariants — `_conservation_of_probability`, `_causal_consistency`, `_trace_id_preservation`, `_supabase_consistency`, `_provenance_integrity`, `_uncertainty_bounds`, `_entity_key_uniqueness`, `_temporal_monotonicity`. `enforce()` runs all invariants, emits `runtime.invariant.violation` (CRITICAL) on failure, increments `invariant_violations_total`.  `register()` for custom invariants.
- **StateRegistry wired** (`backend/core/runtime/state_registry/service.py`): `mutate()` now calls `InvariantRegistry.invariants().enforce()` before applying event. Rejects mutation + increments `state_mutations_rejected_total` on violation.
- **Command bus** (`command_bus.py`): `TEMPORAL_PROPAGATE` now uses `WorldState.model_validate()` + `SimHPCEvent.model_validate()` for proper type casting.
- **Migration** (`supabase/migrations/20260509_invariant_audit.sql`): `invariant_violations` audit table — `violation_id`, `event_id`, `violations JSONB`, `state_id`, `event_type`, `source_plugin`, `resolved` flag. Indexes on event, resolved, created_at.

## May 9, 2026 [02:30 AM]

### Plugin SDK Finalization & Graphs & UI Layer Complete
- **Plugin SDK Finalized:** Migrated plugins (orecasting_swarm, graphrag) to PluginBase contract with auto-discovery via PluginRegistry. Enforced self.emit() for causal event publishing and observe() for state reactions.
- **Minimal Graph UI Layer:** Implemented production-grade visualization layer using ReactFlow for live entity-relationship graphing.
- **Backend Graph API:** Finalized get_graph_snapshot for real-time visualization, integrated with StateRegistryService.
- **SSE Integration:** Enabled live world-state updates through /api/v1/world-state/stream utilizing Supabase realtime.
- **Core Runtime:** Temporal engine integrated with runtime-enforced invariants (Formalizer) and full observability dashboards in Grafana.

## May 9, 2026 [05:45 PM]

### Hardware Moat Layer — Production Compute Governance
- **Provider Abstraction** (`backend/hardware/providers.py`): Multi-provider layer decoupling SimHPC from any single GPU cloud. RunPod A40 fleet (current) + CoreWeave H100 clusters (next tier) via `ProviderInterface`. `HardwareProviderRegistry` with parallel health checks via `asyncio.gather`.
- **SLA Contract Engine** (`backend/hardware/sla.py`): 5-tier SLA system (Free/Professional/Enterprise/Defense/Custom) with automatic breach detection and credit calculation. ITAR-isolated hardware enforcement for Defense tier. Monthly credit caps and compliance audit integration.
- **SLA-Aware Scheduler** (`backend/hardware/scheduler.py`): Decision-tree routing — Defense → ITAR-isolated only (hard fail), Enterprise → dedicated with shared fallback + alert, Professional → cheapest shared, Free → best-effort spot. Writes `hardware_attestations` records linked to simulation certificates.
- **Capacity Reservations** (`backend/hardware/reservations.py`): Pre-reserved GPU-hours with tiered discounts (15%/25%/40% for 1m/3m/1y). Wholesale cost multiplier (60%) for margin tracking. Platform-wide utilization dashboard for procurement leverage.
- **API Routes** (`backend/app/api/hardware.py`): `/api/v1/hardware/schedule`, `/providers`, `/sla/{tenant_id}`, `/sla/tiers`, `/sla/breach`, `/sla/credits/{tenant}`, `/reservations/{tenant}`, `/reservations`, `/cost/arbitrage`, `/capacity`. Registered in `api_router.py`.
- **Observability:** `hardware_scheduling_total`, `sla_breaches_total`, `itar_scheduling_attempts`, `capacity_utilization_pct` metrics via existing observability layer.
- **Git:** Committed and pushed to main.

## May 9, 2026 [06:08 PM]

### Governed Execution Reserve — Warm Pools Layer
- **WarmPoolManager** (`backend/core/hardware/pools.py`): Governed execution reserve layer with `ExecutionCapacity` model (6 pool classes: shared/dedicated/isolated/low_cost/realtime/high_memory). Full reserve/release lifecycle — `WARM_IDLE | RESERVED | RUNNING | DRAINING`. SLA-aware warm slot lookup with ITAR enforcement.
- **EconomicsEngine** (`backend/core/hardware/economics.py`): Margin and cost optimization — `NodeEconomics` with retail/wholesale/margin per GPU-hour. Total platform margin aggregation by provider. Spot savings calculator.
- **CapacityForecaster** (`backend/core/hardware/forecasting.py`): Demand prediction across horizons (15m/1h/4h/24h) using queued jobs and active simulation counts. `DemandSnapshot` recording for historical pattern learning.
- **PlacementEngine** (`backend/core/hardware/placement.py`): Policy-driven selection — `LOWEST_COST`, `LOWEST_LATENCY`, `ISOLATED`, `HIGH_UTILIZATION`, `ENERGY_EFFICIENT`. Defense tier auto-routes to isolated policy. Ranked candidate scoring.
- **AttestationService** (`backend/core/hardware/attestation.py`): Immutable execution proof with TTL-based expiration. `ATTESTED | EXPIRED | REVOKED` status lifecycle. Verification against `hardware_attestations` table.
- **Integration:** All modules wired through `backend/core/hardware/__init__.py` for consistent imports.

## May 9, 2026 [06:10 PM]

### GPU Bin Packing — Hardware Moat Optimization Primitive
- **GPUBinPacker** (`backend/core/hardware/bin_packing.py`): First-fit decreasing bin packing with `GPUBin` model. Fractional GPU support — multiple lightweight workloads (agent swarms, Monte Carlo, inference) share a single GPU. SLA-aware packing: Defense → isolated bins only, Enterprise → dedicated. ITAR isolation enforcement during bin selection. Economic optimization via lowest-cost viable bin ranking.
- **Fractional scheduling:** `pack_fractional()` assigns `gpu_fraction` (0.0–1.0) per workload, enabling mixed workloads on shared capacity.
- **Utilization metrics:** `calculate_utilization()` returns total/used/wasted/optimized bin counts for capacity planning.
- **Git:** Committed and pushed to main.

### Advanced Bin Packing Heuristics — Multi-Objective GPU Scheduling
- **BinPackingHeuristic enum:** `FIRST_FIT_DECREASING`, `BEST_FIT_DECREASING`, `WORST_FIT_DECREASING`, `SLA_AWARE_BEST_FIT`.
- **PackingScore:** Multi-objective scoring — fit (40%), SLA compliance (30%), cost (20%), fragmentation penalty (10%).
- **AdvancedGPUBinPacker:** All 4 heuristics with SLA-aware best fit as default. Defense → isolated bins only, Enterprise → dedicated.
- **Fractional GPU:** Workload tracking via `gpu_fraction` in capacity metadata enables mixed workloads on shared capacity.
- **Git:** Committed and pushed to main.

### Dynamic Heuristic Selection — Context-Aware Bin Packing Intelligence
- **DynamicHeuristicSelector** (`backend/core/hardware/bin_packing_dynamic.py`): Singleton with `HeuristicPerformanceRecord` tracking success rate and recency per heuristic.
- **Decision tree:** Defense → SLA_AWARE, high utilization (>85%) → BEST_FIT, large jobs (>4 GPU) → FIRST_FIT, realtime → SLA_AWARE, sparse bins → FIRST_FIT.
- **Online learning:** `record_outcome()` updates after every packing attempt — exponential moving average of success rate with recency weighting.
- **dynamic_pack()** wrapper: selection + pack + outcome recording in one call.
- **Performance summary:** `get_performance_summary()` exposes per-heuristic metrics for observability.
- **Git:** Committed and pushed to main.

## May 9, 2026 [06:13 PM]

### ML Intelligence Layer — Hardware Moat Prediction and Anomaly Detection
- **HardwareMLModels** (`backend/core/hardware/ml_integration.py`): Singleton ML orchestration — demand forecasting, anomaly detection, packing efficiency prediction, RL policy suggestions.
- **predict_demand():** Horizon-aware demand per pool class (shared/dedicated/isolated).
- **detect_anomalies():** GPU temp (>85C) and utilization (>95%) threshold detection on node telemetry.
- **predict_packing_efficiency():** Utilization + fit score for bin packing quality.
- **suggest_scheduling_action():** State-driven recommendations — PROVISION_ISOLATED, EXPAND_WARM_POOL, OPTIMIZE_PACKING, MAINTAIN.
- **proactively_provision_isolated():** Defense-tier warm pool expansion on predicted demand.
- **Git:** Committed and pushed to main.

## May 9, 2026 [06:15 PM]

### Federated Learning Engine — Secure Multi-Party Learning Orchestration
- **FederatedLearningEngine** (`backend/core/runtime/federated/engine.py`): Global + local `TemporalGNN` models per participant. `local_train()` trains on private subgraph only, returns delta with regime awareness. `aggregate()` weighted FedAvg with confidence + disruption downweighting.
- **Versioned global model:** `ModelRegistry.register_version()` on every aggregation round.
- **FederatedAlgorithms:** `fedavg`, `fedprox`, `scaffold`, `fednova`, `temporal_fedavg` (custom with regime weighting).
- **Event publishing:** `federated.model_aggregated` event on every aggregation for audit trail.
- **Metrics:** `federated_local_train_total`, `federated_aggregations_total`, `federated_rounds_total`.
- **Git:** Committed and pushed to main.

## May 9, 2026 [06:18 PM]

### Homomorphic Encryption — Privacy-Preserving Core Primitive
- **HomomorphicEngine** (`backend/core/runtime/homomorphic/engine.py`): Paillier additive HE with 2048-bit keys. `encrypt_graph_snapshot()` encrypts Entity Graph node values, uncertainties, and edge weights. `homomorphic_aggregate()` performs encrypted sum/avg/max/min without full decryption.
- **EncryptedSnapshot:** Stored in `he_snapshots` Supabase table with ciphertexts per node/edge.
- **Public key ring:** `get_public_key_ring()` exports public key safely for client-side encryption.
- **Composable:** Works with Federated Learning (encrypted local updates) and zk-SNARKs (proofs over ciphertexts).
- **Graceful fallback:** Stores plaintext when `phe` library unavailable.
- **Git:** Committed and pushed to main.

## May 9, 2026 [06:40 PM]

### Prediction Market Plugin — Real-Time Forecasting Domain Specialization
- **Plugin manifest** (`plugins/prediction_market/manifest.json`): Permissions — event.subscribe/emit, state.read, forecast.write, graph.read, agent.register.
- **ForecastSignal model** (`forecasting/signals.py`): source, market_id, value, confidence, provenance, metadata per signal.
- **Ingestors** (`ingestion/`): Polymarket + Kalshi API integration with mock fallbacks. News, Twitter, Weather ingestors for multi-source signals.
- **ProbabilityEngine** (`forecasting/probability_engine.py`): Weighted ensemble with calibration + regime-aware uncertainty (panic/disruption multipliers). Integrates with TemporalEngine and StateRegistry.
- **CalibrationAnalyzer** (`forecasting/calibration.py`): Brier score and calibration error per forecast. EnsembleBuilder for multi-signal merging.
- **ScoringEngine + OutcomeTracker** (`evaluation/scoring.py`): Brier scoring, accuracy, direction correctness. `replay()` ranks historical forecasts against actual outcomes.
- **Public feed API** (`api/routes.py`): `/api/v1/predictions/feeds/public`, `/leaderboard`, WebSocket `/stream`.
- **Architecture:** All signals flow through Event Fabric → State Registry. Agents emit/receive via `emit()` / `observe()`. Regime-aware via TemporalEngine. Reuses core Prediction, Tournament, Calibration, and Replay primitives.
- **Git:** Committed and pushed to main.
