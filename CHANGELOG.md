# SimHPC Changelog

> All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2026-03-10

### Added
- **Alpha Control Room Redesign**: Complete rebuild of `/dashboard/alpha` with HPC trading terminal aesthetic.
  - **Live Signals Panel**: Real-time temperature, grid load, energy price, and solar output with SVG sparkline history graphs.
  - **Active Simulations Panel**: Live simulation registry with animated status badges (`running`, `completed`, `queued`, `failed`).
  - **Simulation Memory Panel**: Past simulation runs archive with status and timestamp display.
  - **Simulation Insights Feed**: Auto-scrolling AI observation log with confidence bars, icons, and suggested actions.
  - **Notebook/Analysis Panel**: Compact launch bar for Jupyter integration and data export.
  - **System Status Footer**: Live status indicators for GPU cluster, SUNDIALS solver, Mercury AI, and Supabase.
  - **UTC Clock**: Live UTC time display in header.
  - **Signal Sparklines**: Rolling 20-point SVG micro-charts for each signal.

---


### Added
- **Alpha RunPod Container Architecture**: New unified worker container for high-performance LLM and RAG services.
  - **vLLM Inference**: Integrated vLLM engine for ultra-fast Mistral/Llama inference (~90 tok/s).
  - **RAG Service**: FAISS-based vector store for engineering context retrieval from documentation.
  - **FastAPI Layer**: Dedicated API for Alpha chat and document management inside the worker.
  - **RunPod Serverless Integration**: Full async lifecycle management for Alpha chat requests in the main orchestrator.
- **Backend RunPod Client**: New `RunPodClient` in `api.py` for managing Serverless jobs, status polling, and result retrieval.
- **Alpha Chat Endpoint**: `POST /api/v1/alpha/chat` for secure engineering assistant interactions.

---

## [1.4.0] - 2026-03-10

### Added
- **Magic Link Demo Tokens**: Complete alpha pilot onboarding system with secure, usage-limited demo links.
  - `POST /api/v1/demo/magic-link` — Validate demo token and create session
  - `GET /api/v1/demo/usage` — Check remaining simulation runs
  - `POST /api/v1/demo/use-run` — Decrement usage counter per simulation
  - `POST /api/v1/demo/create` — Admin endpoint to generate new magic links
- **Supabase `demo_access` Table**: Persistent storage with SHA-256 hashed tokens, usage limits, expiration, and IP logging.
- **Frontend Demo Landing Page (`DemoAccess.tsx`)**: Animated magic link validation with status feedback (validating → success → redirect).
- **Dashboard Demo Banner (`DemoBanner.tsx`)**: Live usage counter with progress bar, color-coded warnings, and upgrade CTAs.
- **CLI Tool (`generate_demo_link.py`)**: Standalone script for generating demo links via API or direct Redis/Supabase mode.
- **Demo Tier (`demo_magic`)**: New plan tier with configurable run limits (default 5) and 7-day expiration.

### Security
- Tokens stored as SHA-256 hashes — raw tokens never persisted in database.
- Admin demo creation endpoint requires `SIMHPC_API_KEY` authentication.
- IP logging on all demo token validation attempts.
- Redis + Supabase dual-layer storage for redundancy and fast reads.

---

## [1.3.1] - 2026-03-10

### Added
- **Protected Routes**: Implemented `ProtectedRoute` component to prevent unauthorized access to dashboard pages. Users are now redirected to the sign-in page if they are not authenticated.
- **Tier-Aware API**: Backend now queries Supabase `profiles` table directly to enforce plan limits (`free` vs `professional`).
- **Supabase Persistence**: Simulation results and summaries are now inserted into the `simulations` table using the Service Role Key.
- **Frontend Mutation Hooks**: Implemented `useMutation` for launching simulations with automated toast notifications and error handling.
- **Payment Success UX**: Added animated success page with confetti and 5-second redirect after Stripe checkout.

### Added
- **ExperimentNotebook Theme Toggle**: Added bright/dark mode toggle to the Experiment Notebook page matching the rest of the website.

### Fixed
- **Experiment Notebook Alignment**: Fixed responsive grid layout and row alignment issues in both light and dark modes.
- **Footer Logo Color**: Fixed SimHPC logo "Sim" text to inherit parent color for proper visibility in footer across all themes.
- **Global Background Consistency**: Updated all page backgrounds (SignIn, SignUp, Benchmarks, Docs, Pricing, About, Contact, APIReference, etc.) to match homepage color #F1EDE0.
- **Theming**: Updated global day background color to `#F1EDE0` for better visual consistency across all pages.

---

## [1.3.0] - 2026-03-09

### Added
- **Google One Tap Sign-In**: Integrated Google Identity Services (`g_id_onload`, `g_id_signin`) for frictionless authentication.
- **GitHub Pages Deployment**: Migrated frontend hosting to GitHub Pages (https://github.com/NexusBayArea/SimHPC).

---

## [1.2.0] - 2026-03-08

### Added
- **Experiment Notebook**: A persistent research workspace for automated logging, side-by-side experiment comparison, and "Replay" capability for solver parameters.
- **Abuse Prevention System**: Multi-layered security including device fingerprinting, IP-based account limits, honeypot fields, and compute guardrails (60s timeouts, delayed queues).
- **Mercury AI Integration**: Finalized transition to Inception Labs' Mercury AI for engineering-grade reports with numerical anchoring.
- Secure Repo Strategy: Migrated to a split-repository architecture, isolating the frontend in `lostbobo` (https://github.com/NexusBayArea/lostbobo.git) while keeping backend and AI logic closed-source.


### Security
- Implemented frontend-only repository strategy for Vercel deployment.
- Hardened `.gitignore` to prevent accidental exposure of backend orchestrator logic.
- Disconnected Supabase from GitHub sync to prevent unauthorized schema access.

---

## [1.1.0] - 2026-03-06

### Added
- **Mercury AI Migration**: Replaced Kimi AI with Mercury (Inception Labs) for report generation.
- **SimHPC Client Library**: TypeScript client with auto-auth and typed methods.
- **API Proxy**: Next.js route handler with JWT session extraction.

### Fixed
- Resolved circular dependencies in Celery tasks.
- Fixed event loop issues in async backend services.
- Hardened JWT verification logic.

---

## [1.0.0] - 2026-03-04

### Added
- Initial production launch with Stripe integration and PDF export.
- Multi-stage Docker optimization.
- Structured logging and Prometheus metrics.
