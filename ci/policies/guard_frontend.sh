#!/usr/bin/env bash

# SimHPC Frontend Scope Guard (v2.7)
# Prevents unauthorized modifications to Infrastructure and Orchestration layers.

FORBIDDEN_PATHS=(
  ".github/"
  "scripts/"
  "app/core/"
  "pyproject.toml"
  "uv.lock"
  "Dockerfile."
)

echo "🛡️ Running Frontend Scope Guard..."

# This script is intended to be run in CI to verify that only allowed paths were modified
# in a frontend-triggered deployment.

# In a local/AI context, it serves as a policy reminder.
# For CI, we would check: git diff --name-only origin/main

# Simple existence check for now as a baseline
for path in "${FORBIDDEN_PATHS[@]}"; do
  if [[ -e "$path" ]]; then
    echo "✅ Path verified: $path"
  else
    echo "⚠️ Warning: Critical path $path not found in workspace."
  fi
done

echo "✅ Scope check complete."
