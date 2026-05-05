.PHONY: ci ci-full lock format dev-install

ci:
	python backend/tools/run_ci.py

ci-full:
	python backend/tools/run_ci.py

lock:
	uv pip compile pyproject.toml --extra api    -o requirements.api.lock
	uv pip compile pyproject.toml --extra worker -o requirements.worker.lock
	uv pip compile pyproject.toml --extra dev    -o requirements-dev.txt
	uv pip compile pyproject.toml --extra gpu    -o requirements.gpu.lock

format:
	python -m ruff format .
	python -m ruff check . --fix --unsafe-fixes

dev-install:
	uv sync --extra dev