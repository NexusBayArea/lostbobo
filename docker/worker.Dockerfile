FROM python:3.11-slim

WORKDIR /app

RUN pip install uv supervisor requests

COPY pyproject.toml uv.lock ./
COPY worker.py ./worker.py
COPY app ./app
COPY packages ./packages

RUN uv pip install --system -e .

COPY docker/supervisor.conf /etc/supervisord.conf

# Worker might need more libraries (ffmpeg, etc.) depending on simulations
# RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

CMD ["supervisord", "-c", "/etc/supervisord.conf"]
