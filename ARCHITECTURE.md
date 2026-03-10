# SimHPC Architecture

> Last Updated: March 8, 2026

---

## System Overview

SimHPC is a cloud-native GPU-accelerated finite element simulation platform. The architecture follows a distributed microservices pattern with a **securely isolated frontend** and a **closed-source backend** orchestration layer.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Vercel        │       │   RunPod        │       │   Supabase      │
│ (Frontend Only) │──────▶│ (API + Worker)  │──────▶│ (Auth + DB)     │
│ React + Vite    │       │ FastAPI + Celery│       │ PostgreSQL      │
│ [Public/Private]│       │ Redis + GPU     │       │ [No Git Sync]   │
└─────────────────┘       │ [Closed Source] │       └─────────────────┘
         │                └─────────────────┘                ▲
         │                         ▲                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                          JWT Auth (python-jose)
```

---

## Repository Strategy (Security Posture)

To protect core intellectual property (AI/Physics logic) during the beta phase, the codebase is split:

- **`simhpc-frontend`**: Contains *only* the React/Vite application. This repository is connected to Vercel for automated deployments.
- **Monorepo (Private)**: Contains the full platform, including the `robustness_orchestrator`, AI services, and physics-worker configurations. This remains closed-source and is never linked to Vercel or Supabase.

---

## Project Structure

```
SimHPC/ (Private Monorepo)
├── simhpc-frontend/              # React frontend source [CANONICAL]
├── robustness_orchestrator/      # Python backend services [CLOSED SOURCE]
│   ├── api.py                   # FastAPI orchestration layer
│   ├── robustness_service.py    # Parameter sweep logic
│   ├── ai_report_service.py     # Mercury AI (Inception Labs) integration
│   ├── pdf_service.py           # Engineering PDF generation
│   ├── tasks.py                 # Celery task definitions
│   └── _core/                   # Core simulation package
└── sdk/
    └── python/
        └── example.py           # Python automation SDK
```

---

## Components

### Frontend (React + Vite)
- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **Auth**: Supabase Auth (@supabase/supabase-js)
- **State**: React Context (theme, auth)
- **Charts**: Recharts for sensitivity visualization
- **Animations**: Framer Motion

### API Orchestrator (FastAPI)
- **Server**: Uvicorn/Gunicorn
- **Auth**: JWT verification via python-jose
- **Rate Limiting**: Redis-backed
- **Logging**: Structured JSON via structlog
- **Metrics**: Prometheus client

### Physics Worker (Celery)
- **Executor**: Celery with Redis broker
- **GPU**: NVIDIA CUDA 12.2.0
- **Solvers**: SUNDIALS, MFEM
- **Task Queue**: Redis

### Persistence Layer
- **Redis**: Job states, rate limits, telemetry
- **Supabase**: User data, auth, PostgreSQL
- **S3/R2**: PDF storage (optional)

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/signup | User registration |
| POST | /api/v1/auth/signin | Email/magic link login |
| GET | /api/v1/auth/session | Get current session |

### Simulations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/simulations/start | Start robustness analysis |
| GET | /api/v1/simulations/{id} | Get simulation status |
| GET | /api/v1/simulations/history | List user simulations |
| POST | /api/v1/simulations/{id}/cancel | Cancel running job |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/reports/ai | Generate AI engineering report |
| GET | /api/v1/reports/{id}/pdf | Download PDF export |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/subscribe | Create Stripe checkout session |
| POST | /api/v1/billing/webhook | Handle Stripe webhooks |
| GET | /api/v1/user/profile | Get subscription status |

### Demo
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/demo/general | Generate demo access link |
| GET | /api/v1/demo/access | Validate and redeem token |

---

## Security Architecture

### Authentication Flow
1. User signs up/in via Supabase (Magic Link) or Google One Tap (`g_id_onload`)
   - **Google Client ID:** `552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com`
2. Google GIS returns ID token -> Verified by Supabase
3. Supabase returns JWT access token
3. Frontend stores token in session
4. Backend verifies JWT via `python-jose`
5. **Tier Verification:** API queries Supabase `profiles` table using Service Role Key to determine `plan_id` and map to `free`/`professional`/`enterprise` tiers.
6. **Persistence:** Final physics data and simulation summaries are inserted into the `simulations` or `simulation_history` table in Supabase.

### Rate Limiting
- **Login/Signup**: 5 attempts/minute per IP
- **Simulations**: 10/hour per user (configurable by tier)
- **AI Reports**: 5/hour per user
- **API Keys**: Custom limits per enterprise client

### Abuse Prevention
- Google OAuth or verified email required
- Device fingerprinting (2 free accounts per device)
- IP-based limits (2 free accounts per IP)
- Free tier: 1 concurrent, 60s timeout, small mesh only
- Honeypot fields in forms
- Credit card trigger after 5 free simulations

---

## Tiered Access Model

| Feature | Free | Professional | Enterprise | Demo (Gen) | Demo (Full) |
|---------|------|--------------|------------|------------|-------------|
| Simulation runs | 5 max | 50 | Unlimited | 10 | 100 |
| Perturbation runs | 5 | 50 | Unlimited | 5 | 100 |
| AI reports | - | ✓ | ✓ | ✓ | ✓ |
| PDF export | - | ✓ | ✓ | - | ✓ |
| Cached reports | - | ✓ | ✓ | ✓ | ✓ |
| API access | - | - | ✓ | - | ✓ |
| Custom sampling | - | - | ✓ | - | ✓ |
| Sobol GSA | - | - | ✓ | ✓ | ✓ |
| Priority queue | - | - | ✓ | - | ✓ |

---

## Deployment

### Production Stack
- **Frontend**: Vercel (via `lostbobo` repo at https://github.com/NexusBayArea/lostbobo.git)
- **Production URL**: https://simhpc.com
- **Backend**: RunPod GPU instance (A40)
- **Database**: Supabase PostgreSQL (No Git sync)
- **Cache/Queue**: Redis 7 (alpine)

### Environment Variables
```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=

# API
SIMHPC_API_KEY=
REDIS_URL=redis://redis:6379/0

# AI
MERCURY_API_KEY=
MERCURY_MODEL=mercury-2

# Billing
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=

# Security
AUTH_SECRET=
GOOGLE_CLIENT_ID=552738566412-t6ba9ar8jnsk7vsd399vhh206569p61e.apps.googleusercontent.com
```

---

## Key Services

### RobustnessService
- Handles parameter sampling (±5%, ±10%, Latin Hypercube, Monte Carlo, Sobol)
- Manages baseline caching to prevent redundant GPU computation
- Implements input validation with physical parameter bounds
- Caps concurrent jobs (max 8) to prevent GPU exhaustion

### AIReportService
- Mercury AI (Inception Labs) integration
- Scientific tone enforcement (100-1000 chars, keyword constraints)
- 24-hour TTL cache for technical interpretations
- Numerical anchor verification against raw simulation metrics
- Graceful fallback to template generation

### PDFService
- FPDF-based PDF generation
- Matplotlib charts for sensitivity rankings
- DejaVu fonts with Helvetica fallback
- S3/R2 upload with signed URLs
