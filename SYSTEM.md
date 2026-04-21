# SimHPC System Source of Truth
> **Version**: 3.0.0 (April 11, 2026)  
> **Authority**: PRIMARY (Overrides all other .md files)  
> **Status**: ENFORCED for all AI Models and CLI Tools

---

## 🔒 3. Local Build Authority Protocol (v3.0.0)

To prevent "Layer Stacking" and CI loops, the system follows these invariants:

- **Local Authority**: Images are built exclusively on the local machine using the Git SHA as a tag via `scripts/build.sh`.
- **Zero-Build CI**: GitHub Actions (`ci-validation.yml` and `orchestrator.yml`) MUST NOT contain `docker login` or `docker build` steps.
- **Port 8080 (LOCKED)**: The unified production endpoint is 8080. All health checks, API insights, and proxy configurations must target this port. 
- **UVX Isolation**: CI linting tools must run via `uvx` to prevent system-level Python environment conflicts.

---

## Core Architecture & Folder Mapping

### Frontend (Client Plane)
- **Location**: Root `/frontend` or `/src`
- **Hosting**: Vercel
- **Stack**: React, Vite, TypeScript, Tailwind CSS
- **Rule**: No heavy Python or GPU logic allowed here

### Backend (Compute Plane)
- **Location**: `/app`
- **Hosting**: RunPod (GPU)
- **Stack**: Python 3.11+, FastAPI, NVIDIA CUDA
- **Execution**: `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080`

### Directory Structure
```
/workspace
├── app/                  # Backend (Python)
│   ├── api.py            # FastAPI orchestrator
│   ├── worker.py         # Physics worker
│   ├── autoscaler.py     # GPU fleet management
│   └── core/             # Auth, Job Queue, Supabase
├── frontend/             # Frontend (React)
├── scripts/              # Deployment scripts
├── Dockerfile.unified    # Production build
└── requirements.txt      # Python deps
```

---

## AI Operational Guardrails

1. **Git Security**: Ignore file MUST be `.gitignore`, not `_gitignore`
2. **Secret Protection**: Never commit `.env`, service role keys, or API tokens
3. **Infisical Standard**: Use `infisical run --` for secret injection
   - **Naming**: `SB_` prefix for Supabase (e.g., `SB_URL`, `SB_JWT_SECRET`)
4. **Data Integrity**: **Supabase is source of truth** - use SQL RPC, not Redis counters

---

## Network & Ports

| Port | Purpose |
|------|---------|
| 8080 | Primary API (main traffic, batch flush) |
| 8000 | Backup/Redundant API |
| 8888 | Jupyter/Development only |

---

## Cognitive Design: O-D-I-A-V Loop

All Mission Control UI development follows:
- **Observe**: Live telemetry & fleet status
- **Detect**: Anomaly detection & flags
- **Investigate**: Historical drill-down
- **Act**: Intervention commands (Intercept, Clone, Boost)
- **Verify**: Physics sign-off & AI certification

---

## Change Management

All changes logged in `CHANGELOG.md` (Keep a Changelog format). SemVer versioning.

---

## Current Pod ID (Dynamic)

Get from Infisical:
```bash
infisical secrets get RUNPOD_ID --plain
```
