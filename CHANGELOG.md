# SimHPC Changelog

> All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.6] - 2026-04-10

### Added
- **Hardened Autoscaler v2.7.6**: Implemented production-safe scaling with scale-up (20s) and scale-down (30s) cooldowns to prevent thrashing.
- **Idempotency Guard**: Added `sim:processed` set-based idempotency to the worker to ensure exactly-once execution across pod restarts.
- **Cost Control Layer**: Implemented aggressive scale-down logic when the queue is empty and added burst protection (max 2 pods per cycle).
- **Pod Tracking**: Established `sim:pods` registry in Redis for deterministic and orderly termination of excess workers.

### Fixed
- **Runaway Scaling**: Enforced hard caps and cooldown windows to prevent GPU cost spikes during traffic surges.
- **Duplicate Job Execution**: Resolved potential race conditions where a job could be claimed by multiple workers during rapid scaling.

## [2.7.5] - 2026-04-10

### Added
- **Production Autoscaler v2.7.5**: Implemented a queue-aware elastic scaling engine for RunPod GPU workers using a non-linear pressure function (sqrt of backlog + age).
- **Worker Heartbeat Registry**: Established a central `sim:workers` hash in Redis for real-time tracking of active vs. stale workers.
- **Job Age Tracking**: Added `created_at` timestamps to enqueued jobs to enable SLA-sensitive scaling.

### Changed
- **Scaling Logic**: Replaced single-pod logic with dynamic multi-pod spawning based on Redis queue depth and oldest job age.
- **Dependency Update**: Added `requests` to the unified dependency manifest for RunPod API integration.

### Fixed
- **Stale Worker Cleanup**: Implemented automatic pruning of workers from the active registry after 60 seconds of inactivity.

## [2.7.4] - 2026-04-10

### Changed
- **Unified Base Image**: Established a single canonical CUDA-enabled base image (`Dockerfile.base`) for all services to eliminate ABI drift and library mismatches.
- **Port Standardization**: Finalized migration of all services, scripts, and documentation to port **8080** for consistent internal and external routing.
- **Dependency Isolation**: All service Dockerfiles now extend from the unified base, using `uv` to install only required extras (e.g., `[worker,gpu]`).

### Fixed
- **Runtime Drift**: Resolved potential `glibc` and `OpenMP` mismatches between API and Worker environments by sharing a common CUDA runtime baseline.

## [2.7.3] - 2026-04-10

### Changed
- **Dependency Unification**: Migrated from multiple `requirements.txt` files to a single `pyproject.toml` (PEP 621) as the source of truth for all services.
- **Modern Tooling**: Adopted `uv` for 10x faster and deterministic dependency resolution and installation.
- **Locking Protocol**: Implemented `uv.lock` for 100% reproducible builds across API, Worker, and Autoscaler.
- **Docker Optimization**: Updated all Dockerfiles (`unified`, `api`, `worker`, `autoscaler`) to use `uv` and multi-stage build patterns where appropriate.

### Fixed
- **Dependency Drift**: Eliminated hidden version mismatches between development, API, and GPU worker environments.

## [2.7.2] - 2026-04-10

### Changed
- **Architectural Upgrade**: Transitioned from `start.sh` to `supervisord` for process management in the Unified Pod, enabling independent restarts for API, Worker, and Autoscaler.
- **Boot-Order Enforcement**: Implemented health-aware startup sequence (Redis → API → Worker/Autoscaler) using custom wait scripts.
- **Port Alignment**: Standardized API orchestrator on port **8080** to match RunPod's internal routing and avoid Jupyter conflicts.
- **Log Management**: Implemented non-rotating `/dev/stdout` and `/dev/stderr` streaming for all sub-processes.

### Fixed
- **Port Conflicts**: Added `fuser -k 8080/tcp` to the container command to prevent "Address already in use" errors from default RunPod services.
- **Pathing Resolution**: Fixed working directory issues in `supervisord.conf` ensuring correct module resolution for the backend.
- **API Health Check**: Enhanced `/health` endpoint to include real-time Redis connectivity verification.
- **Autoscaler Resilience**: Added `system_ready` gate to prevent scaling actions before Redis is reachable.

## [2.7.1] - 2026-04-10

### Added
- **Production Pipeline v2.7.1**: Fully automated deployment to Vercel and RunPod with SHA-based image tagging and podReset verification.
- **Frontend Optimization**: Implemented lazy loading for heavy pages and optimized build chunks to reduce initial bundle size.

### Fixed
- **API Stub Alignment**: Resolved `init_routes` dependencies in `simulations.py`, fixing undefined `get_job_field` and redundant stubs.
- **Critical Syntax Error**: Fixed a broken `HTTPException` call in `simulations.py` that would have crashed the API.
- **Workflow Consolidation**: Replaced outdated RunPod deployment scripts with the unified `deploy.yml` v2.7.1 standard.

## [2.6.27] - 2026-04-09

### Fixed
- **Authority Alignment**: Established Supabase as the absolute source of truth for simulation usage tracking.
- **Data Integrity**: Removed redundant Redis-based usage counters to prevent data drift and eliminate race conditions in quota enforcement.
- **Unified Logic**: Consolidated usage calculation into a single Supabase query, ensuring consistent results between the API and Frontend Dashboard.

## [2.6.24] - 2026-04-09

### Optimized
- **Atomic Idempotency**: Implemented `SETNX`-based idempotency reservation to prevent race conditions during job submission.
- **O(1) Concurrency**: Replaced blocking Redis `KEYS` scans with atomic per-user active job counters for sub-millisecond concurrency checks.
- **Worker-Aware Dispatch**: Simulations now fail-fast if no heartbeating workers are detected in the active registry.

## [2.6.23] - 2026-04-09

### Strategic Roadmap (Full Infra)
- **Worker Management**: Defined the implementation plan for self-registration and heartbeat systems in `worker.py`.
- **Registry Design**: Established the `workers:active` Redis set as the central discovery point for the API.
- **Queue Formalization**: Standardized the Redis job queue with TTL-based worker health tracking.

## [2.6.22] - 2026-04-09

### Strategic Diagnosis
- **"Control-Plane Gap" Identification**: Diagnosed the root cause of `no_active_pods` error as a missing worker discovery and registry mechanism.
- **Worker Process Conflict**: Identified that containers were defaulting to Jupyter Lab (Port 8080) instead of the SimHPC Worker API (Port 8080).
- **Routing Analysis**: Discovered that non-compute requests were incorrectly dependent on active compute pods.

## [2.6.21] - 2026-04-09

### Strategic Roadmap
- **Authority Alignment**: Standardized Supabase as the primary source of truth for usage and simulations.
- **Atomic Idempotency**: Refined idempotency layer to use atomic Redis operations (`SETNX`).
- **Concurrency Optimization**: Replaced O(N) Redis scans with O(1) active job counters.
- **Async Integrity**: Transitioned all blocking calls to non-blocking async operations.

## [2.6.20] - 2026-04-09

### Added
- **Simulation Usage Quota Integration**: The frontend Dashboard now fetches real-time simulation usage stats from the `/api/v1/simulations/usage` endpoint, replacing hardcoded placeholders.
- **Dynamic Quota Display**: Updated the `RunControlPanel` to show "Weekly Runs" and "Quota Usage" (1 Run) to align with backend tier enforcement.
- **Improved API Client**: Added `getUsage` and `getUserProfile` to the `ApiClient` in `apps/frontend/src/lib/api.ts` for unified data fetching.

### Fixed
- **Duplicate API Declaration**: Resolved a critical TypeScript build error by merging duplicate `api` object declarations into the single `ApiClient` class in `apps/frontend/src/lib/api.ts`.
- **RunPod Port Conflict**: Integrated a port 8080 guard in `Dockerfile.unified` and `start.sh` using `fuser -k 8080/tcp` to ensure the FastAPI orchestrator can bind to the port without Jupyter interference.
- **GitHub Workflow Corruption**: Repaired the `deploy-runpod.yml` file, removing corrupted git diff markers and implementing the v2.6.5/v2.6.7 resilient deployment protocols (podReset + Fallback).
- **Unique Image Tagging**: Updated all GitHub workflows to use `${{ github.run_id }}` for Docker tagging, ensuring unique, immutable images for every build.

## [2.5.13] - 2026-04-07

### Added

- **"No-Env" Infisical Strategy**: Fully transitioned the stack to use Infisical CLI for secret injection, eliminating the need for local `.env` files.
- **Dynamic CORS (Regex)**: Replaced hardcoded origin lists in `api.py` with a flexible regex pattern to support all Vercel project subdomains and branch previews.
- **Refined Deployment Script**: Updated `deploy_unified.py` to capture `INFISICAL_TOKEN` from the local session and correctly output `POD_ID` for CLI automation.
- **Autoscaler Fail-Fast**: Implemented a critical check in `autoscaler.py` to shutdown immediately if the `INFISICAL_TOKEN` is missing, preventing "zombie" states.

## [2.5.12] - 2026-04-07

### Added

- **The Secret Handshake (RunPod Skill)**: Formalized the requirement for `INFISICAL_TOKEN` in RunPod templates to ensure stable secret injection on boot.
- **Vercel Sync Automation**: Added standardized command for syncing dynamic RunPod URLs to Vercel production environment variables.

## [2.5.11] - 2026-04-07

### Added

- **FastAPI Regex CORS**: Implemented `allow_origin_regex` to support Vercel branch and preview deployments (`*-projects.vercel.app`) without wildcard risks.
- **Autoscaler Fail-Safe**: Added boot-time verification for `INFISICAL_TOKEN` and API keys in `autoscaler.py` to prevent silent crashes and improve debuggability on RunPod.

### Fixed

- **Bare Except Guard**: Replaced bare `except:` blocks with specific exception handling (`json.JSONDecodeError`, `TypeError`, and `Exception`) in `worker.py` and `deploy_to_runpod.py`.

## [2.6.3] - 2026-04-07

### Fixed

- **Vercel Build Stability**: Migrated `AdminAnalyticsPage.tsx`, `WakeGPU.tsx`, and `ProtectedRoute.tsx` from root `src` to `apps/frontend/src` to resolve `ENOENT` build errors and align with Vercel deployment structure.
- **Infisical Project Integration**: 
  - Standardized all GitHub workflows to explicitly pass `--projectId="f8464ba0-1b93-45a1-86b5-c8ea5a81a2a4"` during secret export, resolving the "Project Not Connected" error in CI/CD.
  - Refreshed Infisical installation scripts to use the official Cloudsmith setup mirror for consistent tool versions.
- **Frontend Path Alignment**: Corrected relative import path for `AdminAnalyticsPage` in `apps/frontend/src/App.tsx`.

## [2.6.2] - 2026-04-07

### Fixed

- **CI/CD Hardening**: 
  - Standardized Infisical authentication across all GitHub workflows to use `INFISICAL_TOKEN` instead of outdated interactive login methods.
  - Standardized Docker Hub secrets to `DOCKER_LOGIN` and `DOCKER_PW_TOKEN` to resolve "unauthorized" errors.
  - Updated Infisical installation scripts to ensure the latest CLI version is used in CI environments.
- **File Path Resolution**: Verified and normalized `AlphaControlRoom.tsx` casing to ensure consistency for case-sensitive Vercel builds.
- **Import Audit**: Confirmed `App.tsx` correctly references all existing page components.

## [2.6.1] - 2026-04-07

### Fixed

- **Bare Except Guard**: Replaced bare `except:` blocks with specific exception handling (`json.JSONDecodeError`, `TypeError`, and `Exception`) in `worker.py` and `deploy_to_runpod.py` to prevent silent bug hiding and ensure Ruff compliance.
- **Python Worker Robustness**: Hardened job parsing logic to gracefully handle invalid Redis data without crashing.

## [2.6.0] - 2026-04-07

### Added

- **Cost-Optimized Autoscaler**:
  - Reduced `IDLE_TIMEOUT` from 300s to 120s for faster GPU release.
  - Implemented **Dormant Termination**: Automatically destroys pods inactive for > 48 hours to eliminate long-term disk and network volume costs.
  - Precise Cost Tracking: Now uses actual polling intervals for 100% accurate daily burn estimates.
- **Direct-Action Admin API**:
  - Implemented `runpod_service.py` in the API layer for immediate pod `stop` and `terminate` commands.
  - Decoupled manual interventions from the autoscaler loop for instant UI responsiveness.
- **Admin UI Enhancements**:
  - Added **Auto-Term Countdown** to the Admin Dashboard for dormant pods.
  - Real-time visibility into cost-optimization strategy.

### Changed

- **Improved Polling Resolution**: Increased autoscaler check frequency to 10s for more responsive scaling.

## [2.5.6] - 2026-04-07

### Added

- **Advanced Unified Proxy (Vercel)**:
  - **Dynamic Pod Resolution**: Automatically fetches active RunPod URLs via GraphQL API—no more hardcoded URLs.
  - **Cold Start Resilience**: Exponential backoff (max 5 retries) for handling GPU pod spin-ups.
  - **Resolved Endpoint Caching**: Caches RunPod URLs for 60s to minimize API overhead.
  - **Vercel-Side Redundancy**: Handles `NO_PODS` scenarios with a 503 status for frontend recovery.
- **Dedicated Health Endpoint**: Added `/health` to `api.py` for lightweight proxy-level verification.

### Fixed

- **CORS Persistence**: Final elimination of CORS blocks by enforcing server-side proxying only.

## [2.5.5] - 2026-04-07

### Added

- **Unified API Proxy (Vercel)**: Implemented `/api/[...path].ts` serverless function to eliminate CORS issues permanently. All frontend calls now route through `/api/api/v1/` to the RunPod fleet.
- **Async Simulation Patch**: Applied a high-performance job queue architecture using Redis `brpop` and status polling.
  - API now pushes `job_id` to `simhpc_jobs` and stores full job state in `job:{id}` keys.
  - Worker uses blocking pop for efficient resource utilization.
- **Vercel Auth Passthrough**: Configured the proxy to pass Supabase JWT tokens to the backend orchestrator.

### Fixed

- **Vercel Build Error (APIReference)**: Verified and corrected the `APIReference` export in `apps/frontend/src/pages/index.ts`.
- **Python Worker Lint Failure**: Fixed `F401` unused imports in `services/worker/worker.py` using `ruff`.
- **Frontend API Alignment**: Updated `apps/frontend/src/lib/api.ts` to use the new unified proxy layer.

## [2.5.4] - 2026-04-06

### Added

- **Full Fleet Build (v2.5.3)**: Built and pushed hardened, non-root Docker images for the entire SimHPC ecosystem:
  - `simhpc-worker:v2.5.3`: NVIDIA CUDA 12.8.1 runtime with CVE remediations and non-root execution.
  - `simhpc-api:v2.5.3`: Hardened multi-stage build with gunicorn/uvicorn and non-root user.
  - `simhpc-autoscaler:v2.5.3`: Infisical-integrated multi-stage build for secure secret injection.

### Fixed

- **Simulation Start Error (405)**: Added detailed error message surfacing in `api.ts` — now shows actual HTTP status and backend error detail instead of generic "Failed to start simulation"
- **CORS Preflight Fix**: Added explicit `OPTIONS` handler for `/api/v1/simulations` and enabled `expose_headers=["*"]` in `api.py` to resolve cross-origin blocks on Vercel deployments.
- **Empty Token Guard**: Added authentication check in `Dashboard.tsx` before calling simulation API
- **Infisical CI Workflow**: Updated `deploy-beta-runpod.yml` — replaced deprecated `--projectId` flag with `.infisical.json` init step, updated env var names from `INFISICAL_CLIENT_ID`/`INFISICAL_CLIENT_SECRET` to `INFISICAL_MACHINE_IDENTITY_ID`/`MAC_ID_SEC`

## [2.5.3] - 2026-04-05

### Fixed

- **API Endpoint Fix**: Fixed `/api/v1/usage` → `/api/v1/simulations/usage` mismatch causing "Failed to fetch" errors
- **Robustness Request Model**: Added `RobustnessRunRequest` Pydantic model for proper request validation
- **Cancel Endpoint**: Added `DELETE /api/v1/simulations/{sim_id}` for job cancellation
- **SQL Security (Lager)**: Hardened PostgreSQL functions and views against search path hijacking and RLS bypass:
  - Added `SET search_path = public` to `update_updated_at_column` and `update_notebook_entry_updated_at` trigger functions.
  - Set `SECURITY DEFINER` on trigger functions for consistent execution.
  - Added `WITH (security_invoker = true)` to `simulation_history` and `certificate_verification_view` views to ensure they respect querying user's RLS policies.
- **Supabase Initialization (Vercel)**: Fixed "Supabase client not initialized" error on Vercel by adding `envPrefix: ['VITE_', 'SUPABASE_']` to `vite.config.ts`. This allows Vite to pick up environment variables provided by the Supabase-Vercel integration (`SUPABASE_URL`, `SUPABASE_ANON_KEY`).
- **Auth Error Messaging**: Improved error messages on SignIn and SignUp pages when the Supabase client is uninitialized, providing actionable guidance on environment variables.
- **Environment Schema**: Updated `frontendSchema` and `env/client.ts` to include all possible Supabase environment variable variants for better robustness.

### Added

- **Simulation Pipeline**: Background async pipeline that updates job status, progress, and persists results to Supabase in real-time
- **Telemetry Queue Integration**: Progress updates pushed to `telemetry_queue` for WebSocket broadcast
- **Supabase-first Listing**: `/simulations` now pulls from Supabase as source of truth with Redis fallback
- **Infisical Integration**: Full secret injection for local dev and production deployments
- **RunPod Integration**: Real GPU job submission and polling via `RunPodJobClient`
- **Retry System**: Exponential backoff with max attempts (3) for transient failures
- **Recovery Worker**: Background task that recovers orphaned jobs on API restart
- **Distributed Locking**: Prevents duplicate job execution across API instances

### Changed

- **Logo Styling**: Removed all glow and shadow effects from the SimHPC logo icon and text ("Sim" and "HPC") for a cleaner, flatter aesthetic.
- **Logo Colors**: Updated "Sim" text and icon to use theme-aware colors (`slate-900` in light mode, `white` in dark mode) and "HPC" text to a consistent blue (`blue-600`/`blue-500`).

## [2.5.2] - 2026-04-04

### Fixed

- **Day/Night Mode (Theme System)**: Complete rewrite of the theme system to fix broken dark/light mode switching:
  - **CSS Variables**: Moved dark theme variables from `:root` to `.dark` selector. `:root` now contains light theme defaults. This aligns with Tailwind's `darkMode: ["class"]` strategy.
  - **useTheme Hook**: Removed conflicting body class manipulation (`bg-slate-950`, `text-white`). Now uses only `document.documentElement.classList.toggle('dark')` which properly cascades CSS variables.
  - **System Preference Detection**: Added `window.matchMedia('(prefers-color-scheme: dark)')` detection for first-time visitors. Theme now respects OS-level dark/light mode preference.
  - **Flash Prevention**: Added inline `<script>` in `index.html` that applies theme before React hydrates, eliminating the flash of wrong theme on page load.
  - **System Preference Listener**: Added event listener for OS theme changes — if user hasn't manually set a preference, the site follows system changes in real-time.
  - **setTheme Export**: Added explicit `setTheme()` function to context for programmatic theme changes.
- **Mobile Responsiveness**: Verified all sections (Hero, Pricing, WhoItsFor, Stack, Footer, Navigation) use proper Tailwind responsive breakpoints (`sm:`, `md:`, `lg:`). Mobile navigation with hamburger menu confirmed working.

### Changed

- **index.css**: Restructured CSS custom properties — light theme in `:root`, dark theme in `.dark` selector.
- **useTheme.tsx**: Simplified to class-only approach on `<html>` element. Added `getInitialTheme()` helper with localStorage + system preference fallback.
- **index.html**: Added inline theme detection script to prevent flash of unstyled content.
- **Light Mode Background**: Changed from pure white (`#ffffff`) to warm cream (`#f1ede0`, HSL `46 38% 91%`) across all light-mode surfaces. Updated `--background`, `--secondary`, `--muted`, `--accent`, `--border`, and `--input` CSS variables. Replaced hardcoded `bg-white` with `bg-background` in Hero, Pricing, WhoItsFor, Stack, and ValueDifferentiator sections.
- **Google OAuth**: Added "Continue with Google" button to both SignIn and SignUp pages using Supabase `signInWithOAuth({ provider: 'google' })`. Redirects to `/dashboard` after successful auth. GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET configured via Infisical.
- **Supabase Env Var Naming**: Fixed Supabase client to use `VITE_SUPABASE_ANON` (matching Vercel env var) instead of `VITE_SUPABASE_ANON_KEY`. Added fallback chain: `VITE_SUPABASE_ANON` → `VITE_SUPABASE_ANON_KEY` → `SUPABASE_ANON_KEY`. Updated Zod schema to match.
- **Supabase Client Initialization**: Changed `supabase.ts` to read env vars directly from `import.meta.env` instead of through Zod-validated `env` client which was silently returning empty strings.
- **Auth Pages Styling**: Added Navigation and Footer to SignIn and SignUp pages. Updated form styling for light/dark theme compatibility.
- **SPA Routing**: Added rewrite rule to `apps/frontend/vercel.json` for client-side routing.
- **Vercel Build Fix**: Updated `deploy-vercel.yml` workflow to build from `apps/frontend/` directory. Added `env/` module files that were missing from `apps/frontend/src/`.
- **Documentation**: Updated README.md with full environment variable table, Google OAuth setup SOP, and correct naming conventions. Updated ARCHITECTURE.md, GEMINI.md, AI_DIRECTIVES.md with correct env var names.
- **Dashboard**: Changed tier label from "Beta Pilot" to "Pilot". Alpha Cockpit link now opens in a new tab (`target="_blank"`).
- **Engineer Notebook**: Complete redesign as a persistent research workspace with:
  - **Experiment entries** with title, research question, parameters, observations, conclusions, and freeform notes
  - **Sidebar entry list** with search, create, and compare mode
  - **Link simulations** — connect notebook entries to specific simulation runs
  - **Compare mode** — side-by-side comparison of two experiments
  - **Replay button** — reloads experiment parameters in a new tab
  - **Experiment timeline** — chronological view of all entries
  - **Linked experiments** — visible list of connected simulations per entry
  - **Collapsible sections** — each field can be expanded/collapsed
  - **Debounced autosave** (1.5s) to Supabase `notebook_entries` table
  - Created `006_engineer_notebook_entries.sql` migration with RLS policies and `updated_at` trigger
- **Dashboard Labels**: Renamed "Alpha Cockpit" → "Live Center" and "Note Book" → "Notebook".
- **Alpha Control Room Dark/Light Mode**: Added `dark:` variants to all backgrounds, borders, text colors, and accents. Sidebar, ticker bar, and footer now adapt to theme toggle.
- **Footer**: Replaced Twitter icon with X logo (SVG), kept link to `x.com/simhpc`. Legal links (Terms, Privacy, Cookie Policy) now route to populated pages.
- **Legal Pages**: Created `src/pages/legal/` with Terms of Service (6 sections), Privacy Policy (5 sections), and Cookie Policy (3 sections). All use shared `LegalLayout` component with dark mode support.
- **Interactive Onboarding System**: Complete rewrite of onboarding from basic localStorage to production-grade step-based engine:
  - **Step definitions** (`steps.ts`): 8 steps from welcome modal → sidebar exploration → run simulation → monitor jobs → view results → try notebook → try live center → completion
  - **OnboardingModal**: Full-screen modal with spring animations, skip button, progress indicator, and dark mode support
  - **OnboardingTooltip**: Element-targeted tooltips with auto-positioning, cyan highlight outlines, progress bar, and step counter
  - **StepRenderer**: Orchestrates modals and tooltips based on current step definition
  - **Supabase autosave**: Debounced (800ms) sync to `onboarding_state` table with localStorage cache for instant resume
  - **Cross-device resume**: Loads from localStorage instantly, then hydrates from Supabase backend
  - **Event tracking**: `trackEvent()` dispatches events that can auto-advance steps
  - **Version conflict resolution**: Optimistic concurrency via version field
  - **Dashboard integration**: Added `data-onboarding` attributes to sidebar, run button, job queue, results panel, notebook link, and live center link
- **Onboarding Completion Fix**: "Start Simulating" button on final modal now properly marks onboarding as complete and dismisses the guide
- **API Reference Page**: New `/api` page with core concepts, 5 endpoint docs (Create, Get, List, Cancel, Results), status lifecycle table, rate limits, error codes, best practices, versioning, and support info. Collapsible sections with copyable code blocks.
- **Header**: Renamed "Docs" to "Documentation" in navigation.
- **Dashboard Route**: Changed `/dashboard/alpha` to `/dashboard/live` in routing and sidebar link.
- **Logo Dark Mode**: "Sim" text now renders as white in dark mode for better contrast.
- **Logo Light Mode**: "Sim" text changed to white for consistent branding across all backgrounds.
- **Logo Day Mode**: "Sim" text changed to `text-slate-900` (near-black) for readability on light backgrounds.
- **Logo Icon Dark Mode**: Logo hexagonal mesh icon now renders white in dark mode on Dashboard and Live pages.
- **Logo Consistent White**: Logo icon and "Sim" text set to white in both day and dark mode (header/footer have dark slate-900 backgrounds).
- **Documentation Page**: New `/docs` page with full Quick Start guide — 7-step workflow (Run → Wait → View → Change → Re-run → Compare → Download), free tier expectations, upgrade triggers, key insight callout, and troubleshooting section (404, Worker Status, Wake GPU, Job Queuing, Performance, Bug Reporting).
- **Pricing Update**: Starter plan $99 → $299/month, Professional plan $299 → $499/month.
- **Logo Glow Effect**: Added thin white drop-shadow glow to logo icon and "Sim" text, subtle blue glow to "HPC" text for visibility across all backgrounds.
- **Dockerfile.autoscaler**: Multi-stage build using `python:3.11-slim` builder with gcc/python3-dev, then production stage with only installed packages. Copies `src/runpod_api.py` and `src/autoscaler.py`.
- **docker-compose.yml**: Simplified to 3 services — Redis (message broker), Autoscaler v2.2.1, and Mock Worker (for testing without GPU). Removed frontend, API, and full worker for lightweight local dev/testing.

---

## [2.5.1] - 2026-04-04

### Fixed

- **Vercel Build Success**: Fixed all TypeScript errors blocking production builds:
  - `SimulationUpdate.status` now uses `SimulationRow['status']` union type instead of `string`
  - Removed `as SimulationRow` cast hack in `useSimulationUpdates.ts`
  - Renamed `setTimeout` state in `Dashboard.tsx` to `setRequestTimeout` to avoid shadowing global `window.setTimeout`
  - Fixed `supabase is possibly null` (TS18047) in `useSimulationUpdates.ts`, `useSimulations.ts`, `SignIn.tsx`, `SignUp.tsx` — use local const after null guard
  - Added `ErrorBoundary` component to surface runtime errors instead of blank screen
  - Fixed `ThemeProvider` to apply theme classes to `<html>` and `<body>` directly
  - Made `supabase` export nullable — returns `null` if env vars are missing
- **Submodule Cleanup**: Removed broken self-referencing `apps/frontend` submodule (was pointing to `lostbobo.git` itself). Cleaned up `.gitmodules` and `.git/modules/`.
- **Frontend Rebuild**: Rebuilt all missing components (Navigation, Hero, Stack, Pricing, Footer, Dashboard, SignIn, SignUp, ConfigurationPanel, RunControlPanel, ResultsPanel, types, hooks) since original files were lost during submodule removal.

### Fixed

- **Frontend Crash (Supabase Client)**: `src/lib/supabase.ts` — added fail-fast validation that throws immediately if `VITE_SUPABASE_URL` or `VITE_SUPABASE_ANON_KEY` are missing. Eliminates silent white-screen crashes caused by empty-string client initialization.
- **useSimulationUpdates Guards**: Wrapped `fetchHistory()` in try/catch, added `!supabase` guard, protected realtime subscription in try/catch block, and made channel cleanup safe with `if (channel)` check.
- **useSimulations Guards**: Added `!supabase` guard, wrapped fetch in try/catch, protected realtime subscription, safe channel cleanup.
- **useAuth Guards**: Added `!supabase` guard in useEffect and getToken() to prevent runtime errors when client is uninitialized.
- **Dashboard Rendering**: Rebuilt `App.tsx` DashboardPage to use actual styled components (`ConfigurationPanel`, `RunControlPanel`, `ResultsPanel`, `DocumentPage`) with tab navigation and mock simulation run flow. Added `framer-motion` dependency (required by ResultsPanel and DocumentPage).
- **Documentation**: Updated `ARCHITECTURE.md` with Frontend Environment Variables section explaining Vite build-time injection, Infisical wrapping, and `VITE_` prefix requirements.

### Changed

- **CI/CD Pipeline (GitHub Secrets)**: Simplified workflows to use GitHub secrets directly (`DOCKER_ACCESS_TOKEN`, `DOCKER_USERNAME`, `VERCEL_TOKEN`, etc.) instead of Infisical OIDC which was failing with 404 errors. Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` to all workflows. Split into path-triggered workflows: `deploy-worker.yml`, `deploy-autoscaler.yml`. `deploy.yml` is audit-only (ruff lint + format). Vercel deploys via native GitHub integration (not GitHub Actions).
- **docker-compose.yml**: Added autoscaler service with billing guards, backend network bridge, simulation_scratch and workspace volumes, healthchecks for api/worker/redis. Updated worker image to v2.5.0.

## [2.5.0] - 2026-04-02

### Added

- **Zod Environment Validation**: `src/env/schema.ts` (typed frontend/backend/full schemas), `src/env/client.ts` (runtime-safe env access), `scripts/validate-env.ts` (CI validation with prod/dev modes). Build fails immediately with clear error if `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, or `VITE_API_URL` are missing or malformed.
- **Dependencies**: Added `zod` (runtime schema validation) and `tsx` (TypeScript script runner) to frontend.
- **API Client**: `src/lib/api.ts` — typed API wrapper for simulation usage, start, and cancel endpoints with Bearer token auth.
- **Build Config**: `package.json` (React 18, Vite 5, Tailwind 3, Supabase JS, Zustand, Radix UI, Lucide, Sonner, React Router), `vite.config.ts` (with `@` alias), `tailwind.config.js`, `postcss.config.js`.
- **Frontend Docker Build**: `apps/frontend/Dockerfile.prod` confirmed as two-stage build (Node 20 Alpine → Nginx Alpine) with `VITE_` build-time ARG injection for Supabase and API URLs.
- **Nginx SPA Config**: `apps/frontend/nginx.conf` with `try_files` fallback for React Router deep-link support and 30-day static asset caching.
- **Git Pre-Commit Hook**: `.pre-commit-config.yaml` — managed by the `pre-commit` framework. Runs `ruff --fix` and `ruff-format` on staged files before every commit. Auto-fixed 26 errors and reformatted 6 files on first run.
- **Unified Deployment Pipeline**: `.github/workflows/deploy.yml` — lint-gated CI/CD that builds Worker + Autoscaler Docker images and deploys Frontend to Vercel, all on push to `main`. Jobs: `audit` → `deploy-worker` + `deploy-autoscaler` + `deploy-vercel`. Docker Hub login uses `DOCKER_ACCESS_TOKEN` via `--password-stdin` for secure authentication.
- **RunPod Auto-Updater**: `services/worker/pull_and_restart.sh` — cron-based script that pulls latest `simhpc-worker:latest` from Docker Hub and restarts the container on change. Zero-touch GPU fleet synchronization.
- **ProtectedRoute (RBAC)**: `src/components/auth/ProtectedRoute.tsx` — admin-gated route wrapper. `/admin/analytics` now requires `app_metadata.role === 'admin'` or founder email match. Non-admins redirect to `/dashboard`.
- **useAuth Supabase Integration**: `src/hooks/useAuth.ts` — expanded from Zustand stub to full Supabase auth listener with `user`, `loading`, `isAdmin`, and async `getToken()`. Backward-compatible `isLoading` alias included.
- **useSimulations Real-Time Hook**: `src/hooks/useSimulations.ts` — Supabase Realtime subscription for the `simulations` table. Extracts telemetry (progress, thermal_drift, pressure_spike) from `result_summary`/`gpu_result` JSONB. Drives live progress rings and warning indicators in `ActiveSimulations.tsx`.
- **Guidance Engine Prompt Template**: `GUIDANCE_PROMPT_TEMPLATE` in `api.py` — Chain-of-Thought prompt for Mercury AI that interprets simulation telemetry into actionable structural health reports.
- **AI Report Endpoint**: `POST /api/v1/alpha/generate-report/{job_id}` — fetches simulation data, formats guidance prompt, calls Mercury AI, saves `ai_report` back to `result_summary` for persistence.
- **Admin Dashboard (Sidebar Layout)**: `src/pages/admin/AdminAnalyticsPage.tsx` — expandable sidebar with Fleet Analytics as default tab. KPI cards (Active Workers, Burn Rate, Active Sims, Queue Depth), live telemetry table with thermal drift and pressure spike warnings. Slots ready for User Management, Stripe Revenue, and AI Guidance Engine Prompts.
- **Supabase Edge Function**: `supabase/functions/get-fleet-metrics/index.ts` — server-side fleet metrics calculation. Verifies admin via `app_metadata`, counts active/queued simulations using `service_role` key (RLS bypass), returns pod count and hourly spend. RunPod hourly rate and job-per-pod logic never exposed to client. Auto-creates billing alerts when spend exceeds $10/hr threshold (deduplicated per hour).
- **Platform Alerts Table**: `supabase/migrations/004_platform_alerts.sql` — `platform_alerts` table with Realtime enabled. Stores billing, thermal, and system alerts with severity levels. Admin-only RLS, indexed for fast queries.
- **Panic Button (Edge Function)**: `supabase/functions/trigger-panic-shutdown/index.ts` — admin-only emergency endpoint. Terminates all RunPod pods via GraphQL API, logs critical alert to `platform_alerts`. Requires double confirmation from UI.
- **Panic Button (Python Skill)**: `services/skills/panic_button.py` — standalone script for CLI/MCP use. Terminates all pods, logs alert. Usable via Infisical-injected env vars.
- **Admin Dashboard Updates**: `AdminAnalyticsPage.tsx` — added Alert Center sidebar (Realtime subscription, severity-coded cards, toast notifications), Panic Button (double-confirmation, loading state), and `platform_alerts` integration.

### Changed

- **Worker Heartbeat**: `send_heartbeat()` moved to the top of the main `while True` loop in `worker.py`. Heartbeat now fires every cycle regardless of job activity, keeping the "Sim Worker" Dashboard LED consistently **Cyan**.
- **Docker Compose**: Frontend service confirmed passing `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL` as build args from host `.env`.
- **Vercel Env Var Documentation**: Documented that Docker `build.args` and Vercel environment variables are separate systems. Vercel requires explicit `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`, and `VITE_STRIPE_PUBLISHABLE_KEY` in Dashboard → Settings → Environment Variables, followed by a redeploy.
- **Infisical Secret Injection**: `api.py` refactored to pull `JWT_ALGORITHM`, `MERCURY_API_URL`, `MERCURY_MODEL_ID`, and `GCP_PROJECT_ID` from environment variables (via Infisical). Hardcoded `HS256`, `mercury-2`, and `inceptionlabs.ai` URL removed. Local start command: `infisical run --env=prod -- docker-compose up --build`.
- **Docker Compose Env Expansion**: All services now declare `${VARIABLE}` syntax for Infisical-injected secrets (`JWT_ALGORITHM`, `MERCURY_API_URL`, `MERCURY_MODEL_ID`, `GCP_PROJECT_ID`). Worker image versions updated to `v2.5.0`.
- **Supabase Client Naming Fallback**: `src/lib/supabase.ts` checks both `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` and `SB_URL`/`SB_ANON_KEY` for Infisical compatibility.
- **Infisical Project Linking**: Requires `infisical init` to be run interactively to create `.infisical.json` and link the local directory to the SimHPC vault. Without this file, `infisical run` returns zero secrets.
- **Infisical Universal Auth (Machine Identity)**: Machine identity "RogWin" configured for CI/CD. Login via `infisical login --universal-auth --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>"` or set `INFISICAL_UNIVERSAL_CLIENT_ID` / `INFISICAL_UNIVERSAL_CLIENT_SECRET` environment variables.
- **Docker Worker Image v2.5.0**: `simhpc-worker:v2.5.0` built successfully from `Dockerfile.worker` (CUDA 12.8.1 runtime, Python 3.10, all dependencies installed).
- **Supabase CLI (v2.84.8)**: Installed via npm at `node_modules/supabase/bin/supabase.exe`. Use full path `.\node_modules\supabase\bin\supabase.exe` or copy to root as `supabase.exe`. Link project with `--project-ref <REF>`, push migrations with `db push`, deploy functions with `functions deploy --use-api`.
- **Supabase Linked & Deployed**: Project `ldzztrnghaaonparyggz` linked. Migrations `002`–`004` pushed. Edge functions `get-fleet-metrics` and `trigger-panic-shutdown` deployed via `--use-api` flag (bypasses Docker).

### Fixed

- **Ruff Lint (api.py)**: Resolved all 33 ruff errors — moved `load_dotenv()` before all imports (E402), removed 9 unused imports (F401: `BackgroundTasks`, `Body`, `WebSocketDisconnect`, `StaticFiles`, `FileResponse`, `Response`, `JWTError`, `jwt`, `get_result`), moved `logger` setup before first use (F821), moved `admin_router.init_routes()` after `verify_admin` definition (F821), renamed duplicate `check_rate_limit` → `enforce_rate_limit` (F811), fixed bare f-string (F541).
- **Ruff Lint (worker.py)**: Removed unused `last_active` variable (F841).
- **Dockerfile.worker**: Updated `COPY` paths from `services/runpod-worker/` to `services/worker/` to match v2.5 consolidation.
- **Dockerfile.autoscaler**: Updated `COPY` paths from `services/runpod-worker/` to `services/worker/`, added missing `requirements-autoscaler.txt`.
- **Worker Race Condition**: Fixed non-atomic `active_jobs` check/pop in `worker.py` — now pops job first, checks capacity second, pushes back with `lpush` if at limit.
- **Consolidation Script**: Fixed `sed -i` for macOS compatibility using `sed -i ''` via OS detection (`$OSTYPE == "darwin*"`).
- **tsconfig.json**: Changed `moduleResolution` from `"Node"` to `"Bundler"` for correct Vite + React 19 subpath resolution.
- **Security**: Removed hardcoded RunPod pod ID default from `api.py`. Redacted live SSH credentials and pod IPs from `progress.md`, `README.md`, `ARCHITECTURE.md`, `GEMINI.md`, `CHANGELOG.md`, and `ROADMAP.md`.

## [2.5.0] - 2026-04-01

### Added

- **SQL Migration**: `supabase/migrations/002_beta_schema_normalization.sql` — idempotent migration renaming `simulation_history` → `simulations`, adding `certificates`, `documents`, `document_chunks`, `simulation_events` tables, RLS policies, indexes, `updated_at` trigger, backward-compat view.
- **TypeScript Types**: New `src/types/` directory with `db.ts` (schema mirror), `audit.ts` (audit types), `api.ts` (API contracts), `realtime.ts` (partial update types), `view.ts` (mapper), `index.ts` (barrel export).
- **Worker v2.5.0**: Full rewrite of `services/runpod-worker/worker.py` — correct status flow (`running → auditing → completed`), writes `gpu_result`, `audit_result`, `hallucination_score`, `pdf_url`, `certificate_id`, `updated_at`. Creates `certificates` row with SHA-256 verification hash.
- **Stub Audit**: `run_audit()` function returning pass/fail structure with `hallucination_score`, `flags`, `rag_anomalies`, `auditor_remark`.
- **Certificate Pipeline**: `create_certificate()` writes to `certificates` table with `verification_hash` and links back via `simulation.certificate_id`.

### Changed

- **Frontend Types**: `useSimulationUpdates.ts` now uses `SimulationRow` and `SimulationUpdate` from `types/`. Queries `simulations` table (not `simulation_history`). Handles partial realtime updates safely.
- **Store**: `controlRoomStore.ts` updated with `AuditAlert` interface, `SimulationStatus` enum, `id` field on `ActiveSimulation`.
- **Dashboard.tsx**: Imports `SimulationRow` from `@/types/db` instead of legacy `SimulationRecord`.
- **SimulationDetailModal.tsx**: Imports `SimulationRow` from `@/types/db`.
- **API**: `record_simulation_start()` in `api.py` now writes to `simulations` table.
- **Routes Split**: `api.py` split into modular route files: `routes/simulations.py` (create, fetch, status, export-pdf), `routes/certificates.py` (generate, verify), `routes/control.py` (cockpit state, commands, timeline, lineage), `routes/admin.py` (fleet management). All routes initialized via `init_routes()` pattern.
- **API Version**: Bumped to `2.5.0`.

---

## [2.4.1] - 2026-04-01

### Added
- **Persistent Onboarding (Autosave & Cross-Device Resume)**: Versioned state sync to backend with `GET/POST /api/onboarding` and `POST /api/onboarding/event` endpoints.
- **Conflict Resolution**: Optimistic UI with version checks — stale writes rejected with `409 Conflict`, frontend auto-hydrates from server.
- **Debounced Autosave**: Onboarding state synced to backend 1s after any change, with 30s multi-device polling.
- **LocalStorage Resume**: Instant UI response from local cache while backend syncs in background.

### Changed
- **Component Extraction**: Extracted `WakeGPU.tsx` from `AdminAnalytics.tsx` into reusable component at `apps/frontend/src/components/admin/WakeGPU.tsx`.
- **Store Synchronization**: Renamed `lineage` → `lineageData` in `controlRoomStore.ts` for consistent naming across all consumer components.
- **CVA Button Standardization**: Replaced ad-hoc `Button.tsx` styling with professional `class-variance-authority` implementation, resolving project-wide typing errors.
- **Tier-Gated Artifact Access**: Integrated signed-URL logic for PDF Report downloads in `SimulationDetailModal.tsx` with Professional-tier plan checks.
- **Promise Handling**: Resolved `getToken` Promise handling across all cockpit components.
- **Path Alias Resolution**: Fixed `tsconfig.json` `@/*` path alias for monorepo frontend.

---

## [2.4.0] - 2026-03-30

### Added
- **Interactive Onboarding (8-Step Value Journey)**: Guided product walkthrough with tooltips, modals, and event-triggered hints.
  - Step 1: Welcome Modal (First Login Trigger)
  - Step 2: Template Selection (Highlight & Dim UI)
  - Step 3: Configuration (Progressive Tooltips)
  - Step 4: Queue Awareness (Soft Sell for GPU)
  - Step 5: Results Visualization (The "Value" Moment)
  - Step 6: MLE Optimization (The "Differentiation" Moment)
  - Step 7: Comparison View (Proof of Value)
  - Step 8: Conversion Trigger (Soft Paywall/Upgrade Card)
- **Conversion Intelligence**: Smart soft paywalls triggered by GPU suggestion or queue wait times.
- **Event-Driven Trigger Engine**: Backend evaluates `event_stream` to trigger context-aware hints.
- **Zustand Onboarding State**: Global `OnboardingProvider` with persistent `onboarding_state` sync.
- **Framer Motion Animations**: Smooth transitions for tooltip and modal rendering.

### Changed
- **Progress Tracking**: Persistent UI element tracking the "Value Journey" across sessions.
- **Documentation**: Version bumps across README, ARCHITECTURE, GEMINI, ROADMAP, and progress to v2.4.0.

---

## [2.3.0] - 2026-03-28

### Added
- **Option C Autoscaler**: Replaced `terminate_pod` with `stop_pod` for hibernation-based scaling. Pods are STOPPED (not terminated) after idle timeout, preserving the disk and Network Volume at `/workspace`.
- **Network Volume Persistence**: Persistent storage mounted at `/workspace` on GPU pods ensures solver caches, weights, and simulation data survive pod stop/start cycles.
- **"Wake GPU" Admin Control**: `POST /api/v1/admin/fleet/warm` endpoint and `WakeGPU.tsx` frontend component allow proactive pod resumption (~90s) before demos.
- **Readiness Polling**: `GET /api/v1/admin/fleet/readiness` endpoint checks if pods are ready and worker is connected.
- **Rich Fleet Status**: Consolidated fleet API returns running/stopped pod IDs, queue depth, daily cost, and scaling events.

### Changed
- **Scaling Strategy**: Autoscaler now prefers `STARTING` (resuming) a STOPPED pod over creating a new one — reduces wake-up from ~3 min to ~90s.
- **Idle Cost Reduction**: Dormant cost reduced to disk-only (~$0.10/day) vs. full GPU billing on termination.
- **Docker Images**: Published `simhpcworker/simhpc-api:v2.3.0`, `simhpcworker/simhpc-worker:v2.3.0`, `simhpcworker/simhpc-autoscaler:v2.3.0`.
- **Documentation**: Version bumps across README, ARCHITECTURE, GEMINI, ROADMAP, and all frontend docs to v2.3.0.
- **Cleanup**: Removed stale duplicate markdown files from `apps/frontend/` (README, GEMINI, ROADMAP, progress, ALPHA_PILOT_GUIDE, MISSION_CONTROL_STRATEGY) — canonical copies are in the repo root.

---

## [2.2.1] - 2026-03-26

### Added
- **Docker Hub Registry**: Published three production images:
  - `simhpcworker/simhpc-api:v2.2.1` — FastAPI orchestrator with Mercury AI integration.
  - `simhpcworker/simhpc-worker:v2.2.1` — NVIDIA CUDA 12.1 GPU physics worker with Redis polling.
  - `simhpcworker/simhpc-autoscaler:v2.2.1` — Queue-aware multi-pod autoscaler with cost caps.
- **Monorepo Restructure**: Migrated API service from `services/robustness-orchestrator/` to `services/api/` for clarity.
- **New `services/worker/`**: Standalone worker service with robustness, PDF, and AI report modules.

### Changed
- **Documentation Consolidation**: Removed duplicated Mercury AI appendix (~300 lines) from 5 files; canonical reference now in `ARCHITECTURE.md`.
- **Submodule Mapping**: Added `.gitmodules` for `apps/frontend` (lostbobo.git) and `services/api` (SimHPC.git).
- **Version Bump**: All references updated from v2.2.0 to v2.2.1 across README, ARCHITECTURE, ROADMAP, GEMINI, ALPHA_PILOT_GUIDE, and MISSION_CONTROL_STRATEGY.
- **`.dockerignore`**: Comprehensive ignore rules to prevent multi-GB build context bloat.

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
  - **pod SimHPC_P_01 Integration**: Full async lifecycle management for Alpha chat requests in the main orchestrator.
- **Backend RunPod Client**: New `RunPodClient` in `api.py` for managing pod SimHPC_P_01 jobs, status polling, and result retrieval.
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

### Fixed
- **Blank White Page**: Reverted manualChunks and lazy loading in the frontend to resolve a TypeError: Cannot read properties of undefined (reading 'createContext') caused by multiple React instances across chunks.

