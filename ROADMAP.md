# SimHPC Roadmap

> Last Updated: March 8, 2026

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
| 1.3.1 | March 9, 2026 | Tier-aware API, Supabase simulation persistence, Payment Success UX |
| 1.3.0 | March 9, 2026 | Google One Tap integration, GitHub Pages deployment |
| 1.2.0 | March 8, 2026 | Experiment notebook, abuse prevention, secure repo split |
| 1.1.0 | March 6, 2026 | Mercury AI migration, Celery worker hardening |
| 1.0.0 | March 4, 2026 | Initial production launch with Stripe and PDF export |

---

## Contribution

To propose features or report bugs, contact: support@simhpc.com
