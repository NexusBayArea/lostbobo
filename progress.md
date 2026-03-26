# Progress Log

## Current Status

- **v2.2.1**: RunPod API Integration + Queue-Aware Autoscaler + Docker Hub Images.
- **v1.6.0-ALPHA**: Mission Control Cockpit (Modular Design Intelligence Platform).
- **v1.5.1-ALPHA**: Alpha Control Room (4-Panel UI).
- **v1.4.0-BETA**: Direct Vercel Deployment & RunPod Orchestration.

---

## RunPod API + Cost-Aware Autoscaler (March 25, 2026)

### Problem: Idle GPU Burn
Manual pod management via RunPod UI led to $10–$25/day idle burn with no automated cost controls.

### Fix: Production-Grade Orchestration
1. **RunPod API Client (`runpod_api.py`)**: Full pod lifecycle management via GraphQL API.
2. **Queue-Aware Autoscaler v2.2.1**: Advanced scaling based on `queue_length` + `inflight_jobs`.
   - **Metrics**: Real-time tracking of pending vs. processing jobs via Redis.
   - **Cost Control**: `MAX_PODS` cap and automatic idle termination after 300s.
   - **GPU Policy**: Prefers cost-effective A40 GPUs with RTX 3090 fallback.
3. **Vercel & Security Policy v2.2.1**: Standardized environment and deployment policy.
   - **Double-Key Strategy**: Implemented split Supabase keys (Anon for Frontend, Service Role for Worker).
   - **Stable Handshake**: Transitioned to RunPod HTTP Proxy URLs to eliminate "Offline" blips from IP changes.
   - **Google One Tap Fix**: Updated Google Cloud Console origins and redirect URIs for Vercel production.
4. **RunPod Fleet Migration (v2.2.1)**: Successfully migrated to a high-performance pod cluster.
   - **New Pod ID**: `tfcp1h68vdsvth`
   - **Direct Access**: SSH (`ssh root@69.30.85.73 -p 22086 -i ~/.ssh/id_ed25519`) and Direct TCP (`69.30.85.73:22086`)
   - **HTTP Proxy**: `https://tfcp1h68vdsvth-8000.proxy.runpod.net`
   - **Global Sync**: Updated 12+ files across frontend, backend, and documentation to reflect the new pod infrastructure.
5. **Worker v2.2.1**: Integrated with autoscaler metrics.
   - **Inflight Tracking**: Increments `simhpc_inflight` on job pop, decrements on completion.
   - **Activity Timestamping**: Updates `pods:last_used:{pod_id}` in Redis for precise idle detection.
   - **GPU Acceleration**: NVIDIA CUDA 12.1 + high-performance physics stack.
4. **Local Alpha Stack**: Implemented `docker-compose.yml` for solo-founder rapid development.
5. **Admin & Health API**: 7 new protected endpoints in `api.py` for fleet and system health monitoring.
   - `GET /api/v1/system/status` — Aggregated health check (Mercury, RunPod, Supabase, Worker).
   - `GET /api/v1/admin/fleet` — Fleet status dashboard data.
   - `GET /api/v1/admin/fleet/cost` — Cost tracking summary.
   - `POST /api/v1/admin/fleet/pod/{id}/stop` — Stop pod.
5. **Security & Connectivity**:
   - **CORS Hardening**: Added `simhpc.nexusbayarea.com` and `simhpc.com` to allowed origins.
   - **Production Redis Guard**: Added validation to block `localhost` Redis usage in Vercel environments.
   - **Supabase Service Role**: Standardized on `SUPABASE_SERVICE_ROLE_KEY` for background writes.
6. **Infrastructure Updates**:
   - `Dockerfile.autoscaler` updated to include `runpod_api.py`.
   - `docker-compose.yml` autoscaler service updated with 10 additional env vars.

---

## Physics Worker: PDF Report Storage (March 23, 2026)

### Problem: Raw Data Exposure
Simulation results were only available as raw JSON in the database, lacking professional engineering artifacts for export.

### Fix: Automated Engineering Artifacts
1. **PDF Generation**: Implemented a professional PDF report generator in `services/worker/pdf_service.py` with Unicode support and numerical anchoring.
2. **Supabase Storage Integration**: 
   - Added `upload_pdf_to_supabase` to handle artifact persistence.
   - Workers now upload generated PDFs to the `reports` bucket.
3. **Tiered Access Control**:
   - Implemented Public URLs for Free/Demo users.
   - Implemented **Signed URLs** (1-hour expiration) for Professional/Enterprise users.
4. **Worker Workflow Update**: 
   - `services/runpod-worker/worker.py` now triggers PDF generation and upload upon simulation completion.
   - The `pdf_url` is returned in the job result and synced to the `simulation_history` table for instant frontend access.

---

## Toast Notification System Fix (March 18, 2026)

### Problem: Silent Errors
The `<Toaster />` component from sonner was **never mounted** in the React tree. All 12 `toast()` calls were silently doing nothing.

### Fix: Reactive Toast Notifications
1. Created `src/App.tsx` with `<Toaster />` (6s default, 8s success, 10s error, cyan theme, rounded corners).
2. Created `src/index.css` (toast CSS overrides) and `src/hooks/useSimulationUpdates.ts` (Supabase Realtime hook).
3. Updated `Dashboard.tsx` to use `toast.promise()` pattern for simulation submissions.
4. Created `src/components/SimulationDetailModal.tsx` — AI insights, physics metrics, PDF download.
5. Created `src/pages/AdminAnalytics.tsx` — Admin Control at `/admin/analytics` with lead qualification.

### Custom Domain & First-Party Auth (March 18, 2026)
- DNS: A `@ → 76.76.21.21`, CNAME `auth → [project-ref].supabase.co`
- Eliminates "Cookie Rejected" errors by making Supabase Auth first-party.
- CORS hardened in `api.py` from `["*"]` to explicit allow-list.

---

## Frontend Deployment Diagnosis (March 18, 2026)

### GitHub Pages vs Vercel Analysis
Console logs revealed that the GitHub Pages deployment fails while Vercel works due to:

1. **Environment Variable Injection**: Vite requires `VITE_SUPABASE_URL` at build time.
2. **CSP Restrictions**: `github.io` enforces strict CSP which blocks Stripe.js.
3. **Third-Party Cookie Blocks**: Enhanced Tracking Protection on `github.io` blocks Supabase Auth.

### Decision: Vercel Production Standard
**Vercel retained as Production Primary.** GitHub Pages remains as backup/staging with env var injection fix applied if needed.

---

### March 18, 2026 (SaaS Deployment & Production Launch)

- **Frontend Deployment**: Successfully pushed the finalized `v1.6.0-ALPHA` cockpit to `lostbobo.git`.
- **Production Status**: SimHPC SaaS is LIVE at <https://simhpc.com>.
- **Conflict Resolution**: Synchronized the frontend repository with the latest component updates.

### March 16, 2026 (Mission Control Cockpit Redesign - v1.6.0)

- **Modular Component Architecture**: Decoupled the Alpha Control Room into production-grade components: `TelemetryPanel`, `ActiveSimulations`, `SimulationLineage`, `OperatorConsole`, and `GuidanceEngine`.
- **Mercury AI Integration**: Fully transitioned to Mercury AI for simulation assistance and notebook generation.
- **System Health LEDs**: Real-time status indicators for Mercury AI, Supabase, and RunPod.
