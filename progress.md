# SimHPC Platform - Progress Report

## Overview

SimHPC is a cloud-based GPU-accelerated finite element simulation platform with integrated robustness analysis and AI-generated engineering reports. Built for engineering teams that require stable, defensible results.

**Live URL:** https://simhpc.com

---

## Project Structure

```
SimHPC/
├── app/                          # React frontend application
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   │   ├── Dashboard.tsx         # Main dashboard with robustness
│   │   │   ├── Benchmarks.tsx        # NAFEMS Verification Vault
│   │   │   └── ...
│   │   ├── sections/            # Landing page sections
│   │   └── lib/
│   │       └── api.ts           # Centralized API client
├── robustness_orchestrator/      # Python backend services
│   ├── api.py                   # FastAPI orchestration layer
│   ├── robustness_service.py    # Parameter sweep logic
│   ├── ai_report_service.py     # AI interpretation layer
│   └── pdf_service.py           # Engineering PDF generation
└── sdk/
    └── python/
        └── example.py           # Python automation SDK
```

---

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features Implemented](#features-implemented)
- [Technical Stack](#technical-stack)
- [Architectural Improvements](#architectural-improvements)
- [Enterprise Readiness](#enterprise-readiness)
- [Tiered Access Model](#tiered-access-model)
- [Technical Summary](#technical-summary)
- [Deployment](#deployment--production)
- [Related Documentation](#related-documentation)

---

## Related Documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical design and system components
- [CHANGELOG.md](./CHANGELOG.md) - Version history and release notes
- [ROADMAP.md](./ROADMAP.md) - Future features and planning

---

## Features Implemented

### 1. Theme System
- **Day Mode:** Off-white background (#F1EDE0) with slate text
- **Night Mode:** Dark slate background (#080E1C) with light text
- **Persistent:** Theme preference saved to localStorage

### 2. Landing Page Sections
- **Hero:** Animated mesh and confidence interval visualization
- **Stack:** Deterministic physics core (SUNDIALS, MFEM)
- **Who It's For:** Battery R&D, Hardware Startups, National Labs

### 3. Verification Benchmark Library (The "Validation Vault")
- Dedicated page showcasing SimHPC results vs. NAFEMS Benchmarks
- Side-by-side comparison with Analytical solutions and Ansys/COMSOL
- Verified cases: LE10 (Stress), FV32 (Thermal), BM3 (Structural)
- Direct link from main navigation for engineering trust

### 4. Dashboard
- **Model Configuration:**
  - Support for CAD formats: STEP, IGES, Parasolid (.x_t), STL
  - Integrated mesh upload and solver selection (SUNDIALS, MFEM)
- **Robustness Analysis:**
  - Parameter sampling (±5%, ±10%, Latin Hypercube, Monte Carlo)
  - **Sobol GSA (Enterprise):** Implementation of Global Sensitivity Analysis using Saltelli sampling. Calculates First-order ($S_1$) and Total ($S_T$) indices.
  - **Interaction Detection:** Identifies multi-variable coupling effects ($S_T - S_1$) to guide joint optimization.
  - **Efficiency:** Baseline result caching to prevent redundant GPU computations.
  - **Clamping:** Input validation ensures all perturbations respect physical parameter bounds (min/max).
  - **Concurrency Control:** Explicit thread/job capping (max 8 concurrent) to prevent GPU resource exhaustion.
- **"Kill Switch" & Telemetry:**
  - **Live Heartbeat:** WebSocket-driven telemetry bridge streaming step size (h) and solver convergence in real-time.
  - Real-time "Cancel and Refund Credits" button in Run Control.
  - **Resilience:** Convergence timeout enforcement (default 300s).

### 5. AI Engineering Reports
- **LLM Integration:** Tenacity-backed retry logic for resilient LLM communication (OpenAI/Groq ready).
- **Sobol Integration:** AI now interprets multi-variable interactions and suggests joint optimization strategies based on $S_1$ vs $S_T$ discrepancies.
- **Governance:** 
  - **Scientific Tone:** Mandatory length constraints (100-1000 chars) and keyword enforcement ("suggests" vs "proves").
  - **Cache Invalidation:** 24-hour TTL for technical interpretations to ensure data freshness.
- **Numerical Anchor:** Hard-coded integrity verification system that cross-checks AI conclusions against raw simulation metrics (max_temp, stability).
- **Export Formats:** Technical delivery via Markdown, JSON, and HTML.

### 6. Security & Persistence
- **Authentication:** Unified Supabase Authentication (Google OAuth & Email Magic Link) with JWT verification.
- **Backend Verification:** FastAPI middleware verifies Supabase JWTs using `python-jose`.
- **Frontend Auth:** `useAuth` hook for managing user sessions and protecting routes.
- **Token Escrow & Pricing:** 
  - Credit management logic that locks user tokens during simulation runs.
  - **Tiered Pricing:** 2 tokens/run for Enterprise Sobol, 5 tokens/run for standard sweeps.
- **Distributed Persistence:** 
  - **Redis:** High-speed persistence for job states and real-time telemetry queuing.
  - **Rate Limiting:** Redis-backed limiters (10 simulations/hour per user) to protect GPU capacity.
- **Monitoring:** Structured JSON logging for all service-level events.


---

## Technical Stack

### Infrastructure & DevOps
- **Orchestration:** Docker Compose (v3.8)
- **Container Architecture:** 
  - `simhpc/api`: FastAPI orchestrator service
  - `simhpc/physics-worker`: Heavy-lift container running SUNDIALS & MFEM with NVIDIA GPU runtime
  - `redis:7-alpine`: Message broker and telemetry store
- **GPU Support:** NVIDIA runtime enabled for RunPod A40 instances
- **Environment:** `${SUPABASE_JWT_SECRET}` for auth, configurable CORS origins
- **Volumes:** Persistent storage (`sim_data`) for simulation outputs

### Frontend
- **Framework:** React 18 (Vite) + TypeScript
- **Authentication:** Supabase Auth (@supabase/supabase-js)
- **Styling:** Tailwind CSS + shadcn/ui
- **Animations:** Framer Motion
- **State Management:** React Context for theme and Auth state
- **Build:** GitHub Pages deployment with GitHub Actions

### Backend (Python Services)
- **Orchestrator:** FastAPI + Uvicorn
- **Auth Utils:** JWT verification for Supabase tokens
- **Physics Utils:** NumPy for parameter sampling
- **Reporting:** AI-driven text generation + FPDF for PDF export

---
### March 5, 2026 (Monetization & User Management)
- **Stripe Subscription Lifecycle:** 
  - Implemented secure backend webhook `/api/v1/billing/webhook` to handle `checkout.session.completed` events from Stripe.
  - Standardized tier upgrades in Redis, mapping Stripe Customer IDs to Supabase User IDs via `client_reference_id`.
- **User Profile Service:** Added `GET /api/v1/user/profile` endpoint to provide synchronized plan and subscription status to the frontend.
- **Dynamic Tier Enforcement:** 
  - Updated `useAuth` hook with `userTier` state and `refreshTier` logic to automatically reflect plan upgrades in the UI.
  - Refactored `api.ts` with `UserProfile` interfaces and support for the new monetization endpoints.
- **Full-Stack Production Ready:**
...
- **Unified Full-Stack Architecture:** Implemented a global `docker-compose.yml` integrating the Vite frontend, FastAPI orchestrator, Celery worker, and Redis state store into a single orchestrated environment.
- **Bi-Modal Containerization:** 
  - Refined `Dockerfile` and `entrypoint.sh` to allow a single production image to serve as either the API or the Worker based on environment variables.
  - Hardened dependencies in `requirements.txt` with pinned versions for `celery`, `gunicorn`, and `redis`.
- **Backend Debugging & Hardening:**
  - Standardized **Tier-Aware Processing**: Workers now dynamically respect `PLAN_LIMITS` for AI report generation and statistical analysis.
  - Improved **State Persistence**: Implemented atomic Redis updates with `decode_responses=True` and standardized JSON serialization for complex payloads (`results`, `ai_report`, `metadata`).
  - Resolved **Circular Dependencies**: Refactored `tasks.py` with local imports to support seamless integration with the main `api.py` while maintaining package modularity.
- **Production Distribution:**
  - Migrated production endpoint to new RunPod instance: **`40n3yh92ugakps`**.
  - Generated **`simhpc_production_march5.zip`**: The authoritative deployment package containing the finalized modular architecture and `_core` package.
  - Updated **`setup_runpod.sh`**: Automated Docker and Docker Compose installation for one-click distributed deployment on GPU instances.
- **Frontend Real-Time Capabilities:**
...
  - **`useSimulation` Hook:** Created a custom React hook for managing the end-to-end simulation lifecycle, including automated polling and state transition handling.
  - **Live Progress Tracking:** Implemented `SimProgress.tsx` using Shadcn UI primitives to visualize solver states and perturbation progress.
  - **Data Visualization:** Developed `SensitivityChart.tsx` using Recharts for high-fidelity horizontal bar charts of parameter influence coefficients.
  - **Simulation Types:** Standardized the data contract between Python and TypeScript with a comprehensive `simulation.ts` types library.
- **`_core` Package Finalization:** 
  - Validated `__init__.py` structure across the backend to ensure reliable package discovery in production environments.
  - Renamed core simulation task to `process_simulation` for consistency across the distributed stack.

### March 5, 2026 (Frontend Auth & Polling)
- **One-Click Live Demo:** Integrated "Explore Live Demo" button in `Hero.tsx` that triggers secure, temporary backend session generation and auto-login.
- **Visual Job Tracking:** Implemented `JobProgress.tsx` component to visualize real-time worker states (Queued, Processing, Completed, Failed) with smooth Framer Motion animations.
- **Asynchronous Polling:** Implemented a recursive `pollStatus` mechanism in `lib/api.ts` to handle the new distributed worker lifecycle.
- **Auth Integration:** Updated `useAuth` hook to expose the Supabase JWT `session` and `getToken()` helper.
- **Secure API Client:** Refactored `api.ts` to automatically attach the Supabase JWT to the `Authorization: Bearer` header when available.

### March 5, 2026 (Production Readiness & Scaling)
- **Distributed Architecture:** Implemented `docker-compose.yml` defining an API Orchestrator, a GPU-enabled Celery Worker, and a Redis state store.
- **Production Packaging:**
  - Created a multi-purpose **GPU-ready Dockerfile** based on `nvidia/cuda:12.2.0-base-ubuntu22.04`.
  - Implemented `entrypoint.sh` to dynamically switch between API and Worker roles based on environment variables.
  - Initialized `__init__.py` files at root and package levels to ensure robust Python modularity.
- **`_core` Package Structure:** 
  - Refactored simulation logic into a structured `_core` package for better modularity and horizontal scaling.
  - Standardized the primary simulation task as `process_simulation` across the API and Worker.
  - Implemented absolute imports across `robustness_service.py`, `ai_report_service.py`, and `auth_utils.py`.
- **Task Offloading:** Integrated Celery for asynchronous processing of heavy physics and AI calculations, ensuring the API gateway remains responsive under load.
- **Worker Bridge (`tasks.py`):** Created a production-ready task bridge that handles parameter reconstruction, deterministic physics execution, and tier-aware AI report generation.
- **Fail-Safe Lifespan:** Refactored FastAPI `lifespan` in `api.py` to move critical secret validation and Redis initialization to the startup hook, improving container resilience and logging.
- **Service Hardening:**
  - Added synchronous wrappers to `RobustnessService` and `AIReportService` for compatibility with distributed workers.
  - Implemented `to_dict` serialization across all core data classes for stable Redis persistence.
- **Auth & Infrastructure:**
  - **Google Sign-In Integration:** Implemented full Google OAuth support in `SignIn.tsx` and `SignUp.tsx` using Supabase Auth.
...
- **Enhanced Registration:** Refactored `SignUp.tsx` to handle secure password-based registration with email verification and metadata syncing (`full_name`).
- **Unified Auth Logic:** Standardized redirect flows to ensure consistent navigation to the `/dashboard` after authentication.
- **Enterprise-Grade Demo System:**
  - **Multi-Tier Demo Access:** Implemented `DEMO_GENERAL` and `DEMO_FULL` plan tiers for controlled prospect exploration and sales qualification.
  - **Secure One-Time Tokens:** Added a Redis-backed, single-use demo access token system with 60-minute expiration and salted SHA-256 hashing to prevent credential exposure.
  - **Automated Onboarding Flow:**
    - `POST /demo/general`: Generates public-facing temporary access links with IP-based rate limiting (10 tokens/day).
    - `GET /demo/access`: Validates tokens, marks them as used, and auto-authenticates users into dedicated demo accounts with pre-configured plan tiers.
  - **Feature Gating & Limits:**
    - **General Demo:** Configured for safe exploration (10 runs, 5 perturbations, AI reports enabled, PDF export disabled).
    - **Full Demo:** Unlocked for deep evaluation (100 runs, 100 perturbations, full AI/PDF features, and Sobol GSA enabled).
  - **Security & Logging:**
    - Integrated with `auth_utils` to generate signed JWTs compatible with existing Supabase verification logic.
    - Implemented IP-based tracking and logging for all demo access events.
- **Infrastructure Configuration:**
  - Initialized `.env` file with Supabase URL and Publishable Key.
  - Added placeholders for `SUPABASE_JWT_SECRET` and `SIMHPC_API_KEY` to ensure correct environment setup.

### March 4, 2026 (Docker Optimization & Infrastructure)
- **Multi-Stage Build:** Transitioned to a multi-stage Docker build process (Builder → Runtime) to reduce final image size and separate build-time dependencies (`cmake`, `gfortran`) from production runtime.
- **Security & Permissions:** Enforced non-root user execution (`appuser`) and hardened file permissions within the container.
- **Production Server:** Migrated from development `uvicorn` to a production-grade `gunicorn` configuration with Uvicorn workers and structured logging.
- **Build Context Optimization:** Created a comprehensive `.dockerignore` file to prevent sensitive files and local caches from being included in the image.
- **Dependency Pinning:** Pinned base image SHA and standardized environment variables for consistent builds across CI/CD environments.

### March 4, 2026 (Backend Hardening & Security Phase 4)
- **AI Report Optimization & Cost Tracking:**
  - Implemented `tiktoken` for real-time LLM token counting and cost monitoring.
  - Parallelized section generation using `asyncio.gather` and `asyncio.to_thread` for significantly faster report delivery.
  - Improved AI fallback messages with more informative placeholders ("AI analysis unavailable — contact support").
- **Stripe & Billing Integration:**
  - Integrated `stripe-python` for automated billing and subscription management.
  - Added `/api/v1/subscribe` endpoint to generate dynamic Stripe Checkout sessions.
  - Implemented `/api/v1/billing/webhook` to handle asynchronous plan upgrades and subscription state changes.
  - Merged `run_with_cors.py` logic directly into `api.py` and standardized `ALLOWED_ORIGINS`.
- **Engineering PDF Enhancements:**
  - Integrated `matplotlib` for embedding high-fidelity horizontal bar charts of parameter sensitivity rankings in PDF exports.
  - Updated `pdf_service.py` to automatically include visual charts for "Sensitivity Ranking" sections when raw data is available.
- **Dependency Management:**
  - Updated `requirements.txt` to include `tiktoken`, `matplotlib`, and `stripe` while pinning major versions for stability.

### March 4, 2026 (Production Hardening & Monetization Security)
- **Stripe Security Hardening:**
  - Added **idempotency keys** to checkout sessions to prevent double charges on retries.
  - Implemented **webhook signature verification** with proper error handling.
  - **DO NOT create users after payment** - Stripe is now the source of truth; plans are only activated after `checkout.session.completed` webhook confirms payment.
  - Added full **subscription status tracking**: `stripe_customer_id`, `stripe_subscription_id`, `status` (active, canceled, trialing, past_due).
  - Added handlers for `customer.subscription.updated` and `customer.subscription.deleted` webhooks.
- **JWT Security:**
  - Enforced short-lived JWT configuration (30 min expiration check).
  - JWT secret rotation documented for production (use secrets manager, not .env in repo).
- **Rate Limiting:**
  - Redis-based rate limiting already implemented for login, signup, report generation, and AI calls.
- **Async Job Queue:**
  - Background tasks already implemented - returns `job_id` and uses polling pattern, does NOT block HTTP thread.
- **API Key Layer:**
  - Already implemented for B2B clients with hashed storage and per-key rate limiting.

### March 4, 2026 (Observability & Monitoring)
- **Structured Logging:**
  - Integrated `structlog` for JSON-formatted logging.
  - Added `request_id` to all requests via middleware.
  - Added `user_id` and Stripe event IDs to log context.
- **Prometheus Metrics:**
  - Added `/metrics` endpoint with `prometheus_client`.
  - Metrics: `http_requests_total`, `http_request_duration_seconds`, `ai_report_duration_seconds`, `pdf_generation_duration_seconds`.
- **Version Endpoint:**
  - Added `/api/v1/version` endpoint returning `version`, `git_commit`, `build_date` for enterprise clients.

### March 4, 2026 (Docker Production Hardening)
- **Redis Configuration:**
  - Removed hardcoded `REDIS_URL=redis://localhost:6379/0` (localhost in Docker = container itself).
  - Now set at runtime: `docker run -e REDIS_URL=redis://redis:6379/0`
- **Deterministic Builds:**
  - Pinned Python version: `python:3.11.8-slim@sha256:...`
- **Image Optimization:**
  - Added `.dockerignore` to exclude `.git`, `__pycache__`, `.env`, `node_modules`, tests.
  - Added `apt-get upgrade` for latest security patches.
  - Added `ENV PYTHONHASHSEED=random` for security.
- **Production Server:**
  - Worker count documented: 2 x CPU + 1 rule of thumb.

### March 4, 2026 (API Documentation)
- **SimHPC API Reference:**
  - Updated footer link to "SimHPC API Reference".
  - Added comprehensive API documentation page covering authentication, base URL, core endpoints (simulations, reports), rate limits, security, error handling, and webhooks.
  - Documented that AI processing is performed internally with no third-party AI API calls.

### March 4, 2026 (Legal Updates)
- **Data Processing Addendum (DPA):**
  - Expanded DPA page with full legal content covering roles, scope of processing, AI processing & model use (self-hosted, no external LLM APIs, no model training), infrastructure & subprocessors, data security measures, data retention, incident response, no sale/no model training certification, and governing law.
- **API Reference Page:**
  - Restored footer link to "API Reference".
  - Updated API Reference page with comprehensive copy matching provided documentation.
  - Verified PageLayout wrapper with Navigation and Footer.
- **Footer:**
  - Updated social links: X (https://x.com/SimHPC) and LinkedIn (https://www.linkedin.com/company/simhpc).
  - Changed "Documentation" to "Documents" in header and footer.
- **Header:**
  - Added spacing between SimHPC logo and navigation links on mobile (mr-4, ml-auto, whitespace-nowrap).
  - Increased gap between theme toggle and menu button on mobile (gap-3).

### March 4, 2026 (Docker Multi-Stage Build)
- **Multi-Stage Dockerfile:**
  - Implemented two-stage build: Builder (compilation) + Runtime (production).
  - Stage 1: Installs build tools (build-essential, cmake, gfortran, libs) and pre-compiles Python packages to `/install` prefix.
  - Stage 2: Copies only pre-compiled packages, excluding build tools from final image.
  - Benefits: ~40-50% smaller image size, reduced attack surface.
  - Added gunicorn access/error log streaming to stdout/stderr for cloud logging.
  - Redis URL documented as runtime env var.
  - Fonts vendored in image (no network fetch at build time).
- **RunPod Deployment:**
  - Created `simhpc_runpod.zip` containing: api.py, robustness_service.py, ai_report_service.py, pdf_service.py, auth_utils.py, requirements.txt, Dockerfile, .dockerignore, services/sensitivity.py, fonts/
  - Renamed font files to match pdf_service.py expectations: DejaVuSans.ttf, DejaVuSans-Bold.ttf, DejaVuSans-Oblique.ttf

- **S3/Object Storage for Reports:**
  - Integrated boto3 for S3, Cloudflare R2, or MinIO.
  - PDFs now uploaded to object storage with signed URLs (configurable expiration).
  - Fallback to direct response if S3 not configured.
  - Container filesystem is now ephemeral-safe.
- **Production Server:**
  - Replaced uvicorn with **gunicorn + uvicorn worker** (4 workers, 120s timeout).
  - Improved multi-worker stability.

### March 4, 2026 (Font & Build Improvements)
- **Vendored Fonts:**
  - Removed external network dependency for fonts at build time.
  - Added `COPY fonts ./fonts` to Dockerfile.
  - Eliminates GitHub rate-limit risk and non-deterministic builds.

### March 4, 2026 (Backend Hardening & Security Phase 3)
- **API & Simulation Logic:**
  - Fixed `method_map` NameError in `start_robustness` endpoint.
  - Resolved Redis bloat by stripping `telemetry` from `SimulationResult` before job state persistence.
  - Standardized on UTC timestamps (`timezone.utc`) across all backend services (API, Robustness, AI Report, and PDF).
  - Implemented `GET /api/v1/robustness/runs` endpoint for retrieving user simulation history.
  - Removed placeholder `escrowed` field from job state to align with current billing implementation.
- **Resilience & Maintenance:**
  - Implemented graceful shutdown in FastAPI `lifespan` hook, marking in-flight jobs as "interrupted" in Redis upon service termination.
  - Hardened `SimulationRunner` by re-seeding its RNG at the start of every analysis run for strict reproducibility.
  - Improved `AIReportService` reliability by adding assertions to prevent redundant retries when LLM clients are not configured.
- **Infrastructure & Export:**
  - Hardened `pdf_service.py` with a `has_custom_font` flag and Helvetica fallback to prevent service crashes when DejaVu fonts are missing.
  - Improved `api.py` code quality by removing redundant imports and dead-code environment variable checks.

### March 4, 2026 (Backend Hardening & Security Phase 2)
- **Auth & WebSocket Security:**
  - Implemented WebSocket authentication using JWT tokens passed via query parameters.
  - Refactored `auth_utils.py` to decouple JWT decoding from FastAPI dependencies, allowing reuse in WebSocket handlers.
  - Added ownership verification to telemetry streams to prevent cross-user data leakage.
- **Resource Management & Performance:**
  - Optimized Redis job scanning by replacing blocking `keys()` calls with `scan_iter` for O(N) safety in high-load environments.
  - Implemented proper singleton pattern for `AIReportService` and `RobustnessService` at the module level in `api.py` to ensure connection reuse across background tasks.
- **Reliability & Error Handling:**
  - Refactored `AIReportService` to isolate Kimi AI API calls into a dedicated retried method, preventing unnecessary retries when falling back to template-based generation.
  - Added critical secret validation (`SUPABASE_JWT_SECRET`) to the FastAPI `lifespan` startup hook to catch misconfigurations before the first request.
  - Cleaned up redundant environment variable checks and unused imports across `api.py` and `auth_utils.py`.
- **Infrastructure:**
  - Hardened font download logic in `Dockerfile` with `--fail` and existence checks to prevent silent build failures.

### March 4, 2026 (Development Environment Hardening)
- **Dependency Resolution:**
  - Diagnosed "Cannot find module" errors (React, React Router) as a file system limitation on the `D:` drive (exFAT).
  - **Issue:** exFAT cluster sizes and file count limitations caused `npm install` to fail with `ENOSPC` (No space left on device) despite having adequate free gigabytes.
  - **Fix:** Successfully verified the project and dependencies on an NTFS-formatted drive (`C:`).
  - **Action:** Recommended moving the development workspace to an NTFS volume to support the large number of small files in `node_modules`.
  - **Validation:** Confirmed `tsc` (TypeScript compiler) passes and the development server starts correctly when hosted on an NTFS volume.

### March 4, 2026 (Compliance & Documentation Expansion)
- **Legal & Compliance:**
  - Implemented **California Consumer Privacy Act (CCPA)** and **Data Processing Addendum (DPA)** pages.
  - Added a comprehensive **Cookie Policy** page.
  - Developed and integrated a global **Cookie Consent Banner** with persistent storage and California-specific opt-out logic.
- **Documentation & Reference:**
  - Created a dedicated **Documentation** page covering SUNDIALS, MFEM, and AI Engine integrations.
  - Launched an interactive **API Reference** page detailing endpoints, authentication, and error handling.
  - Added an **About** page detailing the SimHPC mission and engineering values.
- **Site Navigation & Footer:**
  - Streamlined Footer by removing Careers/Blog/GitHub and adding legal compliance links (CCPA, DPA).
  - Updated social media presence: Migrated Twitter icon to **X branding**.
  - Improved header navigation with direct links to Documentation and About.
- **Visual & Brand Consistency:**
  - Standardized **PageLayout** across all pages to ensure consistent header/footer and theme responsiveness.
  - Refined **SimHPC Logo** to ensure "SIM" text renders in absolute black during day mode for better brand definition.
  - Verified mobile responsiveness for all newly added pages and components.

### March 4, 2026 (Enhanced Technical Documentation)
- **Documentation Overhaul:**
  - Redesigned **Docs.tsx** with modern UI featuring ScrollArea component and Separator dividers.
  - Added comprehensive sections for **SUNDIALS** covering background, architectural integration, numerical capabilities, and use cases (CVODE, CVODES, IDA, IDAS, KINSOL).
  - Added detailed **MFEM Integration** documentation including high-order discretization, parallel performance, mesh handling, and engineering benefits.
  - Implemented **GLVis Visualization Pipeline** section covering WebGL rendering, interactive capabilities, robustness overlays, and diagnostic visualization.
  - Documented **AI Report Generator** with system architecture, deterministic engineering focus, workflow impact, and tier integration details.
  - Added anchor navigation links in header for quick section jumping (SUNDIALS, MFEM, GLVis, AI Report Generator).
  - Integrated **PageLayout** wrapper to match header/footer consistency with other pages.
  - Included legal disclaimer footer consistent with SimHPC terms.

### March 4, 2026 (About Page Refresh)
- **Content Overhaul:**
  - Updated **About.tsx** with comprehensive company messaging covering SimHPC's cloud-native simulation platform, high-order finite elements, adaptive time integration, GPU compute, and automated robustness analysis.
  - Emphasized key value propositions: no cluster management, no solver tuning, no manual report writing.
  - Included company mission statement: "Run simulations. Measure robustness. Deploy with confidence."

### March 4, 2026 (UI Enhancement)
- **Navigation Updates:**
  - Changed "Get Started" button to white background in dark/night mode for better visibility.
  - Updated both desktop and mobile menu buttons for consistent styling.

### March 4, 2026 (Legal Updates)
- **Contact Information:**
  - Changed email in **Terms.tsx** from legal@simhpc.com to info@simhpc.com
  - Changed email in **Privacy.tsx** from privacy@simhpc.com to info@simhpc.com
- **Navigation:**
  - Verified "Features" links in header and footer correctly point to `/` with `#features` anchor, linking to the Stack section with Deterministic Physics Core, Browser-Native Visualization, Integrated Robustness Analysis, and AI Technical Report Layer cards.

### March 4, 2026 (Cookie Policy Update)
- **Content Overhaul:**
  - Updated **CookiePolicy.tsx** with comprehensive cookie policy covering overview, types of cookies (essential, authentication, payment processing, analytics, performance), third-party cookies, retention periods, cookie management, Do Not Track signals, and policy update procedures.

### March 4, 2026 (California Privacy Notice Update)
- **Content Overhaul:**
  - Updated **CCPA.tsx** to "California Privacy Notice" with comprehensive content covering categories of personal information, sources, purposes, sale/sharing disclosures, retention, California resident rights, request submission process, verification process, Do Not Track signals, and update procedures.
  - Updated contact email to info@simhpc.com.

### March 4, 2026 (Contact Page)
- **New Page:**
  - Created **Contact.tsx** with sales (deploy@simhpc.com), information (info@simhpc.com), and support (support@simhpc.com) contact options.
  - Added route in App.tsx for /contact path.

### March 4, 2026 (Browser Compatibility)
- **Firefox/LibreWolf Support:**
  - Added Firefox-compatible scrollbar styles using `scrollbar-width` and `scrollbar-color` CSS properties.
  - WebKit scrollbar styles now have Firefox fallbacks for cross-browser compatibility.
- **Cookie Consent:**
  - Removed "CA" from Opt-out button in CookieConsent.tsx.

### March 4, 2026 (Auth & Report Hardening)
- **Supabase Integration:**
  - Implemented Google OAuth and Email Magic Link sign-in in `SignIn.tsx`.
  - Added `supabase.ts` client and `useAuth` hook for frontend session management.
  - Created `auth_utils.py` for backend JWT verification.
  - Updated `api.py` to use Supabase JWT for authenticated requests.
- **Kimi AI SDK:** Added `openai>=1.0.0` to requirements.txt (Moonshot AI uses OpenAI-compatible API)
- **AI Report Service:**
  - Implemented Kimi API calls with proper system prompts for scientific tone
  - Made template generation data-driven by parsing JSON context from prompts.
  - Tightened temperature integrity regex (`\b\d{2,4}(?:\.\d+)?\s*K\b`) to prevent false positives.
  - Converted `get_ai_report_service` to a proper singleton for multi-worker efficiency.
  - Added HTML escaping and newline normalization (\n/\r\n) to `to_html()` for XSS prevention and consistent rendering.
- **Fallback System:** Graceful fallback to template generation if Kimi API unavailable
- **Dockerfile:**
  - Added environment variables for KIMI_API_KEY, KIMI_MODEL, SUPABASE_JWT_SECRET, SIMHPC_API_KEY
  - Added auto-download of DejaVu fonts if not present
  - Added HEALTHCHECK for container orchestration
  - Optimized layer caching (system deps → requirements → app code)
- **API (api.py):**
  - Lazy API key validation (no runtime error if not set at import)
  - Redis connection validation at startup
  - Graceful handling when API key not configured
- **PDF Service:** Added font path hardening with multiple fallback locations
- **Dockerignore:** Created to reduce build context size

### March 3, 2026 (Bug Fixes & Security Hardening)
- **API (api.py):**
  - Fixed corrupted `RobustnessRunRequest` Pydantic model.
  - Fixed active run counter by using `hget` on Redis hashes instead of `get`.
  - Removed redundant `.decode()` calls in `get_job()` (handled by `decode_responses=True`).
  - Decoupled AI report plan check from run submission to allow flexible generation.
  - Removed hardcoded fallback API key; service now requires `SIMHPC_API_KEY` environment variable.
  - Implemented real JWT verification using `python-jose` with `JWT_SECRET_KEY` support.
  - Optimized PDF endpoint to use `BytesIO` and `Response` for direct streaming without disk I/O.
  - Fixed `UserPlan` enum normalization in background tasks.
- **Robustness Service (robustness_service.py):**
  - Fixed `non_convergent_count` type mismatch in results summary.
  - Added seeded RNG to `SimulationRunner` for fully reproducible physics approximations.
  - Implemented `MAX_CACHE_SIZE` for `baseline_cache` with FIFO eviction to prevent memory leaks.
  - Improved `_percentage_sampling` to use true uniform distribution instead of alternating sweeps.
  - Added graceful fallback for `SobolAnalyzer` when enterprise modules are missing.
  - Fixed `run_robustness_analysis` signature mismatch in demo code.
- **AI Report Service (ai_report_service.py):**
  - Made template generation data-driven by parsing JSON context from prompts.
  - Tightened temperature integrity regex (`\b\d{2,4}(?:\.\d+)?\s*K\b`) to prevent false positives.
  - Converted `get_ai_report_service` to a proper singleton for multi-worker efficiency.
  - Added HTML escaping and newline normalization (\n/\r\n) to `to_html()` for XSS prevention and consistent rendering.- **Infrastructure (pdf_service.py & Dockerfile):**
  - Resolved font loading failures by using paths relative to `__file__`.
  - Hardened Docker image with `appuser` non-root account and proper permission ownership.
  - Streamlined container startup by running `uvicorn` directly, removing redundant CORS middleware layers.

### March 2, 2026
- **Visual Design:** Updated day mode background to premium off-white (#F1EDE0).
- **Navigation:** Decoupled Pricing from landing page into a dedicated high-conversion page.
- **Billing Integration:** Integrated Stripe/Clover checkout sessions with tiered compute plans.
- **Responsive UX:** Implemented mobile-first sidebar drawer and header for the Dashboard.
- **Frontend Refactoring:** Standardized layout components (Navigation/Footer) across all routes.
- **Deployment:** Successfully deployed frontend to GitHub Pages (https://github.com/NexusBayArea/SimHPC).
- **Backend Sync:** Unified CORS for production and fixed missing dependencies for RunPod updates.

### March 1, 2026
- **Distributed State:** Migrated from in-memory to Redis-backed job storage and rate limiting.
- **Scientific AI Governance:** Enforced length and keyword constraints on all engineering reports.
- **Numerical Verification:** Added automated anchor system to verify AI reports against solver metrics.
- **Compute Efficiency:** Implemented baseline caching and clamped input perturbations.
- **Resilient AI:** Integrated Tenacity retry logic for more reliable LLM report generation.
- **Unified Auth:** Implemented middleware supporting both JWT and X-API-Key authentication.
- **Monte Carlo:** Added standard Monte Carlo sampling method for baseline uncertainty studies.
- **Distributed Architecture:** Transitioned from monolithic API to Orchestrator-Worker pattern using Docker Compose.

---

## Architectural Improvements

### AI Report Service (`ai_report_service.py`) ✅ COMPLETED

#### 1. Multi-User Safe Cache System ✅
- **Current:** File-based cache (`./ai_report_cache`) without user/simulation scoping
- **Issues:** No expiration, no concurrency protection, race conditions on parallel writes
- **Fix:** Migrate to Redis-backed cache with per-user and per-simulation scoping, TTL enforcement, and atomic operations

#### 2. Stable Report ID Hashing ✅
- **Current:** `json.dumps(data, sort_keys=True)` vulnerable to float precision drift and dict ordering
- **Fix:** Normalize floats (round), strip metadata fields, define canonical schema before hashing

#### 3. Enhanced Vocabulary Enforcement ✅
- **Current:** Only enforces prohibited phrases
- **Fix:** 
  - Enforce allowed indicator usage
  - Block speculative language
  - Block modal certainty drift
  - Add Pydantic validation for structured JSON output from LLM

#### 4. Singleton Pattern Safety ✅
- **Current:** Global singleton not safe for multi-worker Uvicorn/Gunicorn
- **Fix:** Remove reliance on singleton for shared cache; use Redis for all shared state

#### 5. Deterministic Metadata Lock ✅
- **Current:** Only stores `input_hash` and `version`
- **Fix:** Add structured metadata:
  - `simulation_id`, `solver_version`, `mesh_checksum`, `parameter_hash`
  - `ai_prompt_version` for cache versioning

---

### Robustness Service (`robustness_service.py`) ✅ COMPLETED

#### 1. Deterministic Isolation ✅
- **Principle:** Robustness layer must NEVER call AI, modify solver outputs, or reformat results
- **Contract:** `run_simulation(params) → raw_result`, `aggregate_results(results) → statistics`

#### 2. Random Seed Control (Enterprise Critical) ✅
- **Current:** No seed parameter or logging
- **Fix:** 
  - Accept user-defined seed parameter
  - Log seed in metadata: `random.seed(user_defined_seed)`, `np.random.seed(user_defined_seed)`
  - Return seed in metadata for reproducibility

#### 3. Concurrency & GPU Safety ✅
- **Current:** ThreadPoolExecutor for CPU-bound work
- **Fix:** Use `ProcessPoolExecutor` or external worker system; implement GPU over-subscription guards

#### 4. Sensitivity Ranking Correctness ✅
- **Fix:** 
  - Normalize influence coefficients
  - Guard against zero variance with epsilon
  - Handle signed values and ranking stability for close values

#### 5. Non-Convergence Handling ✅
- **Fix:**
  - Track failed runs separately
  - Exclude from variance calculations
  - Log all non-convergent cases with reason

#### 6. Statistical Integrity ✅
- **Current:** Confidence intervals assume normal distribution
- **Fix:** Document distribution assumption in metadata

#### 7. Structured Output ✅
- **Fix:** Return structured object:
  ```python
  {
    "raw_results": [...],
    "statistics": {...},
    "metadata": {
      "seed", "sampling_method", "run_count", "solver_version"
    }
  }
  ```

---

### API Layer (`api.py`) ✅ COMPLETED

#### 1. Authentication Enforcement ✅
- **Critical:** All protected endpoints must validate JWT and extract user ID
- **Never trust frontend for plan checks or rate limits**

#### 2. Token/Plan Enforcement (Backend) ✅
- **Enforce inside API layer:**
  ```python
  if user.plan == "free" and run_count > 5:
      raise HTTPException(403)
  ```

#### 3. AI Report Endpoint Metering ✅
- **Critical:** Check subscription, deduct tokens, prevent double deduction
- **Implement idempotency key to prevent retry charges**

#### 4. Background Tasks for Long-Running Simulations ✅
- **Current:** Blocking request handler
- **Fix:** Submit job → Return job_id → Poll status → Store results

#### 5. Input Validation ✅
- **Fix:** Use Pydantic models for all request types to prevent missing fields, type mismatches, and malicious payloads

#### 6. Rate Limiting ✅
- **Apply to:** Report generation, simulation runs, status polling
- **Use Redis-backed rate limiters

---

### Enterprise Readiness Gaps ✅ COMPLETED

Required for enterprise clients:
- [x] Solver version logged in all responses
- [x] Random seed logged and returned in metadata
- [x] Reproducibility guarantee with seed
- [x] Raw run data export capability
- [x] AI report versioning
- [x] Robustness algorithm versioning

### Tiered Access Model

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

## Technical Summary

### Live Architecture
- **Website (Frontend):** Deployed to GitHub Pages (https://github.com/NexusBayArea/SimHPC)
- **Physics Core (Backend):** NVIDIA A40 GPU Instance on RunPod
- **API Endpoint:** Available via RunPod proxy

---

## Deployment & Production

### Backend Orchestrator Deployment
1. **Set Environment Variables:**
   ```bash
   export SUPABASE_JWT_SECRET="your-supabase-jwt-secret"
   export SIMHPC_API_KEY="your-api-key"
   ```
2. **Rebuild & Run:**
   ```bash
   docker build -t robustness-orchestrator .
   docker run -d -e SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET robustness-orchestrator
   ```

### Frontend Deployment
- Deploy from GitHub repository: https://github.com/NexusBayArea/SimHPC
- Changes to `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env` are automatically picked up via GitHub Actions.
- Ensure **Google OAuth** is enabled in the Supabase Dashboard under Authentication > Providers.

## March 6, 2026 - Mercury AI Migration

### AI Provider Migration: Kimi → Mercury (Inception Labs)
- **Replaced Kimi AI (Moonshot)** with **Mercury AI (Inception Labs)** for report generation
- **Environment Variables:**
  - `MERCURY_API_KEY` - API key for Mercury (Inception Labs)
  - `MERCURY_MODEL` - Model name (default: `mercury-2`)
- **Updated `ai_report_service.py`:**
  - Added standalone `generate_ai_report()` function for direct Mercury API calls
  - Updated `AIReportService` class to use Mercury instead of Kimi
  - Implemented production-grade prompt with engineering report sections
  - Added timeout protection (30s) to prevent API hangs
  - Updated prompt version to `v1.3`
- **Cost Optimization:**
  - Temperature: 0.2, Max tokens: 1200
  - Free tier: 1M tokens (~200 reports)

### Critical Bug Fixes (March 6, 2026)

#### Security & Startup
1. **auth_utils.py** - Fixed missing `raise` for missing `SUPABASE_JWT_SECRET` (was only logging error)
2. **api.py** - Fixed duplicate logger definition (removed stdlib logger overwriting structlog)
3. **api.py** - Fixed verify_auth blocking all requests when API_KEY is unset (now only requires API_KEY when x-api-key header is provided)
4. **api.py** - Fixed Redis lifespan not raising on connection failure (now raises RuntimeError)

#### Stripe Integration
5. **api.py** - Fixed Stripe webhook not expanding line_items (now retrieves session with expand=["line_items"])
6. **api.py** - Fixed idempotency_key parameter name for Stripe SDK v5+ (changed to `stripe_idempotency_key`)
7. **app/index.html** - Fixed wrong Stripe JS URL (`/clover/stripe.js` → `/v3/`)

#### Celery & Tasks
8. **tasks.py** - Fixed circular import by creating `_core/constants.py` with PLAN_LIMITS and UserPlan
9. **tasks.py** - Fixed cancellation not working (added Redis-based cancel signal check)
10. **tasks.py** - Fixed AI service instantiation per task (now uses singleton pattern)
11. **tasks.py** - Fixed event loop issue (now properly creates/closes loop)
12. **tasks.py** - Added max_retries=0 to prevent retry loops

#### Event Loop Fixes
13. **robustness_service.py** - Fixed run_robustness_analysis_sync event loop pattern
14. **ai_report_service.py** - Fixed generate_report_sync event loop pattern

#### Dependencies
15. **requirements.txt** - Added missing dependencies: structlog, prometheus-client

#### Other Fixes
16. **pdf_service.py** - Added matplotlib Agg backend for headless container environment

### March 10, 2026 (Canonical Backend Reorganization)
- **Source of Truth Consolidation**: Successfully migrated all core backend logic (`api.py`, `robustness_service.py`, `ai_report_service.py`, etc.) from the temporary `tmp_backend` staging area to the root `robustness_orchestrator/` directory.
- **Monorepo Structure**: established a clean monorepo architecture with `simhpc-frontend/` for UI development and `robustness_orchestrator/` for backend, AI, and physics logic.
- **Supporting Assets**: Moved `sdk/`, `docs/`, `docker-compose.yml`, and `setup_runpod.sh` to the root directory to ensure they are readily discoverable and maintainable.
- **Deployment Stability**: Verified that the Docker multi-stage build and RunPod deployment scripts now point to the correct canonical paths, reducing the risk of "missing file" errors during pilot onboarding.

### March 10, 2026 (Alpha Pilot Shipping Preparation)
- **Dockerfile Environment Variables**: Updated the multi-stage Docker build to "bake in" `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` as build arguments, ensuring the static frontend can communicate with the authentication and RAG layers.
- **Nginx SPA Routing**: Verified `nginx.conf` includes the `try_files` catch-all directive to prevent 404 errors on deep links like `/demo/:token` during pilot exploration.
- **Backend CORS Relaxation**: Updated `api.py` to allow all origins (`*`) during the Alpha period, facilitating access across diverse deployment and proxy environments (RunPod, local, etc.).
- **User Documentation**: Created `ALPHA_PILOT_GUIDE.md` as a quick-start manual for pilots to navigate simulations, AI reports, and the demo token system.

### March 10, 2026 (Global Branding & Repository Polish)
- **Global Identity Update**: Performed a final comprehensive audit and replacement of all legacy `btwndlinez` references with `NexusBayArea` across all markdown documentation.
- **Documentation Synchronization**: Synchronized `progress.md` across all sub-repositories and temporary backend directories to ensure a unified project history.
- **Repository Metadata**: Verified that all internal documentation reflects the current split-repository strategy and canonical source locations.

---

*Last Updated: March 10, 2026*

### March 10, 2026 (Alpha Control Room Redesign)
- **4-Panel HPC Terminal Layout**: Complete rebuild of `/dashboard/alpha` with a premium dark trading terminal aesthetic.
  - **Live Signals Panel** (left sidebar): Real-time temperature, grid load, energy price, solar output with rolling SVG sparkline micro-charts (20-point history).
  - **Active Simulations Panel** (top-right): Live simulation registry with animated status badges and dispatch button.
  - **Simulation Memory Panel** (bottom-right): Archive of completed/failed past runs with status indicators.
  - **Simulation Insights Feed** (bottom-right): Auto-scrolling AI observation log with confidence bars and suggested actions.
  - **Notebook/Analysis Panel**: Compact launch bar for Jupyter and data export.
- **New UI Components**: `Sparkline` (inline SVG charts), `UTCClock` (live UTC time), `StatusBadge` (color-coded simulation status).
- **System Status Footer**: Live indicators for GPU cluster, SUNDIALS solver, Mercury AI, and Supabase sync.
- **Signal History Tracking**: Accumulates signal values over time for sparkline visualization, giving the dashboard a "feel alive" quality.
- **Framer Motion Animations**: Entry animations on simulation rows, insight items, and signal value changes.

### March 10, 2026 (NexusBayArea Migration & Final Alpha Polish)
- **Ownership Migration**: Successfully moved all project infrastructure, repositories, and deployment targets from `btwndlinez` to `NexusBayArea`.
- **Vercel Polish**: Cleaned up legacy deployment URLs and updated configuration to point to the new production environment.
- **Documentation Update**: Performed a global audit of all markdown files to ensure consistent branding and accurate repository links.
- **Alpha RunPod Architecture**: Implemented a unified worker container architecture combining FastAPI, vLLM for ultra-fast inference, and a FAISS-based RAG service for engineering context retrieval.
- **vLLM Integration**: Configured vLLM for high-throughput generation (~90 tok/s on RTX 3090) supporting Mistral and Llama models.
- **RAG Service Implementation**: Developed a retrieval-augmented generation system using SentenceTransformers and FAISS, enabling the AI to answer questions based on SimHPC documentation.
- **Backend RunPod Proxy**: Added `AlphaChatRequest` and `/api/v1/alpha/chat` endpoint to the main orchestrator, proxying authorized chat requests to the Serverless LLM worker.
- **Serverless Lifecycle Management**: Updated `RunPodClient` to handle async job submission and status polling for the new LLM and RAG capabilities.
- **Worker Packaging**: Scaffolded `alpha_worker/` directory with Dockerfile, requirements, and modular application code for immediate deployment.

---

### March 10, 2026 (Footer Logo, Global Background & Theme Toggle)
- **Protected Routes**: Implemented `ProtectedRoute` component and wrapped dashboard routes (`/dashboard`, `/dashboard/alpha`, `/dashboard/notebook`) to prevent unauthorized access.
- **Experiment Notebook Alignment**: Fixed responsive grid layout and row alignment issues in both light and dark modes to prevent card overlap and squishing.
- **Theme-Aware Styling**: Refactored `ExperimentNotebook.tsx` to use `bg-background` and `text-foreground` classes, ensuring proper color adaptation during mode switches.
- **Footer Logo Color Fix**: Changed SimHPC logo "Sim" text to `text-inherit` to properly adapt to the footer's dark background across all themes.
- **Global Background Consistency**: Updated all page backgrounds (SignIn, SignUp, Dashboard, etc.) to use `bg-background` (HSL 46° 38% 91%) matching the homepage color #F1EDE0.
- **ExperimentNotebook Theme Toggle**: Added ThemeToggle component to the Experiment Notebook page header, matching the rest of the website's bright/dark mode functionality.
- **Notebook Color Updates**: Updated all hardcoded colors in ExperimentNotebook.tsx to use theme-aware classes (dark: prefix) for proper light/dark mode support.

### March 10, 2026 (Magic Link Demo Token System)
- **Magic Link Demo Access:**
  - Implemented a complete alpha pilot onboarding system using secure, usage-limited magic link tokens.
  - **Backend (`demo_access.py`):**
    - `POST /api/v1/demo/magic-link` — Validates demo token and returns session info with remaining runs.
    - `GET /api/v1/demo/usage` — Returns current usage stats (remaining, limit, used, expired).
    - `POST /api/v1/demo/use-run` — Atomically decrements usage count per simulation run.
    - `POST /api/v1/demo/create` — Admin-only endpoint to generate new magic links (requires `SIMHPC_API_KEY`).
  - **Supabase `demo_access` Table:**
    - Schema: `id`, `email`, `token_hash` (SHA-256), `usage_limit`, `usage_count`, `expires_at`, `created_at`, `ip_address`.
    - RLS policy restricts access to `service_role` only.
    - Indexes on `token_hash` and `email` for fast lookups.
  - **Dual-Layer Storage:** Supabase (persistent) + Redis (fast reads) for redundancy.
  - **Security:** Tokens stored as SHA-256 hashes — raw tokens never persisted. IP logging on all validation attempts.
- **Frontend Changes:**
  - **`DemoAccess.tsx`**: New `/demo/:token` route page with animated validation flow (validating → success → redirect to dashboard).
  - **`DemoBanner.tsx`**: Dashboard banner showing remaining demo runs with progress bar, color-coded warnings (blue → amber → red), and upgrade CTAs.
  - **`Dashboard.tsx`**: Integrated demo state tracking — reads from localStorage, refreshes via API on mount, decrements usage on each simulation run.
  - **`api.ts`**: Added `validateDemoToken()`, `getDemoUsage()`, and `decrementDemoUsage()` methods with `DemoValidationResponse` and `DemoUsageResponse` interfaces.
  - **`App.tsx`**: Registered `/demo/:token` route.
- **CLI Tool (`generate_demo_link.py`):**
  - Two modes: API (talks to running backend) and Direct (writes to Redis/Supabase locally).
  - Outputs formatted magic link ready to send to alpha pilots.
  - Usage: `python generate_demo_link.py --email pilot@coreshell.com --runs 5`
- **Demo Flow:**
  ```
  Generate link → Send to pilot → Pilot clicks → Token validated → Session created →
  Dashboard with usage banner → 5 simulations allowed → Demo ends → "Request More Access"
  ```

### March 8, 2026 (Abuse Prevention & Free Tier Security)

#### Abuse Prevention Architecture
Implemented a multi-layered security strategy to prevent free tier exploitation and protect expensive GPU resources:

1.  **Identity Verification (First Barrier):**
    - Enforced **Google OAuth** or **Verified Email Link** (Magic Link) for all signups via Supabase.
    - Disabled unverified disposable email registration.

2.  **Fingerprinting & Hardware Tracking:**
    - Implemented `user_security` tracking storing: `ip_address`, `device_hash` (browser-native fingerprint), `user_agent`, and `signup_time`.
    - **Device Fingerprint:** Generated from browser primitives (User Agent, Language, Screen Resolution) to identify unique hardware even behind VPNs.

3.  **Cross-Account Linking Prevention:**
    - **Limit:** Max 2 free accounts per IP.
    - **Limit:** Max 1 free account per device.
    - Automated blocking of new signups exceeding these thresholds.

4.  **Compute Guardrails (Resource Protection):**
    - **Free Tier Limits:**
        - 1 concurrent simulation max.
        - Mandatory small mesh limit.
        - Hard execution timeout (60 seconds).
        - No batch runs or AI reports.
    - **Cost Estimation:** Pre-simulation check for estimated compute cost; runs exceeding the free limit are blocked before GPU allocation.

5.  **Queue & Rate Management:**
    - **Delayed Execution:** Free tier jobs are assigned to a low-priority queue with a mandatory 30–120 second delay to discourage bot-driven bulk processing.
    - **API Rate Limiting:** 5 API calls per minute for free users via Redis-backed rate limiters.

6.  **Bot Mitigation:**
    - **Invisible Honeypot:** Added hidden form fields in signup/login to trap and block automated bot submissions.

7.  **Friction-Based Escalation:**
    - **Credit Card Trigger:** After 5 free simulations, users must provide a card (Stripe SetupIntent) to continue, even if remaining on the free tier.

8.  **Abuse Monitoring Dashboard:**
    - Implemented real-time tracking of `accounts_per_ip` and `free_to_paid` conversion rates to identify emerging abuse patterns.

#### Free Tier Technical Specification
| Feature | Free Tier Policy |
|---------|------------------|
| Simulations | 1 concurrent |
| Mesh Size | Small only |
| Runtime | 60s maximum |
| AI Reports | Disabled |
| Queue Priority | Low (Delayed) |
| Account Limit | 1 per device / 2 per IP |
| Rate Limit | 5 calls/minute |

#### Security Posture & Production Deployment Strategy
Implemented a secure, isolated deployment architecture to protect core intellectual property (AI/Physics logic) during beta:

1.  **Frontend Repository:**
    - Hosted at: https://github.com/NexusBayArea/SimHPC
    - **Purpose:** GitHub Pages deployment, ensuring the backend codebase, AI logic, and orchestrator secrets remain protected.
    - **Hardened `.gitignore`:** Aggressively excludes all backend folders (`robustness_orchestrator/`, `ai/`, `sdk/`), Python files, and Docker configurations.

2.  **Backend/AI Privacy:**
    - Established "Backend Closed-Source" policy: Core business logic (MFEM/SUNDIALS integration, Mercury AI RAG, PDF generation) remains in a private monorepo or local git.
    - Deployment to RunPod GPU instances is managed directly from the private environment.

3.  **Supabase Standalone Configuration:**
    - **Workflow:** Managed via the Supabase Dashboard and local CLI (`supabase db push`), bypassing the need to sync the monorepo or create a separate schema repo.
    - Protects the database schema and RLS policies from being linked to the frontend repository.

4.  **Security Checklist:**
    - [x] Create `simhpc-frontend` repo with only frontend code.
    - [x] Add hardened `.gitignore` for frontend isolation.
    - [x] Disconnect/Prevent Supabase from requiring full repo access.
    - [x] Host monorepo privately (local + RunPod volume backups).
    - [x] Configure GitHub Pages deployment from NexusBayArea/SimHPC.

#### Experiment Notebook (New Feature)
Launched a persistent research workspace for automated experiment tracking and knowledge management:

1.  **Automated Logging:** Every simulation run now generates a structured experiment entry with parameters, results, and metadata.
2.  **Comparison Engine:** Side-by-side comparison of multiple experiments (e.g., C-rate sweeps, thermal stability studies) to identify optimal engineering parameters.
3.  **Observation & Conclusion:** Researchers can add qualitative observations and final conclusions to each experiment, building a searchable knowledge base.
4.  **Replay Capability:** One-click "Replay" to reload all parameters and solver configurations from any past experiment into the active dashboard.
5.  **Visual Analytics:** Integrated sparklines and mini-bar charts for rapid assessment of parameter variation effects on convergence and stability.
6.  **Timeline Tracking:** Visual history of experiments grouped by research phase, facilitating long-term study continuity.
7.  **Dashboard Integration:** Dedicated sidebar navigation with "New Feature" badge and responsive collapse states.

### March 9, 2026 - Alpha Control Room Launch
- **"Alpha Control Room" Dashboard:**
    - Implemented a high-fidelity HPC/Trading-style control room at `/dashboard/alpha`.
    - Integrated **Live System Feed** streaming weather (Open-Meteo) and mock grid data in real-time.
    - Added **Simulation Insight Feed**: AI-driven real-time observations and suggestions based on telemetry.
    - Added **Active Simulations** monitor with status tracking (Running, Completed, Idle).
    - Integrated **Notebook / Analysis** quick-launch for Jupyter-driven research.
- **Backend Orchestration (api.py):**
    - Added dedicated `/api/v1/alpha/` endpoint group for signals, insights, simulation history, and triggers.
    - Integrated **Supabase Client** (v2.3) for persistent simulation run logging.
    - Implemented **Open-Meteo API** integration for live environmental signals.
- **Documentation & Deployment:**
    - Updated `ARCHITECTURE.md` and `ROADMAP.md` to reflect the Alpha Control Room and Insight Feed.
    - Registered `/dashboard/alpha` route in the frontend application.

### March 9, 2026 - GitHub Deployment
- **Repository Created:** https://github.com/NexusBayArea/SimHPC (Public)
- **Initial Push:** Successfully deployed main branch to GitHub
- **Git Config:** Updated global credentials for NexusBayArea
- **Documentation:** Created ARCHITECTURE.md, CHANGELOG.md, ROADMAP.md
- **Cleanup:** Removed Vercel configurations, updated all references to GitHub Pages

### March 9, 2026 - Tier-Aware API & Supabase Sync
- **Supabase-Driven Tier Enforcement:** Implemented `verify_user_tier` to query the `profiles` table using the Supabase Service Role Key for real-time plan verification.
- **Simulation History Persistence:** Developed `save_result_to_supabase` to insert simulation results and summaries into the `simulation_history` or `simulations` tables.
- **Frontend Mutation Logic:** Integrated `useMutation` in the simulation dashboard for launching jobs with automated toast-based feedback.
- **Stripe Success UX:** Added a `PaymentSuccess` component with `react-confetti` and automated redirect to ensure a smooth post-purchase experience.

### March 9, 2026 - Google One Tap Integration
- **Implemented Google One Tap (GIS):** Added `g_id_onload` and `g_id_signin` components for frictionless authentication.
- **JWT Handling:** Configured `handleCredentialResponse` callback to process and verify Google-issued JWT ID tokens.
- **UX Configuration:** Enabled popup mode (`data-ux_mode="popup"`) and automatic prompting (`data-auto_prompt="false"` for controlled triggering).
- **Library Integration:** Added async loading of `https://accounts.google.com/gsi/client`.
