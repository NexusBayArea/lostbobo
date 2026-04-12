FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
# Note: we need to copy app and packages for the build to work
COPY app ./app
COPY packages ./packages

RUN uv pip install --system -e .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
