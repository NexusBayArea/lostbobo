---
name: frontend
description: Production-grade Frontend Deployment Flow (v2.7) with Hardening Standards.
version: 2.7.0
license: MIT
compatibility: opencode
---

# Frontend Deployment Skill (v2.7)

This skill synchronizes the **Frontend Deployment Flow** with the **v2.6.8 Production Hardening** standards (Port 8080 unification, `uv` dependency management, and documentation consolidation).

## 🏗️ Unified Repository Structure
Following the "Zero-Drift" mandate, the repository is a high-performance monorepo with logical separation but deployment synchronization.

```text
/simhpc-unified
├── .github/workflows/    # [LOCKED] CI/CD Orchestration
├── app/                  # [PARTIAL] Backend Logic
│   ├── api/routes/       # (Allowed) API Endpoints
│   ├── core/             # [LOCKED] Auth & Job Queue
│   └── services/worker/  # [LOCKED] Physics & Autoscaling
├── frontend/             # (Allowed) Vite/React Cockpit
│   ├── src/              # O-D-I-A-V Components
│   └── public/           # Static Assets
├── scripts/              # [LOCKED] System Guards & simhpc.sh
├── pyproject.toml        # [LOCKED] uv Project Config (Truth)
├── uv.lock               # [LOCKED] Deterministic Lockfile
├── README.md             # Pillar 1: Overview
├── CHANGELOG.md          # Pillar 2: Version History
└── PROGRESS.md           # Pillar 3: Milestone Tracking
```

## ✅ 1. Terminal AI Scope (The "No-Fly Zone")
To prevent infrastructure drift, the AI is restricted to the **"Logic Layers"** only.

| Domain | Access | Target Path |
| :--- | :--- | :--- |
| **Frontend UI** | ✅ READ/WRITE | `frontend/` |
| **API Logic** | ✅ READ/WRITE | `app/api/routes/` |
| **Data Models** | ✅ READ/WRITE | `app/models/` |
| **Infra/Orchestration** | ❌ FORBIDDEN | `.github/`, `scripts/`, `app/core/` |
| **Build System** | ❌ FORBIDDEN | `pyproject.toml`, `uv.lock`, `Dockerfile.*` |

## ✅ 2. The Port 8080 Contract
Environment injection is deterministic using Port 8080.

**Infisical Production Command:**
```bash
# Injects secrets and binds frontend to the hardened RunPod API port
infisical run --env=production -- vercel --prod --yes \
  -e NEXT_PUBLIC_API_URL="https://${RUNPOD_POD_ID}-8080.proxy.runpod.net"
```

## ✅ 3. CI Workflow (`deploy-frontend.yml`)
Hardened workflow with `uv` and Port 8080 validation.

```yaml
name: Deploy Frontend v2.7

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - 'app/api/routes/**'

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scope Check
        run: bash scripts/guard_frontend.sh
      - name: Install uv & Ruff
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv pip install ruff
      - name: Lint API Routes
        run: uv run ruff check app/api/routes/
      - name: Build React Cockpit
        working-directory: ./frontend
        run: |
          npm ci
          npm run build
      - name: Infisical Push
        env:
          INFISICAL_TOKEN: ${{ secrets.INFISICAL_TOKEN }}
        run: |
          export INFISICAL_TOKEN=$INFISICAL_TOKEN
          infisical run --env=production -- vercel --prod --yes
      - name: Validate System Alignment
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${{ secrets.RUNPOD_ID }}-8080.proxy.runpod.net/health")
          if [ "$STATUS" != "200" ]; then
            echo "❌ Backend Port 8080 Unreachable. Aborting."
            exit 1
          fi
```

## ✅ 4. Health Check Logic
Indicators in Mission Control point to the unified 8080 endpoint.
- **Mercury AI LED**: Queries `/api/v1/alpha/insights` via Port 8080.
- **Sim Worker LED**: Checks the `workers:active` Redis set for heartbeats.
- **Supabase LED**: Verifies the `decrement_usage_atomic()` RPC is reachable.

## 🔴 Final Determinism Checklist
* [ ] **No Localhost**: `grep -r "localhost" frontend/` returns 0.
* [ ] **Path Integrity**: `scripts/guard_frontend.sh` is executable.
* [ ] **Secret Naming**: All Supabase secrets in Infisical use the `SB_` prefix.
* [ ] **Lock Alignment**: `uv.lock` is present and matches the current build.
