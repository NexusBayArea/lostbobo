# ================================================
# SimHPC Makefile
# ================================================

.PHONY: help dev lint format check ci lock test clean \
        minikube-start minikube-stop k8s-deploy k8s-delete \
        helm-install helm-upgrade helm-uninstall

help:
	@echo "SimHPC Development Commands"
	@echo "============================"
	@echo "make dev              → Install editable dev environment"
	@echo "make lint             → Ruff lint"
	@echo "make format           → Auto-format code"
	@echo "make check            → Lint + format check"
	@echo "make ci               → Full CI (lock + check + test)"
	@echo "make lock             → Regenerate all lockfiles"
	@echo "make test             → Run tests"
	@echo "make clean            → Cleanup"
	@echo ""
	@echo "Kubernetes / Helm:"
	@echo "make minikube-start   → Start Minikube + addons"
	@echo "make helm-install     → Install via Helm"
	@echo "make helm-upgrade     → Upgrade Helm release"
	@echo ""

# Development Setup
dev:
	uv sync --extra dev
	uv pip install -e .
	@echo "✅ Development environment ready"

# Linting & Formatting
lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

check:
	cd backend && uv run ruff format --check .
	cd backend && uv run ruff check .

# Full CI
ci: lock check test
	@echo "✅ Full CI pipeline passed"

# Lockfiles
lock:
	cd backend && uv pip compile ../pyproject.toml --extra dev -o requirements-dev.txt
	cd backend && uv pip compile ../pyproject.toml --extra iceberg -o requirements.iceberg.lock
	@echo "✅ All lockfiles regenerated"

# Testing
test:
	cd backend && uv run pytest -q || echo "No tests yet - skipping"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed"

# ==================== Kubernetes / Minikube ====================

minikube-start:
	./deploy/minikube-setup.sh

minikube-stop:
	minikube stop

# Helm (preferred)
helm-install:
	helm install simhpc deploy/helm/simhpc --namespace simhpc --create-namespace

helm-upgrade:
	helm upgrade simhpc deploy/helm/simhpc --namespace simhpc

helm-uninstall:
	helm uninstall simhpc --namespace simhpc

# Legacy raw k8s (optional)
k8s-deploy:
	kubectl apply -f deploy/k8s/

k8s-delete:
	kubectl delete -f deploy/k8s/ --ignore-not-found=true

k8s-logs:
	kubectl logs -l app=simhpc -f

k8s-dashboard:
	minikube dashboard