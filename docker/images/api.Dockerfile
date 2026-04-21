FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
COPY app ./app

RUN uv pip install --system -e .

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
