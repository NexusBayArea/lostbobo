# SimHPC Pipeline Hardening - GHCR Registry

## Current Status

Transitioning from fragile Docker-based pipeline to hardened GHCR artifact registry.

---

## Target State

### ✅ Implemented

- Deterministic image naming: `ghcr.io/nexusbayarea/simhpc-worker` (lowercase, single namespace)
- Explicit environment promotion model: dev → staging → prod
- Safe GHCR auth with `packages: write` permission
- Immutable build artifacts via SHA tagging
- No `latest` tag overwrite
- CI-safe tagging tied to commit SHA

---

## Action Items

### 1. Docker Build Setup
- [ ] Update workflow to use docker/build-push-action@v5
- [ ] Configure cache-from/cache-to with GHA
- [ ] Tag with SHA + branch refs

### 2. GHCR Permissions
- [ ] Ensure workflow has `packages: write`
- [ ] Add docker/login-action@v3

### 3. Promotion Layer
- [ ] Implement digest-based promotion (pull → tag → push)
- [ ] Add digest inspection step

### 4. Immutability Rules
- [ ] Never overwrite SHA tags
- [ ] Document digest pinning for deployments

---

## Recent Change

**Error encountered**: `denied: installation not allowed to Create organization package`

**Root cause**: Missing `packages: write` permission in workflow OR org policy blocking package creation.

**Fix applied**: Hardcoded image name to `ghcr.io/nexusbayarea/simhpc-worker` to match expected package namespace.