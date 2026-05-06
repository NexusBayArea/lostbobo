# ================================================
# SimHPC Makefile
# Common development and CI commands
# ================================================

.PHONY: help lint format check lock test clean install dev

# Default target
help:
	@echo "SimHPC Development Commands"
	@echo "============================"
	@echo "make lint          → Run ruff lint + format check"
	@echo "make format        → Auto-format all code"
	@echo "make check         → Full CI-like check (lint + format)"
	@echo "make lock          → Regenerate all requirements lockfiles"
	@echo "make test          → Run tests"
	@echo "make dev          → Install in editable mode with dev extras"
	@echo "make clean        → Remove caches and pyc files"
	@echo ""

# Linting & Formatting
lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

check:
	cd backend && ruff format --check .
	cd backend && ruff check .

# Lockfile Management
lock:
	uv pip compile pyproject.toml --extra api -o requirements.api.lock
	uv pip compile pyproject.toml --extra worker -o requirements.worker.lock
	uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
	uv pip compile pyproject.toml --extra gpu -o requirements.gpu.lock
	@echo "✅ All lockfiles regenerated"

# Testing
test:
	cd backend && pytest -q

# Development Setup
dev:
	uv sync --extra dev
	uv pip install -e .
	@echo "✅ Development environment ready"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "✅ Cleanup completed"

# Full CI-like check (used in workflows)
ci: check lock test
	@echo "✅ Full CI checks passed"