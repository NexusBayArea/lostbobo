# 🤖 AI Directives for SimHPC Development

> **Version**: 3.1.0 (April 12, 2026)
> **Priority**: CRITICAL / MANDATORY
> **Status**: ENFORCED (Local Build Authority)

This document defines the strict operational boundaries and security protocols for AI assistants working on the SimHPC codebase. All development actions must conform to these directives without exception.

---

## 🏗️ 1. Strict Repository Separation & Containerization

SimHPC operates as two decoupled environments to protect intellectual property and ensure runtime stability.

### Frontend (Client Plane)

- **Platform**: Vercel (Production)
- **Stack**: React, Vite, Next.js, TypeScript.
- **Performance**:
  - **Chunk Splitting**: Must split vendor chunks into logical groups (React, Supabase, State, UI) in `vite.config.ts` to keep individual chunks under 1000kB.
  - **Lazy Loading**: Use `React.lazy()` and `Suspense` for route-level code splitting.

### Backend (Compute Plane - v2.7 Unified Strategy)

- **Platform**: RunPod / Supabase (Dedicated GPU Pods)
- **Architecture**: **UNIFIED CONTAINER** (`simhpc-unified`).
- **Standard**: API, Worker, and Autoscaler MUST run in a single container supervised by `supervisord` + `tini`.
- **Constraint**: DO NOT build or deploy separate images for `worker`, `api`, or `autoscaler`. This ensures atomic deployments and simplified service discovery.
- **Entrypoint**: `/usr/bin/tini -- /start.sh`
- **Port**: Standardized on **8080** for all external traffic.

---

## 🛠️ 2. Local Build Authority (LBA)

> [!IMPORTANT]
> **SIMHPC USES A LOCAL BUILD ONLY STRATEGY.**
Exactly ONE system builds images: The **Local Machine**. GitHub Actions (CI) ONLY validates code and configuration.

### CI Restriction

- The `.github/workflows/` directory must **NOT** contain workflows that perform `docker build`, `docker push`, or registry logins.
- CI is restricted to linting (`ruff`), basic validation, and structure checks.

### Automated Sanitization

- CI must use `uvx` to run tools in isolated sandboxes to avoid "Externally Managed Environment" errors.
- Any "deployment fix" requested must be implemented in the local `Dockerfile` or `build.sh`, never in the CI YAML.

### Deployment Decoupling

- Deployment to RunPod is a manual or explicit "Release" action triggered from the local machine, not an automatic side effect of a `git push`.

---

## 🛡️ 3. Zero-Tolerance Git Security

Security of the repository and its secrets is paramount.

- **Naming Convention**: The Git ignore file **MUST** be named exactly `.gitignore`.
- **Action**: If a file named `_gitignore` is detected, rename it to `.gitignore` immediately.
- **Secret Protection**: You are **strictly forbidden** from staging or committing the following:
  - `.env`, `.env.local`, `.env.production`
  - Any file containing `SUPABASE_SERVICE_ROLE_KEY`, `SIMHPC_API_KEY`, or `STRIPE_SECRET_KEY`.
- **Cleanup**: If a secret is accidentally committed, you must immediately run `git rm --cached <file>` and notify the user to rotate the keys.

---

## 🔑 4. Environment Variable Scoping

Variable access is strictly tiered based on the plane of execution.

| Scope | Allowed Variable Types | Example Keys |
| :--- | :--- | :--- |
| **Frontend** | Public/Browser-prefixed only | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON`, `VITE_API_URL` |
| **Backend** | High-privilege/System keys | `SUPABASE_SERVICE_ROLE_KEY`, `RUNPOD_API_KEY` |

> [!CAUTION]
> **NEVER** reference `SUPABASE_SERVICE_ROLE_KEY` or `RUNPOD_API_KEY` within the frontend directory or its build configuration.

---

## 🤝 5. Architectural Handshake

The communication between the Frontend and Backend must follow a standardized API pattern.

- **Protocol**: HTTPS / Secure WebSockets.
- **Enforcement**: The Vercel frontend communicates with the backend **ONLY** via:
  - Standardized JSON API endpoints.
  - Stable **RunPod HTTP Proxy URLs** (to handle dynamic pod IPs).
- **Prohibited**: Do not attempt to run backend Python scripts or direct database admin connections directly from Vercel edge functions.

---

## ⚙️ 6. Core Architecture (v2.7)

### Port Configuration

- **Primary**: 8080 (API)
- **Dev**: 8888 (Jupyter only)
- **Removed**: 8000 (backup port eliminated)

### Source of Truth

- **Supabase**: Canonical state (jobs, simulations)
- **Redis**: Ephemeral cache only (to be removed in v2.7 migration)

### Docker Structure

```yaml
docker/
  images/
    Dockerfile.unified    ← Primary
  scripts/
    start.sh
  compose/
    docker-compose.yml
```

Build Authority: Handled by `scripts/build.sh` on the local machine.

---

## 📋 7. Architectural Mandates (Enforced)

1. **Atomic Reservation**: All new requests MUST use `reserve_idempotency` (`SETNX`) to prevent race conditions during job creation.
2. **O(1) Concurrency**: Concurrency checks MUST use the `user:{user_id}:active_runs` counter; manual scans of the `job:*` pattern are strictly forbidden.
3. **Closed-Loop Counters**: Any process that increments an active job counter MUST ensure it is decremented in a `finally` block or via a dedicated reaper service.
4. **Self-Registration**: Workers MUST register with `workers:active` on startup.
5. **Heartbeat Loop**: Workers MUST update `worker:heartbeat:{worker_id}` every 10s with a 30s TTL.
6. **Single Source of Truth**: Supabase is the authority for all persistent states. Redis is for caching only.
7. **Zero Blocking**: All external service calls MUST be non-blocking (`await`).

### Deployment Rules

- **podReset**: Use `podReset` (not `podRestart`) for CI/CD deployments to force fresh image pull.
- **SHA Tagging**: Always use `git rev-parse --short HEAD` tags locally, never deploy `latest` in production.
- **Manual Trigger**: Deployment is triggered manually via local scripts (`scripts/deploy_to_runpod.py` or similar).

---

## 🏎️ 8. Stateless Reasoning & Context Hardening (SRCH)

To maintain stability and prevent "Mercury" crashes, the following operational mandates are in effect:

### Context Hardening

- **Hard Token Cap**: Output and input must be managed to stay below **100,000 tokens**.
- **Pre-flight Estimation**: Before processing large files or logs, estimate token impact.
- **Aggressive Truncation**: If context approaches the limit, truncate non-essential history or logs immediately.

### Stateless Reasoning Pattern

- **LLM as Compute**: Treat the LLM as a stateless reasoning node. The source of truth for "state" is external (DB, Redis, or `progress.md`).
- **Sliding Window Memory**: Do not rely on full conversation history. Use a [System Prompt] + [Compressed Summary] + [Last 5-10 Turns] pattern.
- **Log Suppression**: Never dump raw execution traces or full logs into the context. Use structured summaries (errors + key events only).

### State Synchronization

- **Mandatory Updates**: For long-running or multi-step tasks, update `progress.md` after every significant architectural change or milestone.
- **Sync Habit**: "Summarize history → Update progress.md → Clear/Summarize history".

---

## 🌐 9. Environment Normalization Layer (ENL)

To ensure platform portability and prevent CI/CD breakage due to variable naming drift, SimHPC enforces a strict **Environment Normalization Layer**.

### Architectural Constraints

- **Infra Isolation**: The infrastructure provides a generic secret bundle prefixed with `SB_*` (e.g., `SB_URL`, `SB_TOKEN`).
- **Normalized Schema**: The application logic **MUST NOT** reference `SB_*` variables directly. It must use internal canonical names defined in `app/core/config.py`.
- **Mapping Authority**: `app/core/env.py` is the only file authorized to map infrastructure variables to internal schema.

### Internal Contract

| Internal Key | Source (Infra) | Purpose |
| :--- | :--- | :--- |
| `APP_URL` | `SB_URL` | Core Service URL (e.g. Supabase REST) |
| `DATA_URL` | `SB_DATA_URL` | Data persistence endpoints |
| `API_TOKEN` | `SB_TOKEN` | High-privilege service access token |
| `JWT_SECRET` | `SB_JWT_SECRET` | Token signing and verification |
| `SECRET_KEY` | `SB_SECRET_KEY` | Internal application encryption key |

> [!CAUTION]
> **NEVER** use `os.getenv("SB_*")` outside of `app/core/env.py`. All components must consume configuration through the `app.core.config.settings` object.

---

> [!IMPORTANT]
> Failure to adhere to these directives may result in credential exposure or critical architectural failure. **Safety first.**
