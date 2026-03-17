# Progress Log

## Current Status
- **v1.6.0-ALPHA**: Mission Control Cockpit (Modular Design Intelligence Platform).
- **v1.5.1-ALPHA**: Alpha Control Room (4-Panel UI).
- **v1.4.0-BETA**: Direct Vercel Deployment & RunPod Orchestration.
- **v1.3.1-BETA**: Supabase Integration & Protected Routes.

---

### March 16, 2026 (Mission Control Cockpit Redesign - v1.6.0)

- **Modular Component Architecture**: Decoupled the Alpha Control Room into production-grade components: `TelemetryPanel`, `ActiveSimulations`, `SimulationLineage`, `OperatorConsole`, and `GuidanceEngine`.
- **Decision Panel (Active Fleet)**: Implemented `ActiveSimulations.tsx` with live solver health indicators (optimal/stiff/diverging) and per-node progress tracking.
- **Operator Guidance Engine**: Enhanced `GuidanceEngine.tsx` with AI-driven strategy recommendations and physics-drift notifications.
- **Lineage Ancestry Graph**: Integrated `SimulationLineage.tsx` for visual debugging of design iterations and "Flux Delta" tracking.
- **Command Console Wiring**: Completed the `OperatorConsole.tsx` wiring to high-stakes backend actions: INTERCEPT, CLONE, BOOST, and CERTIFY.
- **Telemetry Sparkline Optimization**: Refined `TelemetryPanel.tsx` with multi-channel sparklines for GPU Load, Solver Convergence, and Residual Error.
- **System Health & Debugging**: Integrated `SystemStatus.tsx` sidebar component for real-time connection status to Mercury AI, RunPod GPUs, Supabase DB, and Simulation Worker endpoint. Added a 20-line Job Log Viewer to quickly debug RunPod errors and serverless timeouts.
- **Serverless Job Dispatcher**: Refined backend architecture with a Job Dispatcher Layer and Supabase queue to prevent GPU cold start overloads, timeouts, and job loss during high traffic.
- **Unified Cockpit Theme**: Standardized the aesthetic as "Mission Control Cyan" with high-contrast slate backgrounds and premium typography.
- **Code Cleanup & Optimization**: Eliminated unused imports (`ShieldAlert`) and removed redundant component props (`variant` in `ThemeToggle`) to improve bundle size and maintainability.
- **Documentation Consolidation**: Merged `apps/frontend/ARCHITECTURE.md` into the root `ARCHITECTURE.md` to establish a single source of truth for the platform's distributed systems.
- **Secrets Rotation Policy**: Defined a formal security procedure in `ARCHITECTURE.md` for rotating Supabase, RunPod, and Stripe credentials.
- **Naming Standardization**: Harmonized backend directory references (from `robustness_orchestrator` to `robustness-orchestrator`) across all shell scripts and markdown documentation.
- **Workspace Hygiene**: Relocated low-level setup logs (`info.md`) to `docs/internal/` and moved root-level mockups to `docs/assets/mockups/` to reduce root-level clutter.
- **Mercury AI Integration & Health Test**: 
  - Purged all Kimi AI (Moonshot) references and fully transitioned the `AIReportService` to **Mercury AI (Inception Labs)**.
  - Implemented `test_mercury.py` for automated API connectivity verification (`SIMHPC_OK` protocol).
  - Defined strict Alpha-usage roles: Simulation Setup Assistance and Notebook Generation; zero-involvement in core physics/validation.
  - Enhanced interpretive engine with **Numerical Anchoring** to ensure AI summaries match deterministic solver outputs.
- **Repository Maintenance**: Purged redundant zip archives (`SimHPC_Alpha_*`), removed the legacy `zip_source.ps1` utility, and deleted the deprecated `archive/` directory to reclaim storage and improve project focus.
- **Free Tier Enforcement Layer (v1.6.0-ALPHA)**:
  - **Usage Tracking**: Implemented rolling 7-day window with 5 simulation limit per free tier user
  - **Concurrency Control**: Prevents multiple simultaneous runs for free tier users
  - **Compute Guards**: Grid resolution cap (5,000 nodes), 30s runtime timeout, scenario gating
  - **Feature Gating**: Disabled SimulationLineage and SimulationMemory for free tier users
  - **Upgrade Triggers**: Added premium feature toasts and lock overlays with upgrade CTAs
  - **Dashboard Updates**: Added "Runs Remaining" counter in SystemStatus component
- **Metadata-Only Worker Ping (v1.6.0-ALPHA)**:
  - **Cost Control**: Implemented metadata-only ping to confirm worker status without GPU spin-up
  - **System Status Endpoint**: Parallel checks for Mercury AI, Supabase, and RunPod worker
  - **Health Check Guard**: RunPod worker handler checks `check_health_only` flag to bypass physics
  - **Frontend LEDs**: Real-time status indicators with 30-second polling interval
  - **O-D-I-A-V Integration**: Fulfills Observe and Detect stages with instant service feedback

- **System Hardening & Security Architecture (v1.6.0-ALPHA)**:
  - **JWT Security**: Eliminated placeholders, added clock skew tolerance (30s), configurable audience
  - **Endpoint Protection**: Strict `get_current_user` dependency for protected endpoints
  - **Token Revocation**: Redis-backed denylist for immediate token invalidation
  - **PDF Safety**: Dangerous pattern filtering in AI reports (definitive failure claims purged)
  - **Font Fallback**: Graceful fallback to built-in Helvetica if DejaVu fonts missing
  - **Robustness**: Removed SobolAnalyzer mock - system fails fast if module missing

### March 10, 2026 (Alpha Control Room Redesign)

- **Unified HPC Terminal Layout**: Rebuilt `/dashboard/alpha` as a premium 4-panel operations center.
- **Signal History Tracking**: Accumulates signal values over time for sparkline visualization, giving the dashboard a "feel alive" quality.
- **Framer Motion Animations**: Entry animations on simulation rows, insight items, and signal value changes.

### March 10, 2026 (NexusBayArea Migration & Final Alpha Polish)
- **Ownership Migration**: Successfully moved all project infrastructure, repositories, and deployment targets from `btwndlinez` to `NexusBayArea`.
- **Vercel Polish**: Cleaned up legacy deployment URLs and updated configuration to point to the new production environment.
- **Alpha RunPod Architecture**: Implemented a unified worker container architecture combining FastAPI, vLLM for ultra-fast inference, and a FAISS-based RAG service for engineering context retrieval.
- **vLLM Integration**: Configured vLLM for high-throughput generation (~90 tok/s on RTX 3090) supporting Mistral and Llama models.
- **RAG Service Implementation**: Developed a retrieval-augmented generation system using SentenceTransformers and FAISS, enabling the AI to answer questions based on SimHPC documentation.
- **Backend RunPod Proxy**: Added `AlphaChatRequest` and `/api/v1/alpha/chat` endpoint to the main orchestrator, proxying authorized chat requests to the Serverless LLM worker.

### March 10, 2026 (Magic Link Demo Token System)
- **Magic Link Demo Access:**
  - Implemented a complete alpha pilot onboarding system using secure, usage-limited magic link tokens.
  - **Backend (`demo_access.py`):**
    - `POST /api/v1/demo/magic-link` — Validates demo token and returns session info with remaining runs.
    - `GET /api/v1/demo/usage` — Returns current usage stats (remaining, limit, used, expired).
    - `POST /api/v1/demo/use-run` — Atomically decrements usage count per simulation run.
  - **Security:** Tokens stored as SHA-256 hashes — raw tokens never persisted. IP logging on all validation attempts.

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
