# SimHPC Roadmap

> Last Updated: March 16, 2026

## Vision
SimHPC is a cloud-based GPU-accelerated finite element simulation platform with integrated robustness analysis and AI-generated engineering reports. Built for engineering teams that require stable, defensible results.

---

## Feature Roadmap

### Phase 1: Core Platform (Completed ✅)

- [x] React frontend with theme system
- [x] FastAPI orchestration layer
- [x] Robustness analysis engine
- [x] AI report generation (Mercury AI)
- [x] PDF export with visualization
- [x] Supabase authentication
- [x] Stripe billing integration
- [x] **Experiment Notebook** (March 2026)
- [x] **Abuse Prevention System** (March 2026)
- [x] **Secure Multi-Repo Deployment Strategy** (March 2026)
- [x] **Google One Tap Integration** (March 2026)
- [x] **Footer Logo Color Fix** - Changed SimHPC logo "Sim" text to inherit parent color (March 2026)
- [x] **Global Background Update** - Updated all page backgrounds to match homepage color #f1ede0 (March 2026)
- [x] **ExperimentNotebook Theme Toggle** - Added bright/dark mode toggle matching rest of website (March 2026)
- [x] **Magic Link Demo Tokens** - Secure alpha pilot onboarding with usage-limited demo links (March 2026)
- [x] **Alpha RunPod Container Architecture** - Unified vLLM + RAG worker for high-performance LLM services (March 2026)
- [x] **Mission Control Cockpit v1.6.0** - Modular "Decision Intelligence" platform with Telemetry, Active Fleet, Ancestry, and Command Console (March 2026)
- [x] **RAG Engineering Assistant** - Retrieval-augmented chat for SimHPC documentation (March 2026)
- [x] **Core System APIs** - Runtime estimator (`runtime ≈ E * S * P`) and timeline replay system (100% Complete)
- [x] **Control Room UI APIs** - Persistent memory, rule-based insights, and alert aggregation (100% Complete)
- [x] **Demo Flow APIs** - Guided 5-step onboarding and rule-based suggested run logic (100% Complete)
- [x] **Trust Layer APIs** - Full physics provenance and uncertainty metrics APIs (100% Complete)

### Phase 2: Enterprise Features (In Progress)
- [ ] **Advanced Mesh Handling**: Support for large-scale geometries (10M+ elements)
- [ ] **Custom Boundary Conditions UI**: Graphical node/face selection
- [ ] **Transient Thermal Analysis**: Full time-dependent heat transfer
- [ ] **Modal Frequency Analysis**: Structural resonance detection
- [ ] **Material Library**: Pre-configured battery/semiconductor properties

### Phase 3: AI & Automation (Planned)
- [ ] **Auto-Refine**: Automated mesh refinement suggestions based on gradient error estimates
- [ ] **Physics-Based Constraints**: AI validation of input parameter physical consistency
- [ ] **Optimization Loops**: Automated multi-variable optimization to reach target metrics
- [ ] **Pareto Frontier**: Multi-objective trade-off visualization

### Phase 4: Platform Expansion (Backlog)
- [ ] **Mobile Companion**: Real-time simulation alerts and status tracking
- [ ] **Team Workspace**: Shared project folders and collaborative report editing
- [ ] **White-Label API**: Headless simulation engine for enterprise integration
- [ ] **On-Premise Control**: Secure bridge for local cluster orchestration

---

## Technical Roadmap

### Infrastructure
- [ ] Kubernetes migration for worker auto-scaling
- [ ] Multi-region GPU worker pool (RunPod + Lambda)
- [ ] Global CDN for static simulation assets
- [ ] Automated daily database backups (off-site)

### Security & Compliance
- [ ] SOC 2 Type II readiness assessment
- [ ] ISO 27001 compliance audit
- [ ] GDPR/CCPA automated data deletion workflows
- [ ] Full system audit logging with signed hashes

### Developer Experience
- [ ] Python SDK v2.0 (Typed, async-first)
- [ ] REST API OpenAPI 3.1 documentation
- [ ] WebSocket streaming for real-time mesh visualization
- [ ] JupyterLab integration for deep data analysis

---

## Known Limitations

### Current Constraints
| Limitation | Description | Target Fix |
|------------|-------------|------------|
| Mesh Size | Free tier limited to small meshes | Q2 2026 |
| Runtime | 60s timeout on free tier | Q2 2026 |
| Concurrent Runs | 1 max for free users | Q2 2026 |
| File Formats | STEP, IGES, STL, Parasolid only | Q3 2026 |

### Deprecations
- **Kimi AI**: Replaced by Mercury AI (Inception Labs) - March 2026
- **Next.js SaaS Starter**: Abandoned in favor of Vite/React - March 2026
- **Monolithic Repo**: Split into `simhpc-frontend` and private monorepo - March 2026

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.5.1 | March 10, 2026 | Alpha Control Room redesign with 4-panel HPC terminal layout |
| 1.5.0 | March 10, 2026 | Alpha RunPod architecture, vLLM inference engine, RAG engineering assistant |
| 1.4.0 | March 10, 2026 | Magic link demo tokens, usage-limited alpha pilot onboarding |
| 1.3.1 | March 10, 2026 | Tier-aware API, Supabase simulation persistence, Payment Success UX |
| 1.3.0 | March 9, 2026 | Google One Tap integration, GitHub Pages deployment |
| 1.2.0 | March 8, 2026 | Experiment notebook, abuse prevention, secure repo split |
| 1.1.0 | March 6, 2026 | Mercury AI migration, Celery worker hardening |
| 1.0.0 | March 4, 2026 | Initial production launch with Stripe and PDF export |

---

## Contribution

To propose features or report bugs, contact: support@simhpc.com

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
