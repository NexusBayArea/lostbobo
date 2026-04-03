# SimHPC v2.5 "Single Source of Truth" Consolidation Script
# Date: April 1, 2026
# Target: Windows (PowerShell)

$ErrorActionPreference = "Stop"
$LegacyDir = "legacy_archive"
$LogFile = "v2.5_consolidation.log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Tee-Object -FilePath $LogFile -Append
}

Write-Log "--- Starting SimHPC v2.5 Structural Consolidation ---"

# 1. PREPARE ARCHIVE
if (-not (Test-Path $LegacyDir)) { New-Item -ItemType Directory -Path $LegacyDir }
$WorkerLegacy = Join-Path $LegacyDir "worker_versions"
if (-not (Test-Path $WorkerLegacy)) { New-Item -ItemType Directory -Path $WorkerLegacy }

# 2. UNIFY WORKER STRUCTURE
Write-Log "[1/4] Unifying Worker & Autoscaler..."

# Create the final unified worker directory if it doesn't exist
if (-not (Test-Path "services/worker")) { New-Item -ItemType Directory -Path "services/worker" }

# Move the TRUTH worker (v2.5.0)
if (Test-Path "services/runpod-worker/worker.py") {
    Write-Log "  -> Promoting services/runpod-worker/worker.py (v2.5.0) to services/worker/"
    Move-Item -Path "services/runpod-worker/worker.py" -Destination "services/worker/worker.py" -Force
}

# Move the TRUTH autoscaler (Option C) and rename to autoscaler.py
if (Test-Path "services/runpod-worker/app/idle_timeout.py") {
    Write-Log "  -> Promoting services/runpod-worker/app/idle_timeout.py (v2.3.0) to services/worker/autoscaler.py"
    Move-Item -Path "services/runpod-worker/app/idle_timeout.py" -Destination "services/worker/autoscaler.py" -Force
}

# Move dependencies
if (Test-Path "services/runpod-worker/runpod_api.py") {
    Move-Item -Path "services/runpod-worker/runpod_api.py" -Destination "services/worker/runpod_api.py" -Force
}
if (Test-Path "services/runpod-worker/requirements.txt") {
    Move-Item -Path "services/runpod-worker/requirements.txt" -Destination "services/worker/requirements.txt" -Force
}

# 3. ARCHIVE LEGACY
Write-Log "[2/4] Archiving Legacy Duplicates..."

# Archive old services/worker/ content (v1.6.0-ALPHA logic)
if (Test-Path "services/worker/services") {
    Write-Log "  -> Archiving legacy services/worker/ artifacts"
    Move-Item -Path "services/worker/ai_report_service.py" -Destination "$WorkerLegacy/legacy_ai_report_service.py" -ErrorAction SilentlyContinue
    Move-Item -Path "services/worker/pdf_service.py" -Destination "$WorkerLegacy/legacy_pdf_service.py" -ErrorAction SilentlyContinue
    Move-Item -Path "services/worker/robustness_service.py" -Destination "$WorkerLegacy/legacy_robustness_service.py" -ErrorAction SilentlyContinue
    Move-Item -Path "services/worker/services" -Destination "$WorkerLegacy/legacy_services_subdir/" -ErrorAction SilentlyContinue
}

# Archive the redundant runpod-worker folder
if (Test-Path "services/runpod-worker") {
    Write-Log "  -> Archiving redundant services/runpod-worker/ folder"
    Move-Item -Path "services/runpod-worker" -Destination (Join-Path $LegacyDir "runpod-worker_deprecated") -Force
}

# 4. UPDATE API PATHS
Write-Log "[3/4] Updating API Import Paths..."
$ApiPath = "services/api/api.py"
if (Test-Path $ApiPath) {
    $Content = Get-Content $ApiPath
    $Content = $Content -replace '\.\.[\/]"runpod-worker"[\/]"app"', '.."worker"'
    $Content = $Content -replace 'from idle_timeout import warm_pod', 'from autoscaler import warm_pod'
    Set-Content -Path $ApiPath -Value $Content
}

# 5. SECURITY & VALIDATION
Write-Log "[4/4] Final Security Check..."

# Enforce .env protection
$GitFiles = git ls-files .env 2>$null
if ($GitFiles) {
    Write-Log "  !! ALERT: .env is tracked! Untracking now."
    git rm --cached .env
}

Write-Log "--- CONSOLIDATION COMPLETE ---"
Write-Log "Current 'Single Source of Truth' Structure:"
Get-ChildItem -Path "services" -Recurse | Select-Object FullName | Write-Log
