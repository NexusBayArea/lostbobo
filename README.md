# SimHPC Monorepo

This is the private monorepo for SimHPC, containing all frontend, backend, AI, and orchestration logic.

## Directory Structure

- **`apps/`**
  - **`frontend/`**: The canonical frontend application (Vite + React + TypeScript).
  - **`saas-starter/`**: Next.js SaaS starter template.
- **`services/`**
  - **`robustness-orchestrator/`**: Backend service for robustness analysis and PDF report generation.
  - **`runpod-worker/`**: GPU-enabled worker service for RunPod (vLLM, RAG).
- **`packages/`**
  - **`sdk/`**: SimHPC Python SDK.
- **`docs/`**: Project documentation and legal assets.

## Global Documentation

- **`ARCHITECTURE.md`**: Detailed system architecture and security model.
- **`progress.md`**: Project-wide development history and roadmap.
- **`ALPHA_PILOT_GUIDE.md`**: Instructions for early testers and alpha users.
- **`info.md`**: High-level platform information.

## Development

### Prerequisites
- Docker & Docker Compose
- Node.js (for frontend)
- Python 3.10+ (for backend services)

### Quick Start
```bash
docker-compose up --build
```
