# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11.8-slim@sha256:0d1d6fc5d7b40f5f3e5f5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e AS builder

WORKDIR /build

# Install compilation tools for NumPy, SciPy, and other C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies into a wheelhouse or specific prefix
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ============================================
# STAGE 2: Runtime (Production)
# ============================================
FROM python:3.11.8-slim@sha256:0d1d6fc5d7b40f5f3e5f5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e

# Performance & Python behavior settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PATH="/usr/local/bin:$PATH"

# Redis URL must be set at runtime
# docker run -e REDIS_URL=redis://redis:6379/0

WORKDIR /app

# Install ONLY the shared libraries needed at runtime for math/physics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libblas3 \
    liblapack3 \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the pre-compiled packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application assets
# Note: Ensure 'fonts/' is in the same directory as pdf_service.py
COPY fonts ./fonts
COPY . .

# Security: Run as non-privileged user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Documentation & Health
EXPOSE 8000

# Healthcheck ensures the API is actually responding before routing traffic
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Production server configuration
# Using 4 workers for a balance between concurrency and memory usage
CMD ["gunicorn", "api:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
