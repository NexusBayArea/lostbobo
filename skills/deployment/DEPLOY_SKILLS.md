# Master Deployment & DevOps Skills (v3.0.0)

## 🏗️ 1. Local Build Authority (LBA) Mandate

> **Strict Rule:** Docker images are created and pushed ONLY from the local dev environment. GitHub Actions is a "Read-Only" validation gate.

### The Single Entrypoint: `scripts/build.sh`

```bash
#!/bin/bash
# scripts/build.sh
set -e

IMAGE_NAME="ghcr.io/nexusbayarea/simhpc-unified"
GIT_SHA=$(git rev-parse --short HEAD)

echo "🏗️ Building SimHPC Local Authority Image: $GIT_SHA"

# 1. Build locally
docker build -t $IMAGE_NAME:latest -t $IMAGE_NAME:$GIT_SHA -f ./docker/images/Dockerfile.unified .

# 2. Push to Registry
docker push $IMAGE_NAME:latest
docker push $IMAGE_NAME:$GIT_SHA

echo "✅ Local Build Complete: $IMAGE_NAME:$GIT_SHA"
```

---

## 🔐 2. Unified Secret & Supabase Sync

Following the `SB_` prefix naming convention for Infisical and Vercel compatibility.

| Service | Secret Prefix | Storage / Source |
|---------|-------------|-----------------|
| **Supabase** | `SB_` | Infisical (Source of Truth) |
| **Vercel** | `VITE_SUPABASE_` | Synced from Infisical via `sb-sync.sh` |
| **RunPod** | `RUNPOD_` | GitHub Secrets (for Resume trigger) |

### The Translation Wrapper: `scripts/sb-sync.sh`

```bash
#!/bin/bash
# Sync SB secrets from Infisical and rename for Vercel builds.
SB_VARS=$(infisical export --format=dotenv | sed 's/SB_/VITE_SUPABASE_/g')
echo "$SB_VARS" | while read -r line; do
    if [[ $line == VITE_SUPABASE_* ]]; then
        KEY=$(echo $line | cut -d '=' -f 1)
        VALUE=$(echo $line | cut -d '=' -f 2-)
        vercel env add "$KEY" production --force <<< "$VALUE"
    fi
done
```

---

## 🔄 3. Operational Flowchart: LBA v3.0.0

The system follows a **Linear Directed Acyclic Graph (DAG)** to prevent re-entrancy loops.

1. **Validation**: `git push` triggers `.github/workflows/ci-validation.yml`.
   - Runs `ruff` via `uvx`.
   - **NO DOCKER BUILD ALLOWED.**
2. **Construction**: Developer runs `./scripts/build.sh` locally.
3. **Deployment**: Developer runs `./scripts/deploy.py` to trigger the RunPod GraphQL `podResume` mutation.

---

## 🚥 4. Hardening Invariants

### Port Authority

- **Strict Rule**: Production endpoint is **Port 8080**.
- **Forbidden**: Any mention of 8888 or 8000 for primary traffic.
- **Health Check**: `curl -f http://localhost:8080/health`

### Safe Push Protocol

- **Pre-commit**: `infisical scan` to prevent secret leaks.
- **Linting**: `ruff check . --fix` to maintain v3.0.0 code quality.
- **CI Isolation**: Use `uvx` for all cloud-side Python tasks to bypass PEP 668 locks.

---

## 📂 5. Final Repository Structure

```text
/simhpc-unified
├── .github/workflows/
│   └── ci-validation.yml  # [STRICT] No build steps.
├── scripts/
│   ├── build.sh           # [LBA] Image creation authority.
│   ├── deploy.py          # [LBA] Pod resumption authority.
│   └── sb-sync.sh         # [LBA] Secret translation (SB -> VITE).
├── app/                   # Backend logic (Port 8080).
├── frontend/              # Vite/React Cockpit.
├── docker/
│   └── images/
│       └── Dockerfile.unified
└── pyproject.toml         # uv Project Truth.
```

---

## 🚦 Action Items

1. **DELETE** fragmented deployment files.
2. **USE** `scripts/build.sh` for all image builds.
3. **ENFORCE** Port 8080 in all configurations.
4. **USE** `uvx` for CI-side Python tasks.

