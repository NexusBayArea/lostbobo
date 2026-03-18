# SimHPC Monorepo - Mission Control Cockpit

This is the private monorepo for SimHPC, containing all frontend, backend, AI, and orchestration logic.
**Designed as an Operational Interface for aerospace and thermal engineers implementing the O-D-I-A-V decision loop.**

## Directory Structure

- **`apps/`**
  - **`frontend/`**: Mission Control Cockpit interface (Vite + React + TypeScript) - **Operator's primary interface**
- **`services/`**
  - **`robustness-orchestrator/`**: Backend service for robustness analysis and PDF report generation - **Executes O-D-I-A-V loop commands**
  - **`runpod-worker/`**: GPU-enabled worker service for RunPod (vLLM, RAG) - **Physics solver engine**
- **`packages/`**
  - **`sdk/`**: SimHPC Python SDK - **Integration layer for cockpit commands**
- **`docs/`**
  - **`assets/`**: Images, mockups, and visual assets.
  - **`internal/`**: Technical logs and setup information.

## Global Documentation - Focused on Operator Cognition

- **`ARCHITECTURE.md`**: Detailed system architecture emphasizing the O-D-I-A-V loop implementation
- **`progress.md`**: Project-wide development history with focus on cockpit evolution
- **`ALPHA_PILOT_GUIDE.md`**: Instructions for operators using the Mission Control interface
- **`MISSION_CONTROL_STRATEGY.md`**: Strategic evolution of the Operational Cockpit

## Core Architecture - The O-D-I-A-V Loop

SimHPC's v1.6.0-ALPHA is built around the **Operational Cockpit** concept, implementing a tight O-D-I-A-V (Observe-Detect-Investigate-Act-Verify) decision loop for high-stakes engineering scenarios:

1. **OBSERVE** → `TelemetryPanel` (240Hz solver streams from RunPod workers)
2. **DETECT** → `AuditFeed` (Rnj-1 AI Auditor anomaly detection) 
3. **INVESTIGATE** → `SimulationMemory` (Iteration Lineage & Delta Tracking)
4. **ACT** → `OperatorConsole` (Intercept, Clone, Boost, Certify)
5. **VERIFY** → `GuidanceEngine` (Mercury AI Numerical Anchoring against solver outputs)

*Note: Deep Engineering RAG vault implementation deferred to BETA per requirements.*

## Development

### Prerequisites
- Docker & Docker Compose
- Node.js (for frontend)
- Python 3.10+ (for backend services)

### Quick Start
```bash
docker-compose up --build
```
<<<<<<< HEAD
=======

### Run Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

## Deployment
The frontend is automatically deployed to Vercel upon merging into the main branch of the `lostbobo` repository.
- **Primary**: https://simhpc.com
- **Backup**: https://NexusBayArea.github.io/lostbobo

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
>>>>>>> ba695bc (Update frontend components and API connectivity for v1.6.0-ALPHA)
