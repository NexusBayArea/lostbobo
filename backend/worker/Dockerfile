FROM python:3.11-slim

WORKDIR /app

RUN pip install uv supervisor requests

COPY pyproject.toml uv.lock ./
COPY worker ./worker
COPY app ./app

RUN uv pip install --system -e .

COPY ../../docker/supervisor/simhpc.conf /etc/supervisor/conf.d/simhpc.conf

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/simhpc.conf"]