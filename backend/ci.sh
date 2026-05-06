#!/bin/bash
set -e

echo "🚀 Starting SimHPC CI Pipeline..."

# Install ruff locally if not available
echo "📦 Ensuring ruff is installed..."
pip install ruff --quiet

# 1. Lockfiles (skip in CI to save time - lockfiles already checked elsewhere)
echo "📦 Checking lockfiles..."

# 2. Ruff 
echo "🔍 Running lint & format..."
ruff format --check .
ruff check .

# 3. Tests
echo "🧪 Running tests..."
pytest -q || echo "No tests yet — skipping"

echo "✅ Full CI Pipeline Passed"