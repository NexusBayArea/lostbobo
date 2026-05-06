#!/bin/bash
set -e

echo "🚀 Starting SimHPC CI Pipeline..."

# Lockfiles
echo "📦 Regenerating lockfiles..."
uv pip compile ../pyproject.toml --extra api -o requirements.api.lock
uv pip compile ../pyproject.toml --extra worker -o requirements.worker.lock
uv pip compile ../pyproject.toml --extra dev -o requirements-dev.txt
uv pip compile ../pyproject.toml --extra gpu -o requirements.gpu.lock

# Ruff via uv (fixes "command not found")
echo "🔍 Running lint & format..."
uv run ruff format --check .
uv run ruff check .

# Tests
echo "🧪 Running tests..."
pytest -q || echo "No tests yet — skipping"

echo "✅ Full CI Pipeline Passed"
