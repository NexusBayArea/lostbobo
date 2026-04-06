# SimHPC Deployment SOP (Standard Operating Procedure)

> Version: 2.5.3 | Last Updated: April 5, 2026

---

## Overview

SimHPC has four deployable components:

| Component | Deploy Method | Trigger |
|---|---|---|
| **Frontend** (Vercel) | Vercel native GitHub integration | Push to `main` |
| **Worker** (Docker Hub) | GitHub Actions | Push to `main` (path: `services/worker/**`, `Dockerfile.worker`) |
| **Autoscaler** (Docker Hub) | GitHub Actions | Push to `main` (path: `services/worker/runpod_api.py`, `services/worker/autoscaler.py`, `Dockerfile.autoscaler`) |
| **RunPod Worker** | Manual restart | After Docker image update |

---

## 0. Antigravity Infisical Setup (v2.5.2-BETA)

### The Infisical Handshake

Authenticate and connect to the secret vault:

```bash
infisical login
infisical init
```

This connects to the `v2.5.2-BETA` Secret Vault. All subsequent commands use `infisical run --` for secret injection.

### Secret-Safe Build

Build Docker images without local `.env` files:

```bash
infisical run -- env | grep -v "_gitignore" > .env.tmp && \
docker-compose build --no-cache && \
rm .env.tmp
```

### Runtime Injector

Start the local stack with secrets injected directly into memory:

```bash
infisical run -- docker-compose up
```

### Required Secrets in Infisical

| Secret | Description |
|---|---|
| `REDIS_URL` | Full Upstash connection URL (rediss://...) |
| `RUNPOD_API_KEY` | RunPod API key (rpa_...) |
| `RUNPOD_ID` | RunPod pod ID |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `MERCURY_API_KEY` | Mercury AI API key |
| `INFISICAL_TOKEN` | Machine identity token for automated workflows |

### Create Upstash Database

1. Go to **https://upstash.com**
2. Sign in with GitHub or Google
3. Click **Create Database**
   - **Name**: `simhpc`
   - **Region**: Select closest to your users
   - **Type**: Redis
4. Click **Create**

### Get Connection Details

From the database page, copy:
- **REDIS_TCP**: `rediss://default:TOKEN@noble-tapir-XXXX.upstash.io:6379`
- **REDIS_TOKEN**: The token after `default:`

### Add to Infisical

```bash
# Set Redis URL
infisical secrets set REDIS_URL=rediss://default:YOUR_TOKEN@noble-tapir-XXXX.upstash.io:6379

# Set Redis TCP (backup)
infisical secrets set REDIS_TCP=rediss://default:YOUR_TOKEN@noble-tapir-XXXX.upstash.io:6379

# Set Redis Token
infisical secrets set REDIS_TOKEN=YOUR_TOKEN
```

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
- Infisical secrets set (see Section 0)

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
| `INFISICAL_CLIENT_ID` | Infisical machine identity client ID |
| `INFISICAL_CLIENT_SECRET` | Infisical machine identity client secret |
| `DOCKER_ACCESS_TOKEN` | Docker Hub access token (from Infisical) |
| `DOCKER_USERNAME` | Docker Hub username (from Infisical) |

> **Note**: Docker credentials are fetched from Infisical at runtime via the Infisical action. Only the Infisical machine identity credentials need to be stored in GitHub.

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

Same as Worker: `INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET`

---

## 4. Auto-Deploy to RunPod

Automatically restarts your RunPod pod after a successful Docker image push.

### How It Works

1. Push to `main` triggers worker/autoscaler Docker build
2. Docker image pushes to Docker Hub
3. On success, `auto-deploy-runpod` workflow triggers
4. RunPod pod restarts to pull new image
5. Waits for pod to be READY (RUNNING)

### Required Infisical Secrets

| Secret | Description |
|---|---|
| `RUNPOD_API_KEY` | RunPod API key |
| `RUNPOD_POD_ID` | Your pod ID |

### Manual Deploy to RunPod

Use the "Deploy to RunPod" workflow from GitHub Actions:

1. Go to **Actions → Deploy to RunPod**
2. Click **Run workflow**
3. Choose action: `restart`, `stop`, or `start`
4. Click **Run workflow**

---

## 5. Audit Workflow (Ruff Lint)

Runs automatically on every push to `main`:

```bash
git push origin main
```

Checks:
- `ruff check services/worker/worker.py`
- `ruff format --check services/worker/worker.py`

Blocks deployment if lint fails.

---

## 6. Local Development

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

### Full Stack (Docker Compose) with Infisical

```bash
# Secrets are injected at runtime — no .env file needed
infisical run -- docker-compose up --build
```

Services:
- **Frontend**: http://localhost:80
- **API**: http://localhost:8000
- **API Health**: http://localhost:8000/api/v1/health
- **Redis**: localhost:6379

---

## 7. Troubleshooting

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

- Verify `DOCKERHUB_TOKEN` in GitHub secrets
- Check token has read/write access to `simhpcworker` org

### RunPod worker not picking up new image

- Wait 5 minutes (auto-updater cron runs every 5 min)
- Manually restart pod via RunPod API (see Manual Deploy above)
- Check pod logs for `pull_and_restart.sh` errors

---

## 8. Google OAuth Setup (Supabase + Google Cloud Console)

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

## 9. Database Migrations (Supabase)

After adding new `.sql` files to `supabase/migrations/`, push them to Supabase:

### Via Supabase CLI

```bash
# Link project (one-time)
./node_modules/supabase/bin/supabase.exe link --project-ref ldzztrnghaaonparyggz

# Push all pending migrations
./node_modules/supabase/bin/supabase.exe db push
```

### Via Supabase Dashboard

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Copy the contents of the new migration file
3. Paste and run

### Recent Migrations

| File | Purpose |
|---|---|
| `005_engineer_notebook.sql` | `notebooks` table with RLS, autosave support |
| `004_platform_alerts.sql` | `platform_alerts` table for billing/thermal alerts |
| `003_profiles_table.sql` | User profiles with tier/role tracking |
| `002_beta_schema_normalization.sql` | Core tables: `simulations`, `certificates`, `documents` |

---

## 10. RunPod GPU Worker Deployment

### Architecture

The RunPod worker runs on demand GPU pods managed by the autoscaler:

```
GitHub → Docker Hub → RunPod (auto-pull & restart)
```

### Prerequisites

- Docker Hub credentials (`DOCKER_ACCESS_TOKEN`, `DOCKER_USERNAME`) in GitHub Secrets
- RunPod API key and pod ID stored in **Infisical**
- Worker image: `simhpcworker/simhpc-worker:latest`
- Autoscaler image: `simhpcworker/simhpc-autoscaler:latest`

### Step-by-Step SOP

#### 1. Build and Push Worker Image

The worker image auto-deploys via GitHub Actions when `services/worker/**` or `Dockerfile.worker` changes:

```bash
git add -A && git commit -m "update worker" && git push origin main
```

Or manually:

```bash
docker build -f Dockerfile.worker -t simhpcworker/simhpc-worker:latest .
docker push simhpcworker/simhpc-worker:latest
```

#### 2. Build and Push Autoscaler Image

The autoscaler image auto-deploys via GitHub Actions when `services/worker/runpod_api.py`, `services/worker/autoscaler.py`, or `Dockerfile.autoscaler` changes:

```bash
docker build -f Dockerfile.autoscaler -t simhpcworker/simhpc-autoscaler:latest .
docker push simhpcworker/simhpc-autoscaler:latest
```

#### 3. Deploy to RunPod Pod

The automated script fetches ALL secrets from Infisical and recreates the pod with env vars:

```bash
python scripts/deploy_worker.py
```

This script:
1. Fetches all secrets from Infisical (RUNPOD_API_KEY, RUNPOD_ID, REDIS_URL, MERCURY_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
2. Builds and pushes Docker images to Docker Hub
3. Terminates the old pod
4. Creates a new pod with all environment variables from Infisical
5. Updates RUNPOD_ID in Infisical

```bash
# Restart pod
python scripts/restart_runpod_pod.py
```

The script:
1. Gets your API key and pod ID from Infisical
2. Stops the pod (graceful shutdown)
3. Resumes the pod with same GPU config
4. Pod pulls latest Docker images on restart

### Accessing RunPod Terminal

Your worker pod includes SSH and Jupyter for debugging:

```bash
# SSH into pod (from RunPod dashboard)
ssh x4bhfoq0frq1dq-64410b1f@ssh.runpod.io -p 22
```

### Current Pod Configuration

| Setting | Value |
|---|---|
| Pod ID | `qz1ilg2fi9osa0` |
| GPU | NVIDIA A40 |
| Image | `simhpcworker/simhpc-worker:latest` |
| Ports | 22/tcp (SSH), 8888/http (Jupyter) |

### Required Environment Variables

All these must be set in Infisical and passed when creating the pod:

| Variable | Source | Example |
|---|---|---|
| `REDIS_URL` | Upstash Redis | `rediss://default:token@host:6379` |
| `MERCURY_API_KEY` | Inception Labs | `sk_...` |
| `SUPABASE_URL` | Supabase Dashboard | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Settings → API | `eyJ...` |

#### 4. Verify Deployment

```bash
# Check pod status
curl -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{"query": "{ myself { pods { id name desiredStatus runtime imageName } } }"}'

# SSH into pod (if needed for debugging)
ssh -i $RUNPOD_SSH_KEY root@$POD_IP

# Check worker logs inside pod
docker logs -f $(docker ps -q --filter "ancestor=simhpcworker/simhpc-worker:latest")
```

#### 5. Local Testing (Without GPU)

Use the simplified docker-compose for local testing:

```bash
# Start Redis + Autoscaler + Mock Worker
docker-compose up --build

# Services:
# Redis:    localhost:6379
# Mock Worker: runs worker logic without GPU
```

### Troubleshooting

| Issue | Fix |
|---|---|
| Pod won't restart | Check `RUNPOD_API_KEY` is valid and pod exists |
| Old image running | RunPod auto-updater polls every 5 min; manually restart pod |
| SSH connection refused | Verify `RUNPOD_SSH_KEY` matches pod's public key |
| Worker crashes on start | Check `docker logs` inside pod for Python errors |
| Redis connection fails | Verify `REDIS_URL` env var points to correct Redis instance |

---

## 8. Docker Images

| Image | Tags | Size |
|---|---|---|
| `simhpcworker/simhpc-worker` | `latest`, `v2.5.3` | ~2.44GB |
| `simhpcworker/simhpc-autoscaler` | `latest`, `v2.5.3` | ~57MB |

---

## 9. Quick Reference

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
