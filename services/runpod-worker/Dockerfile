FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
ENV SIMHPC_KEY=alpha-secret-key

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
