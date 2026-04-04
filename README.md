# SimHPC Mission Control Cockpit

The SimHPC Frontend is **LIVE** and accessible at [https://simhpc.com](https://simhpc.com).

This is the public-facing repository for the SimHPC Mission Control Cockpit, a premium interface for aerospace and thermal engineering simulations.

## Architecture (v2.5.1)

### Single Source of Truth Structure

SimHPC v2.5 consolidates all backend and worker logic into a unified, clean structure:

- **`services/api/`**: FastAPI orchestrator (Mercury AI integration, fleet management).
- **`services/worker/`**: The unified compute plane.
  - `worker.py`: Physics execution + PDF generation + Supabase sync.
  - `autoscaler.py`: Option C Hibernation strategy (formerly `idle_timeout.py`).
  - `runpod_api.py`: Low-level RunPod lifecycle management.

### Dependencies

- **Python 3.14** — Worker runtime
- **pip 26.0.1**, **setuptools 82.0.1**, **wheel 0.46.3** — Package management
- **redis 7.4.0**, **supabase 2.28.3**, **python-dotenv 1.2.2**, **httpx 0.28.1**, **fpdf 1.7.2**

### Docker Containers

| Service | Image | Dockerfile | Purpose |
| :--- | :--- | :--- | :--- |
| Frontend | Nginx Alpine | `apps/frontend/Dockerfile.prod` | React/Vite cockpit with SPA routing via Nginx |
| API | `simhpcworker/simhpc-api:v2.5.1` | `Dockerfile.api` | FastAPI orchestrator (Mercury AI integration) |
| GPU Worker | `simhpcworker/simhpc-worker:v2.5.1` | `Dockerfile.worker` | Unified Physics + Metrics + Reports |
| Autoscaler | `simhpcworker/simhpc-autoscaler:v2.5.1` | `Dockerfile.autoscaler` | Option C: On-demand + Network Volume |
| Redis | `redis:7-alpine` | — | Message broker + Scaling metrics |

### Local Alpha Launch

To launch the full "Mission Control" stack locally:

1. **Prep your .env**: Ensure your root directory has a `.env` file with your `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL`.
2. **Fire it up**:

   ```bash
   docker-compose up --build
   ```

   This starts Redis, the FastAPI orchestrator, the GPU-ready physics worker, and the Nginx-served frontend.

3. **Verify**:

   - **Frontend**: http://localhost (Dashboard with Cyan LEDs)
   - **API Health**: http://localhost:8000/api/v1/health (returns `{"status": "healthy", ...}`)
   - **Worker Logs**: Look for `Heartbeat sent` in terminal output
   - **Lint Clean**: `pre-commit run --all-files` — all passed
   - **CI Gate**: GitHub Actions runs ruff on every push to `main`/`v2.5.1-DEV`
   - **Deploy**: Push to `main` triggers lint → Docker Hub (Worker + Autoscaler) + Vercel (Frontend)

### Queue Architecture (v2.3.0)

- **Queue Name**: `simhpc_jobs` (pending)
- **Inflight Key**: `simhpc_inflight` (currently processing)
- **Polling**: Every 15 seconds
- **Policy**: STOP on idle, START (resume) on job.
- **Idle Shutdown**: Individual pods **STOPPED** after `IDLE_TIMEOUT` (default 300s)
- **Persistence**: Network Volume mounted at `/workspace` preserves all physics state.
- **Safety**: `MAX_PODS=3`, budget caps enforced, Redis-persisted activity state
- **Warm Control**: `Wake GPU` button uses `/api/v1/admin/fleet/warm` for 90s wake-ups.

## v2.5.1: Structural Consolidation & Truth Alignment

- **Antigravity Mission Control**: Integrated native MCP skills for fleet management, secure deployments, and financial auditing directly from the AI agent.
- **Zero-Trust Security**: Transitioned to Infisical-based secret injection (`infisical run --`), eliminating local `.env` risks. All pod IDs, SSH keys, and server details are managed via Infisical.
- **Single Source of Truth**: Eliminated redundant files. All worker/scaling logic now lives in `services/worker/`.
- **Core Table**: `simulation_history` → `simulations` with backward-compatible view.
- **New Tables**: `certificates`, `documents`, `document_chunks`, `simulation_events`.
- **TypeScript Types**: `db.ts`, `audit.ts`, `api.ts`, `realtime.ts`, `view.ts` — exact schema mirror.
- **RLS**: Org-level and user-level row security with service-role bypass.
- **Backend Alignment**: API and worker updated to write to `simulations` table.
- **Frontend Alignment**: All components updated to use `SimulationRow` type.

### Antigravity Mission Control (v2.5.1)

SimHPC now supports a professional-grade, agent-led "Mission Control" via the Antigravity IDE/CLI. The following MCP skills are available:

*   **`simhpc-ops`**: Real-time fleet metrics (burn rate, active pods).
*   **`gcp-vault`**: Secure `gcloud` bridge with memory-sanitized secret injection.
*   **`deploy-guardian`**: Safety gate enforcing Ruff linting before Infisical-wrapped deployments.
*   **`resource-reaper`**: Automated financial shield that terminates stale GPU pods based on heartbeat telemetry.

**One-Command Workflow**:
- *"Guardian, safely deploy the API service."*
- *"Reaper, clean the fleet and give me a summary of today's simulation history."*

### Zero-Trust Secret Management

To ensure zero-leak security, SimHPC uses **Infisical** for all sensitive credentials:
- **Injection**: Use `infisical run -- [command]` to inject secrets at runtime.
- **Setup**: Run `infisical init` in the project root first to create `.infisical.json`. Verify with `infisical run -- cmd /c "set" | findstr SB_`.
- **Naming**: Infisical may use `SB_URL`/`SB_ANON_KEY` instead of `SUPABASE_URL`. The Supabase client checks both.
- **Managed Keys**: `RUNPOD_POD_ID`, `RUNPOD_SSH_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`.
- **Placeholder Pattern**: See `.env.example` for the required keys. Actual values never hit the disk.

#### Infisical Universal Auth (Machine Identity)

For CI/CD and automated workflows, use Universal Auth with a machine identity:

```bash
infisical login --universal-auth --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>"
```

- **Client ID**: Machine identity UUID (e.g., `55d8d8e8-dd7e-4d5c-b7d1-aec3e3a577f2`)
- **Client Secret**: Long-lived secret (stored in Infisical vault, never committed)
- **Environment Variables**: Alternatively set `INFISICAL_UNIVERSAL_CLIENT_ID` and `INFISICAL_UNIVERSAL_CLIENT_SECRET`

The machine identity **"RogWin"** is configured for this project.

## v2.4.1-DEV: Persistence & Conflict Resolution

- **Autosave System**: Debounced background sync of onboarding state to the FastAPI backend.
- **Cross-Device Resume**: Local cache (instant UI) + Backend source of truth (consistency).
- **Conflict Handling**: Versioned state updates prevent race conditions across multiple browser tabs.

## v2.4.0-DEV: Progressive Onboarding & Insight

- **Interactive Onboarding**: Guided product walkthrough with tooltips, modals, and event-triggered hints.
- **Conversion Intelligence**: Smart soft paywalls triggered by GPU suggestion or queue wait times.
- **Progress Tracking**: Persistent UI element tracking the "Value Journey."

## v2.3.0: Option C Autoscaler (On-Demand)

- **Advanced Metrics**: Scaling decisions now based on `pending` + `inflight` jobs for precision.
- **Stop/Resume**: Replaced termination with pod hibernation (STOP) to preserve state.
- **Wake Control**: Integrated Admin cockpit "Wake GPU" for proactive readiness.

## v2.1.1: Concurrent Workers

- **TelemetryPanel**: 240Hz solver streams.
- **OperatorConsole**: High-stakes engineering actions (Intercept, Clone, Boost, Certify).
- **SimulationLineage**: Visual ancestry and Flux Delta tracking.
- **GuidanceEngine**: Mercury AI-powered strategy recommendations.
- **Toast Notifications**: Sonner-based toast system with 6s/8s/10s duration tiers, cyan glow theme, `toast.promise()` pattern, and Supabase Realtime completion celebrations.
- **Simulation Detail Modal**: Clickable simulation rows with AI insights, physics metrics JSON, and PDF download.
- **Admin Analytics**: Real-time GPU pod health, simulation counts, and lead qualification tracking at `/admin/analytics`.
- **Custom Domain**: First-party auth via subdomain strategy (app + auth on same apex).

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Run Development Server

```bash
cd apps/frontend
npm install
npm run dev
```

### VS Code Debugging

The repository includes a pre-configured `.vscode/launch.json` for debugging the frontend:

1. Start the development server: `cd apps/frontend && npm run dev`.
2. Press `F5` in VS Code or select **"Launch Chrome (Frontend)"** from the Run and Debug sidebar.
    * **Port**: `59824`
    * **Web Root**: `apps/frontend`

### Build for Production

```bash
cd apps/frontend
npm run build
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for the complete Standard Operating Procedure.

### Quick Links

- **Frontend**: [https://simhpc.com](https://simhpc.com) — Vercel (production)
- **Worker Image**: `simhpcworker/simhpc-worker:latest` — Docker Hub
- **Autoscaler Image**: `simhpcworker/simhpc-autoscaler:latest` — Docker Hub
- **GitHub Actions**: https://github.com/NexusBayArea/lostbobo/actions
- **Vercel Dashboard**: https://vercel.com/<your-team>/simhpc/deployments

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
