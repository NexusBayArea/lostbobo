# SimHPC Development Guidelines

## Project Structure (v2.5.1)

We follow a strict monorepo structure to separate concerns and protect intellectual property. All legacy components from `apps/frontend` have been consolidated into the root `src/` directory.

- **`src/`**: React Cockpit application (Unified root source).
- **`services/api/`**: FastAPI orchestrator (Mercury AI integration, fleet management).
- **`services/worker/`**: Unified compute plane (Physics execution + Scaling + Reports).
- **`packages/`**: Shared libraries, SDKs, and internal tools.
- **`docs/`**: Centralized documentation.
- **`legacy_archive/`**: Consolidated legacy artifacts and deprecated `apps/frontend` submodule.

## Database Schema (v2.5.1)

The core database table is `simulations`. A backward-compatible view named `simulations` exists for legacy code.

**Key columns**: `id`, `user_id`, `org_id`, `job_id`, `scenario_name`, `status`, `prompt`, `input_params`, `result_summary`, `gpu_result`, `audit_result`, `hallucination_score`, `report_url`, `pdf_url`, `certificate_id`, `error`, `created_at`, `updated_at`.

**Supporting tables**: `certificates`, `documents`, `document_chunks`, `simulation_events`, `platform_alerts`.

**TypeScript types** live in `src/types/`:
- `db.ts` — Exact Supabase schema mirror
- `audit.ts` — Audit + verification types
- `api.ts` — API response contracts
- `realtime.ts` — Supabase realtime partial update types
- `view.ts` — UI view models + mapper

## Best Practices

1. **Isolation**: Maintain clear boundaries between apps and services.
2. **Environment**: Store all secrets in `.env`. Never commit `.env` files.
3. **Documentation**: Keep `README.md` and `ARCHITECTURE.md` updated with any structural changes.
4. **Consistency**: Follow existing naming conventions (kebab-case for folders).
5. **Cleanliness**: Regularly clean up temporary files, build artifacts, and logs.
6. **Git Security**: Always use a standard `.gitignore` file. Never commit `.env` or any file containing secrets.

## Deployment Notes

- **Vercel is Production Primary**: Handles root `src/` build and deployment automatically via native GitHub integration.
- **RunPod HTTP Proxy (v2.3.0)**: Always use the RunPod HTTP Proxy URL for `VITE_API_URL` to prevent "Offline" errors.
- **Google Auth (v2.5.1)**: Google Client ID `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`.
- **Infisical Setup**: Run `infisical init` in the project root. Secrets may use `SB_URL`/`SB_ANON_KEY` naming.
- **Supabase Client Naming**: `src/lib/supabase.ts` checks both `VITE_SUPABASE_URL` and `SB_URL` for compatibility.

## Mission Control Dashboards (v2.5.1)

- **Admin Analytics**: `src/pages/admin/AdminAnalyticsPage.tsx` — Protected by `requireAdmin`. Features Fleet HUD, Panic Button, and Scaling Events.
- **Alpha Control Room**: `src/pages/AlphaControlRoom.tsx` — Expert-level cockpit with O-D-I-A-V loop components (Telemetry, Lineage, Console).
- **Active Telemetry**: Driven by `useSimulations` hook with Supabase Realtime synchronization.

# AI Project Guardrails

## 1. Critical File Naming & Security
- **FORBIDDEN**: Never name the ignore file `_gitignore`. It MUST be exactly `.gitignore`.
- **ACTION**: If `_gitignore` is detected, rename it to `.gitignore` immediately.

## 2. Structural Separation
- **Frontend**: Root `src/` directory. No Python or GPU logic.
- **Backend**: `services/` directory. Handles all physics and AI orchestration.

## 3. Environment Variable Policy
- **Build Time**: `VITE_` prefixed variables are injected at build time.
- **Zero-Trust**: Administrative tasks MUST use `infisical run --` for secret injection.
