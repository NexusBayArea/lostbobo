FROM python:3.11-slim

WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv supervisor requests

# FIXED: Points to the backend sub-directory for the manifest
COPY backend/pyproject.toml backend/uv.lock* ./

# Copy backend source components with consistent paths
COPY backend/app ./app
COPY backend/packages ./packages
COPY backend/autoscaler ./autoscaler
COPY backend/compiler ./compiler
COPY backend/infra ./infra
COPY backend/tools ./tools
COPY backend/worker ./worker

# Install using the system python via uv
RUN uv pip install --system -e .

COPY docker/supervisor.conf /etc/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
