# ============================================
# simhpc-worker: Heavy compute image (~1GB)
# numpy, scipy, matplotlib, fpdf2
# Runs on RunPod GPU pods, autoscaled
# ============================================

# --- STAGE 1: Build ---
FROM python:3.11-slim AS builder

WORKDIR /build

# System libs for scipy / numpy C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- STAGE 2: Runtime ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime shared libs (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libblas3 \
    liblapack3 \
    libsuitesparse-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled packages from builder
COPY --from=builder /install /usr/local

# Copy heavy compute code
COPY robustness_service.py .
COPY pdf_service.py .
COPY ai_report_service.py .
COPY services/ ./services/
COPY fonts/ ./fonts/

# Security: non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# No EXPOSE — worker is not a web server, it polls Redis

CMD ["python", "-c", "print('Worker image ready. Use worker.py to poll Redis queue.')"]
