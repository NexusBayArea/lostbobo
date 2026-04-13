# syntax=docker/dockerfile:1

FROM ghcr.io/nexusbayarea/simhpc-base:latest

WORKDIR /app

COPY . .

ENV SERVICE_ROLE=api

CMD ["python", "-m", "app.main"]