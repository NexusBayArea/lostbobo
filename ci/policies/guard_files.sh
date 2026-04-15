#!/usr/bin/env bash

CRITICAL_FILES=(
  "app/main.py"
  "app/api/api.py"
  "app/services/worker/worker.py"
)

for file in "${CRITICAL_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "[FATAL] Missing critical file: $file"
    exit 1
  fi
 done
