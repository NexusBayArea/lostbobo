# SimHPC Development Guidelines

## Project Structure (v2.5.0)

We follow a strict monorepo structure to separate concerns and protect intellectual property.

- **`apps/frontend/`**: React Cockpit application (deployed to Vercel).
- **`services/api/`**: FastAPI orchestrator (Mercury AI integration, fleet management).
- **`services/worker/`**: Unified compute plane (Physics execution + Scaling + Reports).
- **`packages/`**: Shared libraries, SDKs, and internal tools.
- **`docs/`**: Centralized documentation.
- **`legacy_archive/`**: Safely archived legacy artifacts.

## Database Schema (v2.5.0)

The core database table is `simulations` (formerly `simulations`). A backward-compatible view named `simulations` exists for legacy code.

**Key columns**: `id`, `user_id`, `org_id`, `job_id`, `scenario_name`, `status`, `prompt`, `input_params`, `result_summary`, `gpu_result`, `audit_result`, `hallucination_score`, `report_url`, `pdf_url`, `certificate_id`, `error`, `created_at`, `updated_at`.

**Supporting tables**: `certificates`, `documents`, `document_chunks`, `simulation_events`.

**TypeScript types** live in `apps/frontend/src/types/`:
- `db.ts` — Exact Supabase schema mirror
- `audit.ts` — Audit + verification types
- `api.ts` — API response contracts
- `realtime.ts` — Supabase realtime partial update types
- `view.ts` — UI view models + mapper

**Migration file**: `supabase/migrations/002_beta_schema_normalization.sql`

## Best Practices

1. **Isolation**: Maintain clear boundaries between apps and services. Do not cross-import code directly between them; use shared `packages/` if necessary.
2. **Environment**: Store all secrets in `.env` (root or per-service). Never commit `.env` files. For Vercel, inject `VITE_` vars via Dashboard or `vercel-envs` in workflow. For GitHub Pages, pass secrets in the `env:` block of the build step.
3. **Documentation**: Keep `README.md` and `ARCHITECTURE.md` updated with any structural changes.
4. **Consistency**: Follow existing naming conventions (kebab-case for folders).
5. **Cleanliness**: Regularly clean up temporary files, build artifacts, and logs.
6. **Git Security**: Always use a standard `.gitignore` file (not `_gitignore`). Never commit `.env` or any file containing secrets. If a secret is accidentally committed, rotate it immediately and untrack the file using `git rm --cached <file>`.

## Deployment Notes

- **Vercel is Production Primary**: Handles `VITE_` env injection, SPA routing, and CSP for Stripe/Supabase automatically.
- **GitHub Pages is Backup/Staging**: Requires manual env var injection in workflow and CSP meta tag in `index.html`.
- **Known Issue (v1.6.0-ALPHA)**: GitHub Pages fails with "Supabase Credentials Missing" and CSP violations. Fix: add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` to GitHub Secrets and pass them in the build step.
- **Custom Domain (v2.3.0)**: App at `simhpc.com`, Auth at `auth.simhpc.com`. DNS: A `@ → 76.76.21.21`, CNAME `auth → [project-ref].supabase.co`. Update Supabase Redirect URLs and Stripe JS Origins after domain is live.
- **Double-Key Strategy (v2.3.0)**: Frontend uses `VITE_SUPABASE_ANON_KEY` (RLS enforced). Worker uses `SUPABASE_SERVICE_ROLE_KEY` (RLS bypassed) for telemetry and artifact sync.
- **Stable RunPod Proxy (v2.3.0)**: Always use the RunPod HTTP Proxy URL (see `INFRASTRUCTURE.md`) for `VITE_API_URL` to prevent "Offline" errors caused by IP changes.
- **Google Auth (v2.3.0)**: Google Client ID `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`. Redirects must point to `https://simhpc.com/api/auth/callback/google`.
- **Local Docker Stack (v2.5.0)**: `docker-compose up --build` starts Redis, API, Worker, Autoscaler, and Nginx-served Frontend. Verify with `GET http://localhost:8000/api/v1/health`.
- **Vercel ≠ Docker (v2.5.0)**: `docker-compose.yml` `build.args` only apply to Docker builds. Vercel runs `vite build` directly and reads from its own Dashboard env vars. You must set `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`, and `VITE_STRIPE_PUBLISHABLE_KEY` in Vercel → Settings → Environment Variables, then redeploy.
- **Credential Policy (v2.5.0)**: Never commit pod IDs, SSH keys, or IP addresses to tracked `.md` files. Use Infisical to manage `RUNPOD_POD_ID` and `RUNPOD_SSH_KEY` for runtime injection.
- **Docker Hub Auth (v2.5.0)**: All GitHub workflows use `DOCKER_ACCESS_TOKEN` piped via `--password-stdin`. Requires `DOCKER_ACCESS_TOKEN` and `DOCKER_USERNAME` secrets in GitHub repo.
- **Infisical Secret Injection (v2.5.0)**: All high-privilege secrets (GCP, RunPod, Supabase) are injected at runtime via `infisical run --`. Local `.env` files are deprecated. `RUNPOD_POD_ID` and `RUNPOD_SSH_KEY` are managed exclusively via the Infisical vault.
- **Infisical Setup**: Run `infisical init` in the project root to create `.infisical.json` and link to the SimHPC vault. Verify with `infisical run -- cmd /c "set" | findstr SB_`. Secrets may use `SB_URL`/`SB_ANON_KEY` naming instead of `SUPABASE_URL`.
- **Supabase Client Naming**: `src/lib/supabase.ts` checks both `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` and `SB_URL`/`SB_ANON_KEY` for Infisical compatibility.
- **Health Endpoint (v2.5.0)**: `GET /api/v1/health` probes Redis (`ping()`) and Supabase (`worker_heartbeat` query). Returns `200 healthy` or `503 degraded` with per-service status.
- **Worker Heartbeat (v2.5.0)**: `send_heartbeat()` fires at the top of every `while True` cycle, not just when jobs are active. This keeps the "Sim Worker" Dashboard LED consistently Cyan.

## Toast System (v2.3.0)

- **Library**: sonner (`^2.0.7`)
- **Mount Point**: `<Toaster />` in `src/App.tsx`
- **Config**: 6s default, 8s success, 10s error, 350px min-width, bottom-right, cyan theme `#00f2ff`, rounded corners
- **Pattern**: `toast.promise()` for submission; `toast.loading()` → `toast.success/error()` with same ID for other async ops
- **CSS**: Overrides in `src/index.css` for dark terminal styling
- **Realtime**: `useSimulationUpdates` hook subscribes to Supabase `simulations` table — triggers 10s completion toast at top-center

## Interactive Onboarding (v2.4.1-DEV)

### Admin RBAC (v2.5.0)

- **ProtectedRoute**: `src/components/auth/ProtectedRoute.tsx` wraps `/admin/analytics` with `requireAdmin`.
- **Admin Check**: `useAuth().isAdmin` — checks `user.app_metadata.role === 'admin'` OR `user.email === 'arche@simhpc.com'`.
- **Setup**: In Supabase Console → User Profile → Raw App Metadata, add `{"role": "admin"}` to your account.
- **Backend**: Admin endpoints still protected by `X-Admin-Secret` header (`verify_admin` in `api.py`).

### Real-Time Telemetry (v2.5.0)

- **Hook**: `src/hooks/useSimulations.ts` — subscribes to `simulations` table via Supabase Realtime.
- **Telemetry Extraction**: Reads `progress`, `thermal_drift`, `pressure_spike` from `result_summary` / `gpu_result` JSONB.
- **Integration**: `ActiveSimulations.tsx` uses this hook to drive live progress rings and thermal drift warnings.
- **Companion**: `useSimulationUpdates.ts` handles toast notifications on status change; `useSimulations.ts` drives the telemetry UI.

### Guidance Engine (v2.5.0)

- **Prompt Template**: `GUIDANCE_PROMPT_TEMPLATE` in `api.py` — Chain-of-Thought prompt for Mercury AI.
- **Endpoint**: `POST /api/v1/alpha/generate-report/{job_id}` — requires auth, fetches sim data, calls Mercury AI, persists `ai_report` in `result_summary`.
- **Chain of Truth**: Worker generates drift data → API orchestrates Mercury AI → Frontend displays report via `useSimulations`.

### Admin Dashboard (v2.5.0)

- **Page**: `src/pages/admin/AdminAnalyticsPage.tsx` — sidebar layout with expandable nav (Fleet Analytics, User Management, Stripe Revenue, AI Prompts).
- **Fleet Metrics**: `supabase/functions/get-fleet-metrics/index.ts` — Supabase Edge Function. Calculates active pods and hourly spend server-side. Admin-only via `app_metadata` check. Auto-creates billing alerts when spend > $10/hr (deduplicated per hour).
- **Security**: RunPod hourly rate and `MAX_CONCURRENT_JOBS` logic stays on the server. Frontend receives pre-computed metrics only.
- **Deploy**: `supabase functions deploy get-fleet-metrics` — requires `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` as function secrets.

### Platform Alerts + Panic Button (v2.5.0)

- **Schema**: `supabase/migrations/004_platform_alerts.sql` — `platform_alerts` table with Realtime. Types: `billing`, `thermal`, `system`. Severities: `info`, `warning`, `critical`.
- **Alert Center**: Sidebar widget in `AdminAnalyticsPage` subscribes to `platform_alerts` via Supabase Realtime. Toast notifications on INSERT.
- **Panic Button (Edge Function)**: `supabase/functions/trigger-panic-shutdown/index.ts` — terminates all RunPod pods, logs critical alert. Admin-only. Deploy: `supabase functions deploy trigger-panic-shutdown`.
- **Panic Button (Python)**: `services/skills/panic_button.py` — CLI/MCP skill script. Same termination logic. Requires `RUNPOD_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
- **Safety**: UI requires double `window.confirm()` before triggering. Button shows loading state during execution.

### Persistence & Sync Strategy
1.  **Versioned Autosave**: All state updates increment a `version` counter.
2.  **Conflict Resolution**: On `409 Conflict`, the frontend must discard local state and hydrate from the server response.
3.  **Local First**: Use `localStorage` for instant UI resume before the backend sync completes.
4.  **Debounced Sync**: Batch rapid UI changes (e.g., parameter tweaks) into a single 1s debounced save call.
5.  **Periodic Polling**: Poll every 30s to keep multiple devices in sync without complex WebSockets.

### Key Design Principles
1.  **Show, don’t tell**: Use active highlights and tooltips.
2.  **One action per step**: Minimize cognitive load.
3.  **Immediate feedback loops**: Confirm completion of each step visually.
4.  **Delay monetization**: Only show paywalls after value (results) is demonstrated.
5.  **Friction as a lever**: Use queue wait times to drive GPU upgrades.

## Tooling

- **Antigravity MCP Skills (v2.5.0)**:
  - **`simhpc-ops`**: Python-based tool (`services/skills/fleet_tool.py`) that fetches real-time fleet burn rate and active pod counts from Supabase Edge Functions.
  - **`simhpc-secrets`**: Python-based tool (`services/skills/secret_sync.py`) that wraps `gcloud` to sync production secrets from GCP Secret Manager to `.env.production`.
  - **`gcp-vault`**: Secure GCP bridge (`services/skills/secure_gcp_tool.py`) that prefixes `gcloud` commands with `infisical run --` for zero-leak secret management.
  - **`deploy-guardian`**: Deployment safety gate (`services/skills/deployment_guardian.py`) that enforces Ruff linting before executing secure Infisical-wrapped GCP deployments.
  - **`resource-reaper`**: Financial Shield (`services/skills/resource_reaper.py`) that cross-references RunPod and Supabase heartbeats to terminate stale "Zombie" GPU instances (>15 mins idle).
  - **`panic-button`**: Emergency shutdown (`services/skills/panic_button.py`) — terminates all RunPod pods, logs critical alert to `platform_alerts`.
  - **Registration**: Configured in `antigravity.config.json` in the workspace root.
- **PowerShell**: Used for local environment management.
- **Docker Compose**: Used for local orchestration of services.
- **Vite**: Frontend development server (Default Port: `59824`).
- **VS Code**: Recommended IDE. Repository includes `.vscode/launch.json` for frontend debugging.
- **Vercel**: Primary hosting and deployment platform for the frontend.
- **Git**: Primary version control. Do not stage/commit unless requested. Ensure `.gitignore` is correctly named with a leading dot.
- **Ruff**: Python linter. Run `python -m ruff check services/` before committing. All checks must pass (0 errors). Config uses default rules (E, F, W).
- **Pre-Commit Framework**: `pip install pre-commit` + `.pre-commit-config.yaml`. Run `pre-commit install` after cloning. Runs `ruff --fix` + `ruff-format` on every commit. Run `pre-commit run --all-files` to check the entire codebase.
- **GitHub Actions CI**: `.github/workflows/lint.yml` runs `ruff check` and `ruff format --check` automatically on push to `main`/`v2.5.0-DEV` and on PRs.
- **Unified Deploy Pipeline**: `.github/workflows/deploy.yml` — lint gate → Docker Hub (Worker + Autoscaler) + Vercel (Frontend). Push to `main` triggers full pipeline.
- **RunPod Auto-Updater**: `services/worker/pull_and_restart.sh` + cron (`*/5 * * * *`) pulls latest `simhpc-worker:latest` and restarts on change. Keeps GPU fleet in sync with GitHub.
- **Pre-Commit Hook**: `.git/hooks/pre-commit` blocks local commits if ruff fails. Run `chmod +x .git/hooks/pre-commit` after cloning.
- **Security Audit**: Root `.env` must remain untracked. Use `.env.example` for templates.

# AI Project Guardrails

## 1. Critical File Naming & Security

- **FORBIDDEN**: Never name the ignore file `_gitignore`. It MUST be exactly `.gitignore`.
- **ACTION**: If `_gitignore` is detected, rename it to `.gitignore` immediately before any git commands.
- **PROHIBITION**: Never commit `.env` or `.env.local` files. Use `git rm --cached .env` if accidentally tracked.

## 2. Structural Separation (The "Great Wall")

- **Frontend (Vercel)**: Only React/Vite/Next.js code. No Python, no GPU orchestration logic.
- **Backend (RunPod/Supabase)**: All heavy physics, Mercury AI, and DB admin logic.
- **Communication**: Frontend connects to Backend ONLY via the RunPod HTTP Proxy URL: `https://[POD_ID]-8000.proxy.runpod.net`.

## 3. Environment Variable Policy

- **Vercel/Frontend**: Only use `VITE_` or `NEXT_PUBLIC_` prefixes for non-sensitive keys (e.g., Supabase Anon Key).
- **RunPod/Worker**: High-privilege keys (e.g., `SUPABASE_SERVICE_ROLE_KEY`, `STRIPE_SECRET_KEY`) live here only.
- **Double-Key Strategy**: Use the Anon Key for client reads; use the Service Role Key for Worker writes.

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
