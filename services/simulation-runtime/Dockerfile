FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/simulation-runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/simulation-runtime/ .
COPY services/proto/ services/proto/

EXPOSE 50053

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50053'); grpc.channel_ready_future(channel).result(timeout=5)"

CMD ["python", "-u", "sim_server.py"]
