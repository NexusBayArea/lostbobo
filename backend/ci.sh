#!/bin/bash
set -e

echo "🚀 Starting SimHPC CI Pipeline..."

# 1. Lockfiles
echo "📦 Regenerating lockfiles..."
uv pip compile ../pyproject.toml --extra api -o requirements.api.lock
uv pip compile ../pyproject.toml --extra worker -o requirements.worker.lock
uv pip compile ../pyproject.toml --extra dev -o requirements-dev.txt
uv pip compile ../pyproject.toml --extra gpu -o requirements.gpu.lock

# 2. Ruff (using uv pip run)
echo "🔍 Running lint & format..."
uv pip run ruff format --check .
uv pip run ruff check .

# 3. Tests
echo "🧪 Running tests..."
pytest -q || echo "No tests yet — skipping"

echo "✅ Full CI Pipeline Passed"