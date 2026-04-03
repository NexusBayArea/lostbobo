#!/bin/bash
# SimHPC v2.5 "Single Source of Truth" Consolidation Script
# Date: April 1, 2026

set -e

LEGACY_DIR="legacy_archive"
STDOUT_LOG="v2.5_consolidation.log"

# Detect OS for sed compatibility
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE=("sed" "-i" "")
else
    SED_INPLACE=("sed" "-i")
fi

echo "--- Starting SimHPC v2.5 Structural Consolidation ---" | tee $STDOUT_LOG

# 1. PREPARE ARCHIVE
mkdir -p "$LEGACY_DIR"
mkdir -p "$LEGACY_DIR/worker_versions"

# 2. UNIFY WORKER STRUCTURE
echo "[1/4] Unifying Worker & Autoscaler..." | tee -a $STDOUT_LOG

# Create the final unified worker directory if it doesn't exist
mkdir -p services/worker

# Move the TRUTH worker (v2.5.0) to the final location
if [ -f "services/runpod-worker/worker.py" ]; then
    echo "  -> Promoting services/runpod-worker/worker.py (v2.5.0) to services/worker/" | tee -a $STDOUT_LOG
    mv "services/runpod-worker/worker.py" "services/worker/worker.py"
fi

# Move the TRUTH autoscaler (Option C) and rename to autoscaler.py
if [ -f "services/runpod-worker/app/idle_timeout.py" ]; then
    echo "  -> Promoting services/runpod-worker/app/idle_timeout.py (v2.3.0) to services/worker/autoscaler.py" | tee -a $STDOUT_LOG
    mv "services/runpod-worker/app/idle_timeout.py" "services/worker/autoscaler.py"
fi

# Move dependencies
[ -f "services/runpod-worker/runpod_api.py" ] && mv "services/runpod-worker/runpod_api.py" "services/worker/runpod_api.py"
[ -f "services/runpod-worker/requirements.txt" ] && mv "services/runpod-worker/requirements.txt" "services/worker/requirements.txt"

# 3. ARCHIVE LEGACY
echo "[2/4] Archiving Legacy Duplicates..." | tee -a $STDOUT_LOG

# Archive old services/worker/ content (v1.6.0-ALPHA logic)
if [ -d "services/worker/services" ]; then
    echo "  -> Archiving legacy services/worker/ artifacts" | tee -a $STDOUT_LOG
    mv "services/worker/ai_report_service.py" "$LEGACY_DIR/worker_versions/legacy_ai_report_service.py" 2>/dev/null || true
    mv "services/worker/pdf_service.py" "$LEGACY_DIR/worker_versions/legacy_pdf_service.py" 2>/dev/null || true
    mv "services/worker/robustness_service.py" "$LEGACY_DIR/worker_versions/legacy_robustness_service.py" 2>/dev/null || true
    mv "services/worker/services" "$LEGACY_DIR/worker_versions/legacy_services_subdir/" 2>/dev/null || true
fi

# Archive the redundant runpod-worker folder
if [ -d "services/runpod-worker" ]; then
    echo "  -> Archiving redundant services/runpod-worker/ folder" | tee -a $STDOUT_LOG
    mv "services/runpod-worker" "$LEGACY_DIR/runpod-worker_deprecated/"
fi

# 4. UPDATE API PATHS
echo "[3/4] Updating API Import Paths..." | tee -a $STDOUT_LOG
# Update api.py to look for the autoscaler in services/worker/ instead of the old /app/ path
"${SED_INPLACE[@]}" 's/\.\.[\/]"runpod-worker"[\/]"app"/\.\.[\/]"worker"/g' services/api/api.py
"${SED_INPLACE[@]}" 's/from idle_timeout import warm_pod/from autoscaler import warm_pod/g' services/api/api.py

# 5. SECURITY & VALIDATION
echo "[4/4] Final Security Check..." | tee -a $STDOUT_LOG

# Enforce .env protection
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "  !! ALERT: .env is tracked! Untracking now." | tee -a $STDOUT_LOG
    git rm --cached .env
fi

echo -e "\n--- CONSOLIDATION COMPLETE ---" | tee -a $STDOUT_LOG
echo "Current 'Single Source of Truth' Structure:" | tee -a $STDOUT_LOG
ls -R services/ | tee -a $STDOUT_LOG
