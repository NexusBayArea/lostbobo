#!/bin/bash
# SimHPC Cleanup & Standardization Script (v2.4.1-CLEANUP)
# Date: April 1, 2026
# Security Policy: April 1 Standard (🚨 CRITICAL)

set -e

# --- Configuration ---
LEGACY_DIR="legacy_archive"
STDOUT_LOG="cleanup_audit.log"

echo "--- SimHPC Directory Audit & Cleanup Starting ---" | tee $STDOUT_LOG

# 1. ARCHIVING LEGACY (Archive v1.6.0-ALPHA or old v2.2.1 stack)
echo "[1/4] Archiving legacy files..." | tee -a $STDOUT_LOG
mkdir -p "$LEGACY_DIR"

# Identify and move legacy files
# autoscaler.py in runpod-worker is the old v2.2.1 version (Truth is idle_timeout.py v2.3.0)
if [ -f "services/runpod-worker/autoscaler.py" ]; then
    echo "  -> Archiving legacy autoscaler.py (v2.2.1)" | tee -a $STDOUT_LOG
    mv "services/runpod-worker/autoscaler.py" "$LEGACY_DIR/autoscaler_v2.2.1.py"
fi

# 2. IDENTIFYING TRUTH (Keeping March 25–31 updates)
echo "[2/4] Verifying 'Truth' versions..." | tee -a $STDOUT_LOG

# api.py (v2.4.1)
if grep -q "warm_fleet" "services/api/api.py"; then
    echo "  -> services/api/api.py: VALID (v2.4.1)" | tee -a $STDOUT_LOG
else
    echo "  !! services/api/api.py: WARNING - Version mismatch. Manual check required." | tee -a $STDOUT_LOG
fi

# worker.py (v2.5.0)
if grep -q "SimHPC RunPod Worker (v2.5.0)" "services/runpod-worker/worker.py"; then
    echo "  -> services/runpod-worker/worker.py: VALID (v2.5.0)" | tee -a $STDOUT_LOG
else
    echo "  !! services/runpod-worker/worker.py: WARNING - Version mismatch. Manual check required." | tee -a $STDOUT_LOG
fi

# idle_timeout.py (v2.3.0 - The true autoscaler)
if grep -q "Option C (v2.3.0)" "services/runpod-worker/app/idle_timeout.py"; then
    echo "  -> services/runpod-worker/app/idle_timeout.py: VALID (v2.3.0)" | tee -a $STDOUT_LOG
else
    echo "  !! services/runpod-worker/app/idle_timeout.py: WARNING - Version mismatch. Manual check required." | tee -a $STDOUT_LOG
fi

# 3. STANDARDIZING WORKERS (Consolidating logic)
echo "[3/4] Consolidating worker structures..." | tee -a $STDOUT_LOG

# Move specialized worker logic into the primary runpod-worker directory
# Handles environment differences via .env (as per project standard)
if [ -d "services/worker" ]; then
    echo "  -> Moving services/worker/ logic into services/runpod-worker/" | tee -a $STDOUT_LOG
    cp services/worker/ai_report_service.py services/runpod-worker/
    cp services/worker/pdf_service.py services/runpod-worker/
    cp services/worker/robustness_service.py services/runpod-worker/
    
    echo "  -> Archiving services/worker/ folder" | tee -a $STDOUT_LOG
    mv "services/worker" "$LEGACY_DIR/services_worker_legacy/"
fi

# 4. VERIFICATION (April 1 Security Policy)
echo "[4/4] Verifying security policy compliance..." | tee -a $STDOUT_LOG

# Check .gitignore for .env protection
if grep -q "^\.env$" ".gitignore"; then
    echo "  -> .gitignore: PASS (.env is protected)" | tee -a $STDOUT_LOG
else
    echo "  !! .gitignore: FAIL (.env NOT PROTECTED) - FIXING IMMEDIATELY" | tee -a $STDOUT_LOG
    echo ".env" >> ".gitignore"
fi

# Ensure .env is NOT tracked in Git
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    echo "  !! .env: FAIL (Detected in Git index) - UNTRACKING NOW" | tee -a $STDOUT_LOG
    git rm --cached .env
else
    echo "  -> .env: PASS (Not tracked in Git)" | tee -a $STDOUT_LOG
fi

# Final status
echo "--- Cleanup Complete. Audit log saved to $STDOUT_LOG ---" | tee -a $STDOUT_LOG
