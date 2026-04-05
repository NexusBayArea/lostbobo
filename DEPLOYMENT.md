# SimHPC Deployment SOP (Standard Operating Procedure)

> Version: 2.5.1 | Last Updated: April 4, 2026

---

## Overview

SimHPC has three deployable components:

| Component | Deploy Method | Trigger |
|---|---|---|
| **Frontend** (Vercel) | Vercel native GitHub integration | Push to `main` |
| **Worker** (Docker Hub) | GitHub Actions | Push to `main` (path: `services/worker/**`, `Dockerfile.worker`) |
| **Autoscaler** (Docker Hub) | GitHub Actions | Push to `main` (path: `services/worker/runpod_api.py`, `services/worker/autoscaler.py`, `Dockerfile.autoscaler`) |

---

## 1. Vercel Frontend Deployment

### Prerequisites

- GitHub repo connected to Vercel project
- Environment variables set in Vercel Dashboard (see below)

### Automatic Deploy (Recommended)

1. Push to `main`:
   ```bash
   git push origin main
   ```
2. Vercel automatically detects the push, builds, and deploys
3. Check status at: **https://vercel.com/<your-team>/simhpc/deployments**

### Manual Deploy (if auto-deploy fails)

1. Go to **Vercel Dashboard → Deployments**
2. Click **⋮** on the latest deployment → **Redeploy**
3. Uncheck "Use existing Build Cache" if the build was broken

### Required Vercel Environment Variables

Set in **Vercel Dashboard → Project → Settings → Environment Variables** (Production):

| Variable | Source | Required |
|---|---|---|
| `VITE_SUPABASE_URL` | Supabase Dashboard → Settings → API | Yes |
| `VITE_SUPABASE_ANON` | Supabase Dashboard → Settings → API (anon key) | Yes |
| `VITE_API_URL` | RunPod HTTP Proxy URL for API pod | Yes |

> **Note**: Vite replaces `VITE_*` vars at **build time**. If you change a var, you must trigger a redeploy for it to take effect.

### Vercel Build Settings

In **Vercel Dashboard → Project → Settings → General → Build & Development Settings**:

| Setting | Value |
|---|---|
| Framework Preset | Vite |
| Root Directory | `apps/frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |

---

## 2. Docker Hub Worker Deployment

### Prerequisites

- GitHub secrets configured (see below)
- Docker Hub account with `simhpcworker` org

### Automatic Deploy

1. Push changes to `services/worker/` or `Dockerfile.worker`:
   ```bash
   git push origin main
   ```
2. GitHub Actions builds and pushes:
   - `simhpcworker/simhpc-worker:latest`
   - `simhpcworker/simhpc-worker:v2.5.0`
3. RunPod Auto-Updater detects new image and restarts (~5 min)

### Manual Deploy

1. Build locally:
   ```bash
   docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .
   docker push simhpcworker/simhpc-worker:latest
   ```
2. Restart RunPod:
   ```bash
   curl -X POST "https://api.runpod.io/graphql" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $RUNPOD_API_KEY" \
     -d '{"query": "mutation { podRestart(podId: \"$RUNPOD_POD_ID\") { id status } }"}'
   ```

### Required GitHub Secrets

Set in **GitHub → Repo Settings → Secrets → Actions**:

| Secret | Source |
|---|---|
| `DOCKER_ACCESS_TOKEN` | Docker Hub → Account Settings → Security → Access Tokens |
| `DOCKER_USERNAME` | Docker Hub username |

---

## 3. Docker Hub Autoscaler Deployment

### Automatic Deploy

1. Push changes to `services/worker/runpod_api.py`, `services/worker/autoscaler.py`, or `Dockerfile.autoscaler`:
   ```bash
   git push origin main
   ```
2. GitHub Actions builds and pushes:
   - `simhpcworker/simhpc-autoscaler:latest`
   - `simhpcworker/simhpc-autoscaler:v2.5.0`

### Required GitHub Secrets

Same as Worker: `DOCKER_ACCESS_TOKEN`, `DOCKER_USERNAME`

---

## 4. Audit Workflow (Ruff Lint)

Runs automatically on every push to `main`:

```bash
git push origin main
```

Checks:
- `ruff check services/worker/worker.py`
- `ruff format --check services/worker/worker.py`

Blocks deployment if lint fails.

---

## 5. Local Development

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

### Full Stack (Docker Compose)

```bash
# Create .env file with required variables
docker-compose up --build
```

Services:
- **Frontend**: http://localhost:80
- **API**: http://localhost:8000
- **API Health**: http://localhost:8000/api/v1/health
- **Redis**: localhost:6379

---

## 6. Troubleshooting

### Build fails with TypeScript errors

- Check `tsconfig.app.json` has correct `include` paths
- Ensure all imports resolve correctly (no missing modules)
- Run `npx tsc -b` locally to see errors before pushing

### Vercel deploys but shows blank/blue screen

- Open browser console for error messages
- Check ErrorBoundary on screen for runtime errors
- Verify `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON` are set in Vercel
- Hard refresh (Ctrl+Shift+R) to clear cached build

### Docker Hub push fails

- Verify `DOCKER_ACCESS_TOKEN` and `DOCKER_USERNAME` in GitHub secrets
- Check token has read/write access to `simhpcworker` org

### RunPod worker not picking up new image

- Wait 5 minutes (auto-updater cron runs every 5 min)
- Manually restart pod via RunPod API (see Manual Deploy above)
- Check pod logs for `pull_and_restart.sh` errors

---

## 9. Google OAuth Setup (Supabase + Google Cloud Console)

### Prerequisites

- Google Cloud Console project with OAuth 2.0 Client ID configured
- Supabase project with Google provider enabled

### Step-by-Step SOP

#### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Add **Authorized JavaScript origins**:
   - `https://simhpc.com`
   - `https://simhpc.vercel.app`
   - `http://localhost:5173` (for local dev)
5. Add **Authorized redirect URIs**:
   - `https://ldzztrnghaaonparyggz.supabase.co/auth/v1/callback` (your Supabase callback)
6. Save and copy the **Client ID** and **Client Secret**

#### 2. Enable Google in Supabase

1. Go to **Supabase Dashboard** → **Authentication** → **Providers**
2. Find **Google** and click to configure
3. Toggle **Enable Sign in with Google**
4. Paste your **Client ID** and **Client Secret** from Google Cloud Console
5. Note the **Redirect URL** shown (should be `https://<project-ref>.supabase.co/auth/v1/callback`)
6. Click **Save**

#### 3. Verify Redirect URL Match

The redirect URL in Supabase **must exactly match** one of the Authorized redirect URIs in Google Cloud Console:

- Supabase shows: `https://ldzztrnghaaonparyggz.supabase.co/auth/v1/callback`
- Google Cloud Console must have: `https://ldzztrnghaaonparyggz.supabase.co/auth/v1/callback`

> **Common Error**: `Unable to exchange external code: 4/0A` means the redirect URI doesn't match. Double-check both sides.

#### 4. Store Credentials in Infisical (for local dev)

```bash
infisical secrets set GOOGLE_CLIENT_ID="<your-client-id>" --env=prod
infisical secrets set GOOGLE_CLIENT_SECRET="<your-client-secret>" --env=prod
```

#### 5. Test

1. Go to `https://simhpc.com/signup` or `https://simhpc.com/signin`
2. Click **Continue with Google**
3. Should redirect to Google consent screen → back to `/dashboard`

### Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Unable to exchange external code: 4/0A` | Redirect URI mismatch | Add exact Supabase callback URL to Google Cloud Console |
| `Supabase client not initialized` | Missing env vars | Check `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON` in Vercel |
| Google button does nothing | Supabase provider not enabled | Enable Google in Supabase Dashboard → Auth → Providers |
| 404 after Google redirect | Missing SPA rewrite rule | Ensure `vercel.json` has `rewrites` rule for `/index.html` |

---

## 7. Docker Images

| Image | Tags | Size |
|---|---|---|
| `simhpcworker/simhpc-worker` | `latest`, `v2.5.0` | ~2.44GB |
| `simhpcworker/simhpc-autoscaler` | `latest`, `v2.5.0` | ~57MB |

---

## 8. Quick Reference

### Deploy Everything

```bash
# 1. Push all changes
git add -A && git commit -m "your message" && git push origin main

# 2. Frontend auto-deploys via Vercel
# 3. Worker/Autoscaler auto-deploy via GitHub Actions (if paths match)

# 4. Verify
curl https://simhpc.com                    # Frontend
curl http://localhost:8000/api/v1/health   # API (local)
docker pull simhpcworker/simhpc-worker     # Worker image
```

### Rollback

1. Go to **Vercel Dashboard → Deployments**
2. Click **⋮** on the last working deployment → **Instant Rollback**
