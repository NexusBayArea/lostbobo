FROM python:3.11-slim

WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv supervisor requests

# FIXED: Points to the backend sub-directory for the manifest
COPY backend/pyproject.toml backend/uv.lock* ./

# Copy the app and packages from the backend folder
COPY backend/app ./app
COPY backend/packages ./packages
# If worker.py is in the backend root, use this:
COPY backend/worker/worker.py ./worker.py

# Install using the system python via uv
RUN uv pip install --system -e .

COPY docker/supervisor.conf /etc/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
