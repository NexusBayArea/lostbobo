# SimHPC Roadmap

> Last Updated: April 01, 2026

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
- [x] **RunPod Pod Migration** - Migrated from Legacy Serverless to dedicated GPU pod with infinite loop workers (March 2026)
- [x] **Mission Control Cockpit v1.6.0** - Modular "Decision Intelligence" platform with Telemetry, Active Fleet, Ancestry, and Command Console (March 2026)
- [x] **RAG Engineering Assistant** - Retrieval-augmented chat for SimHPC documentation (March 2026)
- [x] **Core System APIs** - Runtime estimator (`runtime ≈ E * S * P`) and timeline replay system (100% Complete)
- [x] **Control Room UI APIs** - Persistent memory, rule-based insights, and alert aggregation (100% Complete)
- [x] **Demo Flow APIs** - Guided 5-step onboarding and rule-based suggested run logic (100% Complete)
- [x] **Trust Layer APIs** - Full physics provenance and uncertainty metrics APIs (100% Complete)
- [x] **RunPod API Client (v2.2.1)** - Production-grade pod lifecycle management via GraphQL API (March 2026)
- [x] **Cost-Aware Autoscaler (v2.2.1)** - Daily budget caps, cost tracking, fleet monitoring, event audit trail (March 2026)
- [x] **Admin Fleet API (v2.3.0)** - Warm-up capability, readiness polling, and rich fleet status (March 2026)
- [x] **Option C Infrastructure (v2.3.0)** - Stop/Resume strategy with Network Volume persistence (March 2026)
- [x] **Docker Hub Registry (v2.2.1)** - Published images: simhpcworker/simhpc-api, simhpc-worker, simhpc-autoscaler (March 2026)
- [x] **Cockpit Backend Sync (v2.4.1)** - Unified O-D-I-A-V loop state aggregator and explicit command APIs (April 2026)
- [x] **Supabase Initialization Fix (v2.5.3)** - Fixed Vercel environment variable injection via `envPrefix` (April 2026)
- [x] **Logo Styling Update (v2.5.3)** - Removed glows/shadows and updated to theme-aware colors (April 2026)

### Phase 2: Enterprise Features (Completed ✅)

- [x] **Interactive Onboarding (v2.4.0)**: Guided product walkthrough with 8-step "Value Journey" and conversion intelligence.
- [x] **Persistence & Resume (v2.4.1)**: Versioned autosave and cross-device resume logic for onboarding.
- [x] **Schema Normalization (v2.5.0)**: `simulation_history` → `simulations`, certificates table, RAG tables, event log, RLS, TypeScript type contracts.
- [x] **API Routes Split (v2.5.0)**: `api.py` split into `routes/simulations.py`, `routes/certificates.py`, `routes/control.py`, `routes/admin.py`.
- [x] **Worker Status Flow (v2.5.0)**: Full `running → auditing → completed` with `audit_result`, `certificate_id`, `pdf_url`, `updated_at`.
- [x] **Missing Endpoints (v2.5.0)**: `POST /simulations`, `GET /simulations/{id}`, `POST /simulations/{id}/export-pdf`, `GET /certificates/{id}/verify`.
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

- [x] RunPod API integration for automated pod lifecycle (v2.2.1)
- [x] Cost-aware autoscaling with daily budget caps (v2.2.1)
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
| :--- | :--- | :--- |
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
| :--- | :--- | :--- |
| 2.5.0 | April 01, 2026 | Schema Normalization, API Routes Split, Worker Status Flow, Certificate Pipeline, Missing Endpoints |
| 2.4.1 | April 01, 2026 | Cockpit Backend Synchronization & Persistent Onboarding |
| 2.4.0 | March 30, 2026 | Interactive Onboarding walkthrough & Conversion Intelligence |
| 2.3.0 | March 28, 2026 | Option C Autoscaler, "Wake GPU" admin panel, Stop/Resume strategy |
| 2.2.1 | March 26, 2026 | Docker Hub registry, consolidated docs, monorepo restructure |
| 2.2.0 | March 25, 2026 | RunPod API client, cost-aware autoscaler v2.2.0, admin fleet endpoints |
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

To propose features or report bugs, contact: <support@simhpc.com>

---

> **Mercury AI**: See [ARCHITECTURE.md](./ARCHITECTURE.md#appendix-mercury-ai-usage-in-alpha) for usage guidelines and health tests.
