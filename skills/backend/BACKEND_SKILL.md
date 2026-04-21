# Backend & Infrastructure Skill (v3.0.0)

> **Note**: This file is for documentation only. DO NOT PUSH TO GIT.

## 🏗️ LBA Repository Structure
The repository is now a **Decoupled Monorepo**. Infrastructure logic is split between local "Authority" and cloud "Validation."

```text
/simhpc-unified
├── .github/workflows/
│   └── ci-validation.yml    # [STRICT] Only uvx linting/structure checks. NO BUILDS.
├── scripts/                # [LOCKED] System Authority
│   ├── build.sh            # [LBA] Local Docker Build & Tag (Git SHA)
│   ├── deploy.py           # [LBA] Manual RunPod Reset / GraphQL Trigger
│   └── check_context.py    # Pre-build validation script
├── app/                    # [CORE] Backend Logic
│   ├── api/                # FastAPI Endpoints (Standard: Port 8080)
│   ├── services/worker/    # Physics Engine & Job Processing
│   └── core/               # Auth, Redis Queue, & Config
├── docker/
│   ├── images/
│   │   └── Dockerfile.unified # Single source for all-in-one image
│   └── supervisor/
│       └── simhpc.conf     # Process management (Port 8080)
├── pyproject.toml          # uv Project Truth
└── uv.lock                 # Deterministic Lockfile
```

---

## 🔄 Operational Flowchart: The Linear Pipeline
Unlike the previous cyclical loop, the v3.0.0 pipeline is a **Directed Acyclic Graph (DAG)**.



1.  **Code Change**: Developer modifies code in `/app`.
2.  **CI Validation**: `git push` triggers `ci-validation.yml`. Runs `ruff` via `uvx`. **Result: Pass/Fail (No Image).**
3.  **Local Build**: Developer runs `./scripts/build.sh`. Docker builds the image locally. **Result: Image Tagged with SHA.**
4.  **Manual Release**: Developer runs `docker push` followed by `./scripts/deploy.py`. **Result: RunPod pulls new image and resumes.**

---

## 🔒 Hardening Invariants (The "Skills")

### 1. Port 8080 "Gold Standard"
* All internal services (Uvicorn, Gunicorn) must bind to **0.0.0.0:8080**.
* All health probes must target `http://localhost:8080/health`.
* **Prohibited**: Any suggestion of Port 8888 or 8000 for primary traffic.

### 2. The "No-Docker-In-Cloud" Rule
* The AI is strictly prohibited from adding Docker login or build steps to `.github/workflows`.
* Cloud environments are considered "ReadOnly" for artifacts.

### 3. uvx Isolation
* To bypass "Externally Managed Environment" errors in GitHub Runners, all Python tools (Ruff, Pytest) must be executed via `uvx`.
* **Command**: `/home/runner/.local/bin/uvx ruff check .`

### 4. Self-Healing Logic
* The CI must automatically apply minor linting fixes (unused imports, etc.) and flag them, but it cannot commit back to the repo without user approval.

---

## 🚦 Status Indicators (v3.0.0)
| Component | Standard | Verification |
| :--- | :--- | :--- |
| **Backend API** | Port 8080 | `curl /health` returns 200 |
| **Worker Queue** | Redis BRPOPLPUSH | `workers:active` key heartbeat |
| **Build State** | Local Only | `docker images` shows SHA-tagged image |
| **CI State** | Green | `ci-validation.yml` completes < 60s
