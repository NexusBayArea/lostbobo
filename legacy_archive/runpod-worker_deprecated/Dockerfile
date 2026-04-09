FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-runtime-ubuntu22.04

WORKDIR /workspace

# Install system dependencies and security patches
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Environment variables
ENV PYTHONPATH=/workspace
ENV MODEL_PATH=/workspace/models/mistral-7b-v0.1
ENV SIMHPC_KEY=${SIMHPC_KEY}

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
