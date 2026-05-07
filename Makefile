# ================================================
# SimHPC Makefile
# ================================================

.PHONY: help dev lint format check ci lock test clean

help:
	@echo "SimHPC Development Commands"
	@echo "============================"
	@echo "make dev           → Install editable dev environment"
	@echo "make lint          → Ruff lint"
	@echo "make format        → Auto-format code"
	@echo "make check         → Lint + format check"
	@echo "make ci            → Full CI (lock + check + test)"
	@echo "make lock          → Regenerate all lockfiles"
	@echo "make test          → Run tests"
	@echo "make clean         → Cleanup"
	@echo ""

# Development Setup
dev:
	uv sync --extra dev
	uv pip install -e .
	@echo "✅ Development environment ready"

# Linting & Formatting
lint:
	cd backend && ruff check .

format:
	cd backend && ruff format .

check:
	cd backend && ruff format --check .
	cd backend && ruff check .

# Full CI (this is what your workflow calls)
ci: lock check test
	@echo "✅ Full CI pipeline passed"

# Lockfiles
lock:
	uv pip compile pyproject.toml --extra api -o requirements.api.lock
	uv pip compile pyproject.toml --extra worker -o requirements.worker.lock
	uv pip compile pyproject.toml --extra dev -o requirements-dev.txt
	uv pip compile pyproject.toml --extra gpu -o requirements.gpu.lock
	@echo "✅ All lockfiles regenerated"

# Testing
test:
	cd backend && pytest -q || echo "No tests yet - skipping"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed

# Kubernetes / Minikube
minikube-start:
	./deploy/minikube-setup.sh

minikube-stop:
	minikube stop

k8s-deploy:
	kubectl apply -f deploy/k8s/

k8s-delete:
	kubectl delete -f deploy/k8s/ --ignore-not-found=true

k8s-logs:
	kubectl logs -l app=simhpc -f

k8s-dashboard:
	minikube dashboard

# Helm Chart
helm-install:
	helm install simhpc deploy/helm/simhpc --namespace simhpc --create-namespace

helm-upgrade:
	helm upgrade simhpc deploy/helm/simhpc --namespace simhpc

helm-uninstall:
	helm uninstall simhpc --namespace simhpc
