# Session Log

## 2026-05-10 19:31:22 PST

### Actions Taken

1. **Reviewed Provenance Storage Implementation**
   - Verified existing `backend/core/kernel/lineage/storage.py` with ProvenanceStorage class
   - Confirmed import path uses `backend.app.core.supabase` (not `backend.core.services.supabase_client`)

2. **Added Missing `create_snapshot` Method**
   - File: `backend/core/kernel/lineage/storage.py`
   - Added `hashlib` and `json` imports
   - Implemented `create_snapshot()` method for audit/replay functionality

3. **Created Database Migration**
   - File: `deploy/supabase/migrations/20260510_provenance_storage.sql`
   - Added columns to execution_lineage: trace_id, correlation_id, causation_id
   - Created `provenance_nodes` table with unique constraint on (execution_id, node_type, node_name)
   - Created `provenance_edges` table
   - Created `provenance_snapshots` table with integrity_hash
   - Added indexes for graph traversal performance
   - Configured RLS policies for service_role

### Notes

- Log.md already present in .gitignore (line 29)
- ProvenanceStorage uses singleton pattern via `_instance` class variable
- Graph updates happen in real-time during event storage
- Snapshots use SHA256 hash of canonical JSON for integrity verification

## 2026-05-10 19:40:27 PST

### Actions Taken

1. **Updated LineageCollector to Use ProvenanceStorage**
   - File: `backend/core/kernel/lineage/collector.py`
   - Replaced direct Supabase insert with ProvenanceStorage.store_event()
   - Added singleton storage instance in `__new__`
   - Fixed ruff linting issues (2 errors)

2. **Created LineageDashboard Component**
   - File: `frontend/src/components/LineageDashboard.tsx`
   - Lists recent executions with event counts and source types
   - Click execution to view full lineage graph via LineageVisualizer
   - Uses `/api/lineage/executions` endpoint

### Notes

- LineageVisualizer already exists at `frontend/src/components/LineageVisualizer.tsx`
- Backend API `/lineage/executions` already implemented in `backend/app/api/lineage.py`
- Pre-commit hooks ran successfully after ruff fixes

## 2026-05-10 20:01:00 PST

### Actions Taken

1. **Created Helm Chart for SimHPC Core**
   - Created `simhpc-core/` directory with Chart.yaml (v0.9.1)
   - Created values.yaml with GPU configuration (fractional, MPS, nodeSelector, tolerations)
   - Created templates: deployment.yaml, service.yaml, configmap.yaml, secret.yaml, job-migration.yaml, ingress.yaml
   - Created .helmignore

2. **Fixed Pre-commit Issues**
   - Added .tsx and .ts to .gitattributes for LF line endings
   - Fixed YAML template parsing by simplifying deployment.yaml
   - Added trailing newlines to all helm files

### Notes

- Helm chart supports GPU scheduling: fractional GPU, MPS, node selector, tolerations
- Chart version: 0.9.1, app version: 2026.05
- Log.md remains in .gitignore - not pushed

## 2026-05-10 20:05:23 PST

### Actions Taken

1. **Added Production Values File**
   - File: `simhpc-core/values.prod.yaml`
   - Production settings: replicaCount: 3, HPA, PDB, securityContext
   - TLS configuration for ingress
   - Higher resource limits and queue depth
   - Infisical integration for secrets management

### Notes

- HPA configured: min 3, max 12 replicas, 70% CPU target
- PDB: minAvailable 2 for zero-downtime updates
- Security: runAsNonRoot, runAsUser 1000, fsGroup 1000
- All pre-commit hooks pass (green)

## 2026-05-10 20:25:23 PST

### Actions Taken

1. **Added HPA Template**
   - File: `simhpc-core/templates/hpa.yaml`
   - HorizontalPodAutoscaler with CPU/memory metrics
   - Scale up: 100% in 15s, Scale down: 10% in 60s
   - Configurable via values.yaml hpa section

2. **Added VPA Template**
   - File: `simhpc-core/templates/vpa.yaml`
   - VerticalPodAutoscaler for CPU/memory recommendations
   - Supports recommendation-only mode or auto-updates
   - Configurable min/max allowed resources

### Notes

- VPA requires CRDs: kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/vertical-pod-autoscaler-1.0.0/crd.yaml
- HPA and VPA work together: HPA handles replica count, VPA handles resource requests
- GPU resources (nvidia.com/gpu) are not managed by VPA
- All pre-commit hooks pass (green)
