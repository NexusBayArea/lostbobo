# SimHPC Mission Control Cockpit

The SimHPC Frontend is **LIVE** and accessible at [https://simhpc.com](https://simhpc.com).

This is the public-facing repository for the SimHPC Mission Control Cockpit, a premium interface for aerospace and thermal engineering simulations.

## Architecture (v2.2.0)

### Docker Containers
| Service | Image | Purpose |
| :--- | :--- | :--- |
| API | `Dockerfile.api` | FastAPI orchestrator (Mercury AI integration) |
| GPU Worker | `Dockerfile.worker` | v2.2.1: NVIDIA CUDA 12.1 + Metric Sync |
| Autoscaler | `Dockerfile.autoscaler` | v2.2.1: Queue-Aware (Q + Inflight) |
| Redis | `redis:7-alpine` | Message broker + Scaling metrics |

### Local Alpha Launch
To launch the full "Mission Control" stack locally:

1. **Prep your .env**: Ensure your root directory has a `.env` file with your `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SIMHPC_API_KEY`.
2. **Fire it up**:
   ```bash
   docker-compose up --build
   ```
   This will start the Redis broker, the FastAPI orchestrator, and the GPU-ready physics worker.

### Queue Architecture (v2.2.1)
- **Queue Name**: `simhpc_jobs` (pending)
- **Inflight Key**: `simhpc_inflight` (currently processing)
- **Polling**: Every 10 seconds
- **Policy**: `target = ceil((pending + inflight) / MAX_JOBS_PER_GPU)`
- **Idle Shutdown**: Individual pods terminated after `IDLE_TIMEOUT` (default 300s)
- **Safety**: `MAX_PODS=2`, budget caps enforced, Redis-persisted activity state
- **Fleet API**: Admin endpoints at `/api/v1/admin/fleet/*` for pod lifecycle management

## v2.2.1: Queue-Aware Production Autoscaler
- **Advanced Metrics**: Scaling decisions now based on `pending + in-flight` jobs for precision.
- **GPU Selection**: Automated preference for cost-efficient A40 GPUs.
- **Worker Sync**: High-fidelity idle detection via `pods:last_used:{id}` Redis timestamps.

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
|----------|---------|--------|
| `VITE_SUPABASE_URL` | Supabase project URL | Supabase Dashboard |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | Supabase Dashboard |
| `VITE_API_URL` | Backend API endpoint | RunPod API container |
#### Vercel (Automatic)
Vercel injects these via the Dashboard or `vercel-action` workflow. **Never use local .env files for production secrets.**

### Strategic Vercel Best Practices

#### 1. The "Double-Key" Strategy
- **Frontend**: Uses `VITE_SUPABASE_ANON_KEY` to allow users to authenticate and read their own data.
- **RunPod Worker**: Uses `SUPABASE_SERVICE_ROLE_KEY` to perform administrative database updates, bypassing Row Level Security (RLS) for high-frequency physics telemetry.

#### 2. Stable RunPod Handshake
If the Sim Worker shows as "Offline," it is likely due to an IP change after a restart.
- **Action**: Use the **RunPod HTTP Proxy URL** (e.g., `https://x613fv0zoyvtx9-8000.proxy.runpod.net`) in `VITE_API_URL` instead of a direct IP.

### RunPod Connectivity (v2.2.1)
- **Pod ID**: `x613fv0zoyvtx9`
- **Direct TCP Connection**: `194.68.245.30:22128` (maps to internal port `:22`)
- **SSH Command**: 
  ```bash
  ssh root@194.68.245.30 -p 22128 -i ~/.ssh/id_ed25519
  ```
- **CORS**: Ensure `ALLOWED_ORIGINS` in your FastAPI backend includes your specific Vercel domain. Never use `*` in production.

#### 3. Google Cloud Console Configuration
For Google One Tap and Sign-In to function on Vercel:
- **Authorized JavaScript Origins**: Add `https://simhpc.com` and your Vercel preview URLs.
- **Authorized Redirect URIs**: Add `https://simhpc.com/api/auth/callback/google`.

#### GitHub Pages (Manual — Required)
...

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
