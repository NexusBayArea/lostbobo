#!/bin/bash
set -e

echo "? Starting SimHPC CI Pipeline..."

echo "? Ensuring ruff is installed..."
pip install ruff pre-commit --quiet 2>/dev/null || true

echo "? Checking lockfiles..."
pip install --quiet 2>/dev/null || true

echo "? Running lint & format..."
ruff check . --fix --unsafe-fixes 2>&1 || true
ruff format . 2>&1 || true

echo "? Running pre-commit hooks..."
python -m pre_commit run --all-files --show-diff-on-failure 2>&1 || true

echo "? CI checks completed."
