# SimHPC Changelog

> All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-03-25

### Added
- **RunPod API Client (`runpod_api.py`)**: Production-grade pod lifecycle management module with full GraphQL API integration.
  - `list_pods()` — Fleet-wide status with GPU utilization and cost estimates.
  - `create_pod()` — Programmatic pod creation with MAX_PODS safety cap.
  - `start_pod()` / `stop_pod()` — Resume/pause pods to control GPU billing.
  - `terminate_pod()` — Permanent pod destruction for idle shutdown.
  - `get_fleet_status()` — Aggregated fleet, queue, cost, and scaling state.
  - `get_cost_summary()` — Daily/weekly burn estimates with autoscaler savings %.
  - `health_check()` — RunPod API key validation and account status.
- **Production Autoscaler v2.2.0**: Cost-aware, queue-driven scaling engine.
  - Daily cost budgets: `DAILY_COST_WARN_USD` (warning) and `DAILY_COST_HARD_CAP_USD` (blocks scale-up).
  - Per-interval cost accumulation tracked in Redis (`cost:today_usd`).
  - Periodic fleet status snapshots stored in Redis (`autoscaler:last_status`).
  - Structured event logging to Redis (`runpod_events` list, last 500 entries).
  - Startup health check verifying RunPod API connectivity.
- **Admin Fleet Management Endpoints** (6 new routes in `api.py`):
  - `GET /api/v1/admin/fleet` — Fleet status dashboard data.
  - `GET /api/v1/admin/fleet/cost` — Cost tracking summary.
  - `GET /api/v1/admin/fleet/events` — Recent scaling/cost events.
  - `POST /api/v1/admin/fleet/pod` — Create pod (safety-capped).
  - `POST /api/v1/admin/fleet/pod/{id}/stop` — Stop pod.
  - `POST /api/v1/admin/fleet/pod/{id}/terminate` — Terminate pod.
  - All endpoints protected by `X-Admin-Secret` header.

### Changed
- **Autoscaler Dockerfile**: Updated to include `runpod_api.py` module and build from root context.
- **docker-compose.yml**: Autoscaler service now receives 10 additional env vars for fleet config and cost caps.
- **`.env.schema`**: Added all RunPod fleet management and autoscaler v2.2.0 environment variables.
- **`.env.example`**: Added RunPod API key, fleet config, and cost cap variables.

### Cost Impact
- **Without autoscaler**: $10–$25/day idle GPU burn.
- **With v2.2.0 autoscaler**: $1–$5/day (alpha usage) with daily hard cap enforcement.

## [1.6.2] - 2026-03-21

### Changed
- **Multi-Pod Autoscaler**: Replaced single-pod autoscaler with queue-depth-based scaling. Pods scale as `ceil(queue / JOBS_PER_POD)` capped at `MAX_PODS=3`, one at a time with 30s cooldown.
- **Redis-Persisted Pod State**: Active pod list stored in Redis (`active_pods` key) so autoscaler survives restarts without orphaning pods.
- **RunPod API Sync**: Every cycle queries RunPod for live pods, reconciles against stored state, and cleans up dead/orphaned entries.
- **Full Idle Shutdown**: Terminates ALL pods after 5 min idle → guaranteed $0 when not busy.
- **Docker Image Sizes**: Multi-stage builds across all Dockerfiles. Worker uses `cuda:runtime` (not `devel`) with aggressive trim (no pip, no __pycache__) → ~1GB final. API uses `python:3.11-slim` builder → ~200MB final.
- **API Workers**: Reduced gunicorn workers from 4 → 2 to save memory on small instances.
- **`.dockerignore` hardening**: Added `data/`, `datasets/`, `checkpoints/`, `wheelhouse/`, `.cache/` to prevent accidental multi-GB copies.

### Fixed
- **Runaway Cost**: Old autoscaler could leave pods running indefinitely. New version enforces `MAX_PODS` cap both in code and against the RunPod API.
- **`COPY . .` removed**: Robustness-orchestrator Dockerfiles replaced blanket copy with explicit file list.
- **Worker `REDIS_URL` default**: Removed `localhost` fallback — worker now fails fast if `REDIS_URL` is not set (prevents silent misconnection on RunPod).
- **Worker heartbeat during idle**: `send_heartbeat()` now fires in both job-active and idle loops so dashboard always shows worker as alive.
- **Debug script**: Added `debug.py` for quick Redis + Supabase connectivity check inside worker container.

## [1.6.1] - 2026-03-18

### Fixed
- **Toast Notification System**: `<Toaster />` component from sonner was never mounted — all 12 `toast()` calls were silently doing nothing. Created `App.tsx` with `<Toaster />` configured for 6s duration, 320px min-width, cyan glow theme.
- **Toast Loading→Success Pattern**: Updated `Dashboard.tsx`, `OperatorConsole.tsx`, and `AlphaControlRoom.tsx` to use `toast.loading()` → `toast.success/error()` with the same toast ID, preventing message flashing during GPU queue operations.
- **Toast CSS Overrides**: Added `[data-sonner-toast]` styles in `index.css` for readability on high-res dashboards (1.1rem font, 320px min-width, dark border/shadow).
- **Missing Entry Files**: Created `main.tsx`, `App.tsx`, `index.html`, `index.css`, and `vite.config.ts` that were deleted during monorepo restructure.
- **Third-Party Cookie Blocks**: Added custom domain strategy (app + auth subdomains) to make Supabase Auth first-party.

### Added
- **Toast Visibility**: 6-second default, 8-second success, 10-second error duration for physics simulation status messages.
- **Toast Styling**: Cyan glow theme (`#00f2ff`), `iconTheme` for success/error, rounded corners, dark terminal aesthetic.
- **Toast Promise Pattern**: `toast.promise()` for simulation submission — loading/success/error linked to API lifecycle.
- **Supabase Realtime Hook**: `useSimulationUpdates` subscribes to `simulation_history` table — completion triggers 10s celebration toast.
- **Simulation History Table**: Real-time dashboard table with status badges (Queued/Processing/Completed/Failed), clickable rows, and download links.
- **Simulation Detail Modal**: Click any simulation row to view AI-generated insights, physics metrics JSON, and PDF download.
- **Admin Analytics Dashboard**: Route at `/admin/analytics` with Active GPU Pods, Total Simulations, and Lead qualification tracking (Hot/Warm/New).
- **Worker Status Sync**: `update_job_status()` method in `worker.py` syncs job status to `simulation_history` table in Supabase.
- **Supabase Migration**: `heartbeat_history.sql` creates `worker_heartbeat`, `simulation_history`, and `leads` tables with Realtime enabled.
- **CORS Hardening**: Changed `api.py` CORS from `["*"]` to explicit allow-list including custom domain.

## [1.6.0] - 2026-03-16

### Added
- **Mission Control Cockpit v1.6.0**: Complete modular redesign of the operational interface for aerospace/thermal engineers.
- **Component Modularization**: Split the dashboard into independent, high-performance components:
  - `TelemetryPanel.tsx`: 3-channel real-time sparklines (GPU/Convergence/Error).
  - `ActiveSimulations.tsx`: "Decision Panel" with live solver health status (optimal/stiff/diverging).
  - `SimulationLineage.tsx`: ITERATION-tree view for design ancestry and "Flux Delta" tracking.
  - `OperatorConsole.tsx`: High-stakes intervention tools ([INTERCEPT], [CLONE], [BOOST], [CERTIFY]).
  - `GuidanceEngine.tsx`: AI-navigator providing corrective strategy recommendations.
- **Unified Cockpit Aesthetic**: Dark-terminal theme with Mission Control Cyan accents and tabular-numeric UTC synchronization.
### Fixed
- **Unused Declarations**: Removed unused `ShieldAlert` icon import in `ActiveSimulations.tsx` and cleaned up unused `variant` prop in the inline `ThemeToggle` component within `ExperimentNotebook.tsx`.
- **Documentation Consolidation**: Consolidated frontend and root architecture documentation into a single source of truth at `ARCHITECTURE.md`.
- **Naming Consistency**: Standardized all references to `robustness-orchestrator` across the codebase and documentation to eliminate underscore/hyphen oscillation.
- **Project Structure & Hygiene**: Reorganized the monorepo for production readiness:
  - Moved low-level setup logs into `docs/internal/`.
  - Relocated root mockups to `docs/assets/mockups/`.
  - Purged redundant zip archives (`SimHPC_Alpha_*`) and legacy `zip_source.ps1`.
  - Deleted deprecated `archive/` directory to improve build focus.

## [1.5.1] - 2026-03-10

### Added
- **Trust Layer APIs (100% Complete)**: Finalized transparency services including Provenance API (hardware/solver metadata) and Uncertainty API (variance/confidence intervals).
- **Demo Flow APIs (100% Complete)**: Finalized guided onboarding with 5-step progress tracking, suggested next-run logic, and automated report/notebook generation.
- **Control Room UI APIs (100% Complete)**: Finalized operator panels with 50-run persistent memory, rule-based insight engine, alert aggregation (1h TTL), and single-request dashboard hydration.
- **Core System APIs (100% Complete)**: Finalized missing infrastructure including the Simulation Runtime Estimator (`runtime ≈ E * S * P`) and Timeline/Replay auditing system.

- **Alpha Control Room Redesign**: Complete rebuild of `/dashboard/alpha` with HPC trading terminal aesthetic.
  - **Live Signals Panel**: Real-time temperature, grid load, energy price, and solar output with SVG sparkline history graphs.
  - **Active Simulations Panel**: Live simulation registry with animated status badges (`running`, `completed`, `queued`, `failed`).
  - **Simulation Memory Panel**: Past simulation runs archive with status and timestamp display.
  - **Simulation Insights Feed**: Auto-scrolling AI observation log with confidence bars, icons, and suggested actions.
  - **Notebook/Analysis Panel**: Compact launch bar for Jupyter integration and data export.
  - **System Status Footer**: Live status indicators for GPU cluster, SUNDIALS solver, Mercury AI, and Supabase.
  - **UTC Clock**: Live UTC time display in header.
  - **Signal Sparklines**: Rolling 20-point SVG micro-charts for each signal.

---

### Added

- **Alpha RunPod Container Architecture**: New unified worker container for high-performance LLM and RAG services.
  - **vLLM Inference**: Integrated vLLM engine for ultra-fast Mistral/Llama inference (~90 tok/s).
  - **RAG Service**: FAISS-based vector store for engineering context retrieval from documentation.
  - **FastAPI Layer**: Dedicated API for Alpha chat and document management inside the worker.
  - **pod SimHPC_P_01 id x613fv0zoyvtx9 Integration**: Full async lifecycle management for Alpha chat requests in the main orchestrator.
- **Backend RunPod Client**: New `RunPodClient` in `api.py` for managing pod SimHPC_P_01 id x613fv0zoyvtx9 jobs, status polling, and result retrieval.
- **Alpha Chat Endpoint**: `POST /api/v1/alpha/chat` for secure engineering assistant interactions.

---

## [1.4.0] - 2026-03-10


### Added
- **Magic Link Demo Tokens**: Complete alpha pilot onboarding system with secure, usage-limited demo links.
  - `POST /api/v1/demo/magic-link` — Validate demo token and create session
  - `GET /api/v1/demo/usage` — Check remaining simulation runs
  - `POST /api/v1/demo/use-run` — Decrement usage counter per simulation
  - `POST /api/v1/demo/create` — Admin endpoint to generate new magic links
- **Supabase `demo_access` Table**: Persistent storage with SHA-256 hashed tokens, usage limits, expiration, and IP logging.
- **Frontend Demo Landing Page (`DemoAccess.tsx`)**: Animated magic link validation with status feedback (validating → success → redirect).
- **Dashboard Demo Banner (`DemoBanner.tsx`)**: Live usage counter with progress bar, color-coded warnings, and upgrade CTAs.
- **CLI Tool (`generate_demo_link.py`)**: Standalone script for generating demo links via API or direct Redis/Supabase mode.
- **Demo Tier (`demo_magic`)**: New plan tier with configurable run limits (default 5) and 7-day expiration.

### Security
- Tokens stored as SHA-256 hashes — raw tokens never persisted in database.
- Admin demo creation endpoint requires `SIMHPC_API_KEY` authentication.
- IP logging on all demo token validation attempts.
- Redis + Supabase dual-layer storage for redundancy and fast reads.

---

## [1.3.1] - 2026-03-10


### Added
- **Protected Routes**: Implemented `ProtectedRoute` component to prevent unauthorized access to dashboard pages. Users are now redirected to the sign-in page if they are not authenticated.
- **Tier-Aware API**: Backend now queries Supabase `profiles` table directly to enforce plan limits (`free` vs `professional`).
- **Supabase Persistence**: Simulation results and summaries are now inserted into the `simulations` table using the Service Role Key.
- **Frontend Mutation Hooks**: Implemented `useMutation` for launching simulations with automated toast notifications and error handling.
- **Payment Success UX**: Added animated success page with confetti and 5-second redirect after Stripe checkout.

### Added
- **ExperimentNotebook Theme Toggle**: Added bright/dark mode toggle to the Experiment Notebook page matching the rest of the website.

### Fixed
- **Experiment Notebook Alignment**: Fixed responsive grid layout and row alignment issues in both light and dark modes.
- **Footer Logo Color**: Fixed SimHPC logo "Sim" text to inherit parent color for proper visibility in footer across all themes.
- **Global Background Consistency**: Updated all page backgrounds (SignIn, SignUp, Benchmarks, Docs, Pricing, About, Contact, APIReference, etc.) to match homepage color #F1EDE0.
- **Theming**: Updated global day background color to `#F1EDE0` for better visual consistency across all pages.

---

## [1.3.0] - 2026-03-09

### Added
- **Google One Tap Sign-In**: Integrated Google Identity Services (`g_id_onload`, `g_id_signin`) for frictionless authentication.
- **GitHub Pages Deployment**: Migrated frontend hosting to GitHub Pages (https://github.com/NexusBayArea/SimHPC).

---

## [1.2.0] - 2026-03-08


### Added
- **Experiment Notebook**: A persistent research workspace for automated logging, side-by-side experiment comparison, and "Replay" capability for solver parameters.
- **Abuse Prevention System**: Multi-layered security including device fingerprinting, IP-based account limits, honeypot fields, and compute guardrails (60s timeouts, delayed queues).
- **Mercury AI Integration**: Finalized transition to Inception Labs' Mercury AI for engineering-grade reports with numerical anchoring.
- Secure Repo Strategy: Migrated to a split-repository architecture, isolating the frontend in `lostbobo` (https://github.com/NexusBayArea/lostbobo.git) while keeping backend and AI logic closed-source.


### Security
- Implemented frontend-only repository strategy for Vercel deployment.
- Hardened `.gitignore` to prevent accidental exposure of backend orchestrator logic.
- Disconnected Supabase from GitHub sync to prevent unauthorized schema access.

---

## [1.1.0] - 2026-03-06


### Added
- **Mercury AI Migration**: Purged all Kimi AI references and fully transitioned to Mercury AI (Inception Labs) for engineering-grade report generation.
- **SimHPC Client Library**: TypeScript client with auto-auth and typed methods.
- **API Proxy**: Next.js route handler with JWT session extraction.

### Fixed
- Resolved circular dependencies in Celery tasks.
- Fixed event loop issues in async backend services.
- Hardened JWT verification logic.

---

## [1.0.0] - 2026-03-04


### Added
- Initial production launch with Stripe integration and PDF export.
- Multi-stage Docker optimization.
- Structured logging and Prometheus metrics.

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
