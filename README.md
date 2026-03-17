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
