# SimHPC Changelog

> All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-03-16

### Added
- **Mission Control Cockpit v1.6.0**: Complete modular redesign of the operational interface for aerospace/thermal engineers.
- **Component Modularization**: Split the dashboard into independent, high-performance components:
  - `TelemetryPanel.tsx`: 3-channel real-time sparklines (GPU/Convergence/Error).
  - `ActiveSimulations.tsx`: "Decision Panel" with live solver health status (optimal/stiff/diverging).
  - `SimulationLineage.tsx`: ITERATION-tree view for design ancestry and "Flux Delta" tracking.
  - `OperatorConsole.tsx`: High-stakes intervention tools ([INTERCEPT], [CLONE], [BOOST], [CERTIFY]).
  - `GuidanceEngine.tsx`: AI-navigator providing corrective strategy recommendations.
- **Unified Cockpit Aesthetic**: Dark-terminal theme with Mission Control Cyan accents and tabular-numeric UTC synchronization.
### Fixed
- **Unused Declarations**: Removed unused `ShieldAlert` icon import in `ActiveSimulations.tsx` and cleaned up unused `variant` prop in the inline `ThemeToggle` component within `ExperimentNotebook.tsx`.
- **Documentation Consolidation**: Consolidated frontend and root architecture documentation into a single source of truth at `ARCHITECTURE.md`.
- **Naming Consistency**: Standardized all references to `robustness-orchestrator` across the codebase and documentation to eliminate underscore/hyphen oscillation.
- **Project Structure & Hygiene**: Reorganized the monorepo for production readiness:
  - Moved low-level setup logs into `docs/internal/`.
  - Relocated root mockups to `docs/assets/mockups/`.
  - Purged redundant zip archives (`SimHPC_Alpha_*`) and legacy `zip_source.ps1`.
  - Deleted deprecated `archive/` directory to improve build focus.

## [1.5.1] - 2026-03-10

### Added
- **Trust Layer APIs (100% Complete)**: Finalized transparency services including Provenance API (hardware/solver metadata) and Uncertainty API (variance/confidence intervals).
- **Demo Flow APIs (100% Complete)**: Finalized guided onboarding with 5-step progress tracking, suggested next-run logic, and automated report/notebook generation.
- **Control Room UI APIs (100% Complete)**: Finalized operator panels with 50-run persistent memory, rule-based insight engine, alert aggregation (1h TTL), and single-request dashboard hydration.
- **Core System APIs (100% Complete)**: Finalized missing infrastructure including the Simulation Runtime Estimator (`runtime ≈ E * S * P`) and Timeline/Replay auditing system.

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
- **Mercury AI Migration**: Purged all Kimi AI references and fully transitioned to Mercury AI (Inception Labs) for engineering-grade report generation.
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

---

## Appendix: Mercury AI Usage in Alpha

### 1. Where Mercury Is Used in Alpha

In your current Alpha architecture, **Mercury should only be used in two places**:

#### 1️⃣ Simulation Setup Assistance

Mercury helps interpret user inputs into simulation parameters.

Example:

User input:
```
simulate high temperature stress
```

Mercury converts it into structured parameters:
```
temperature: 45
duration: 48h
wind: moderate
```

Then the simulation module runs.

So the flow is:
```
User Input
↓
Mercury interpretation
↓
Simulation parameters
↓
RunPod simulation
```

#### 2️⃣ Notebook Generation

Mercury writes the **explanatory text** inside the notebook.

Example:

Simulation output:
```
voltage_drop = 8%
temperature = 42C
```

Mercury generates:
```
The simulation indicates that elevated temperatures resulted in an 8% voltage drop,
suggesting increased thermal stress on the battery system.
```

So the flow is:
```
Simulation results
↓
Mercury explanation
↓
Notebook summary
```

### 2. Where Mercury Should NOT Be Used in Alpha

Avoid using Mercury for:

❌ actual physics simulations
❌ experiment selection
❌ simulation validation

### 3. Simple Mercury Health Test

The easiest test is to create a **test endpoint**.

Example:

Node.js example:
```javascript
export async function testMercury(req, res) {
  const response = await fetch("https://api.inceptionlabs.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.MERCURY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "mercury",
      messages: [
        { role: "user", content: "Return the word SIMHPC_OK" }
      ]
    })
  });

  const data = await response.json();
  res.json(data);
}
```

Expected response:
```
SIMHPC_OK
```

If you get that, Mercury is working.

### 4. Test From Terminal

You can test Mercury directly with curl:
```
curl https://api.inceptionlabs.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mercury",
    "messages": [
      {"role":"user","content":"reply SIMHPC_OK"}
    ]
  }'
```

Expected output:
```
SIMHPC_OK
```

### 5. What Alpha Mercury Usage Should Look Like

Ideal Alpha flow:
```
User runs simulation
↓
RunPod executes model
↓
Results returned
↓
Mercury writes explanation
↓
Notebook generated
```

So Mercury is **assistive**, not core.

### 6. Quick Mercury Test Inside Your System

The fastest test you can run right now:

Add this temporary call inside notebook generation:

Prompt:
```
Explain the following simulation result in one sentence.
```

If the notebook text appears → **Mercury is working**.
