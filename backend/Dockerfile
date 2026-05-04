FROM python:3.11-slim AS builder

WORKDIR /app
COPY backend/requirements*.lock ./
RUN pip install --no-cache-dir -r requirements.api.lock

# Production runtime image
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend /app/backend

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend

EXPOSE 8080

# Use supervisor or direct gunicorn
CMD ["python", "-m", "backend"]
