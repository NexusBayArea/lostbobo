# SimHPC Unified Architecture v2.6.7

## Building the System

### Folder Structure
```
/workspace
├── app/                  # Core Backend Package
│   ├── __init__.py
│   ├── main.py           # uvicorn entry point
│   ├── api.py            # FastAPI orchestrator
│   ├── worker.py         # Physics worker (supervises jobs)
│   ├── autoscaler.py     # GPU fleet autoscaling
│   ├── services/         # Onboarding, Robustness, Worker
│   ├── models/           # Pydantic schemas
│   └── core/             # Auth, Job Queue, Supabase
├── Dockerfile.unified    # Multi-stage Docker build
├── requirements.txt      # Python dependencies
└── start.sh             # Startup script
```

### Execution
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Port Configuration
- **Primary API:** 8080 (main traffic, batch flush to Supabase)
- **Backup API:** 8000 (redundancy)
- **Jupyter:** 8888 (development only)

---

## Building Rules

### Zero-Leak Packaging
- **EXCLUDE:** `.env`, `.git/`, `__pycache__/`, `*.md`, `*.png`, `*.jpg`, `*.zip`, `node_modules/`, `venv/`
- **INCLUDE:** `app/`, `requirements.txt`, `Dockerfile.unified`, `start.sh`

### Health Check
```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/health
```

### Pod ID (Dynamic)
Get latest from Infisical:
```bash
infisical secrets get RUNPOD_ID --plain
```
