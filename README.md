# SimHPC Mission Control Cockpit

The SimHPC Frontend is **LIVE** and accessible at [https://simhpc.com](https://simhpc.com).

This is the public-facing repository for the SimHPC Mission Control Cockpit, a premium interface for aerospace and thermal engineering simulations.

## Architecture (v2.5.0)

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
| API | `simhpcworker/simhpc-api:v2.5.0` | `Dockerfile.api` | FastAPI orchestrator (Mercury AI integration) |
| GPU Worker | `simhpcworker/simhpc-worker:v2.5.0` | `Dockerfile.worker` | Unified Physics + Metrics + Reports |
| Autoscaler | `simhpcworker/simhpc-autoscaler:v2.5.0` | `Dockerfile.autoscaler` | Option C: On-demand + Network Volume |
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
   - **CI Gate**: GitHub Actions runs ruff on every push to `main`/`v2.5.0-DEV`
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

## v2.5.0: Structural Consolidation & Truth Alignment

- **Antigravity Mission Control**: Integrated native MCP skills for fleet management, secure deployments, and financial auditing directly from the AI agent.
- **Zero-Trust Security**: Transitioned to Infisical-based secret injection (`infisical run --`), eliminating local `.env` risks. All pod IDs, SSH keys, and server details are managed via Infisical.
- **Single Source of Truth**: Eliminated redundant files. All worker/scaling logic now lives in `services/worker/`.
- **Core Table**: `simulation_history` → `simulations` with backward-compatible view.
- **New Tables**: `certificates`, `documents`, `document_chunks`, `simulation_events`.
- **TypeScript Types**: `db.ts`, `audit.ts`, `api.ts`, `realtime.ts`, `view.ts` — exact schema mirror.
- **RLS**: Org-level and user-level row security with service-role bypass.
- **Backend Alignment**: API and worker updated to write to `simulations` table.
- **Frontend Alignment**: All components updated to use `SimulationRow` type.

### Antigravity Mission Control (v2.5.0)

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
npm install
npm run dev
```

### VS Code Debugging

The repository includes a pre-configured `.vscode/launch.json` for debugging the frontend:

1. Start the development server: `npm run dev`.
2. Press `F5` in VS Code or select **"Launch Chrome (Frontend)"** from the Run and Debug sidebar.
    * **Port**: `59824`
    * **Web Root**: `apps/frontend`

### Build for Production

```bash
npm run build
```

## Deployment

The frontend is automatically deployed to Vercel upon merging into the main branch of the `lostbobo` repository.

- **Primary**: [https://simhpc.com](https://simhpc.com) — Vercel (production)
- **Backup**: [https://NexusBayArea.github.io/lostbobo](https://NexusBayArea.github.io/lostbobo) — GitHub Pages (staging/debug only)

### Environment Variables (Critical)

Vite requires `VITE_` prefixed variables to be available **at build time**. They are hardcoded into the JavaScript bundle during `npm run build`.

| Variable | Purpose | Source |
| :--- | :--- | :--- |
| `VITE_SUPABASE_URL` | Supabase project URL | Supabase Dashboard |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | Supabase Dashboard |
| `VITE_API_URL` | Backend API endpoint | RunPod API container |

#### Vercel (Automatic)

Vercel injects these via the Dashboard or `vercel-action` workflow. **Never use local .env files for production secrets.** Ensure `.gitignore` is correctly named with a leading dot to prevent local `.env` files from being tracked.

> **Important**: Vercel and Docker use separate env var systems. Docker `build.args` in `docker-compose.yml` do not transfer to Vercel. You must explicitly set these in **Vercel → Project → Settings → Environment Variables** for the Production environment:
>
> | Variable | Required |
> | :--- | :--- |
> | `VITE_SUPABASE_URL` | Yes |
> | `VITE_SUPABASE_ANON_KEY` | Yes |
> | `VITE_API_URL` | Yes |
> | `VITE_STRIPE_PUBLISHABLE_KEY` | Yes |
>
> Then trigger a **redeploy** — Vite bakes these at build time; adding them after deploy has no effect until rebuild.

### Strategic Vercel Best Practices

#### 1. The "Double-Key" Strategy

- **Frontend**: Uses `VITE_SUPABASE_ANON_KEY` to allow users to authenticate and read their own data.
- **RunPod Worker**: Uses `SUPABASE_SERVICE_ROLE_KEY` to perform administrative database updates, bypassing Row Level Security (RLS) for high-frequency physics telemetry.

#### 2. Stable RunPod Handshake

If the Sim Worker shows as "Offline," it is likely due to an IP change after a restart.

- **Action**: Use the **RunPod HTTP Proxy URL** in `VITE_API_URL` instead of a direct IP.
- **Why**: Direct IPs change on pod restart. The proxy URL is stable.
- **Pod ID**: See private `INFRASTRUCTURE.md` (excluded from git).
- **Connection**: See private `INFRASTRUCTURE.md` — pod-specific details are rotated per deployment.
- **SSH Command**: See private `INFRASTRUCTURE.md`.

- **CORS**: Ensure `ALLOWED_ORIGINS` in your FastAPI backend includes your specific Vercel domain. Never use `*` in production.

#### 3. Google Cloud Console Configuration

For Google One Tap and Sign-In to function on Vercel:

- **Authorized JavaScript Origins**: Add `https://simhpc.com` and your Vercel preview URLs.
- **Authorized Redirect URIs**: Add `https://simhpc.com/api/auth/callback/google`.

#### GitHub Pages (Manual — Required)

GitHub Pages is static hosting and cannot read secrets at runtime. You must:

1. Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to **Repo → Settings → Secrets → Actions**
2. Pass them in the workflow build step:

```yaml
- name: Build
  run: npm run build
  env:
    VITE_SUPABASE_URL: ${{ secrets.VITE_SUPABASE_URL }}
    VITE_SUPABASE_ANON_KEY: ${{ secrets.VITE_SUPABASE_ANON_KEY }}
```

#### Known Issue: GitHub Pages CSP & Stripe

`github.io` domains enforce stricter Content-Security-Policy and block third-party cookies. If using GitHub Pages, add this to `index.html`:

```html
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; connect-src 'self' https://*.supabase.co https://*.stripe.com; script-src 'self' 'unsafe-inline' https://*.stripe.com; style-src 'self' 'unsafe-inline';">
```

**Recommendation**: Use **Vercel as Production Primary** — it handles Auth, Stripe, and SPA routing natively.

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
