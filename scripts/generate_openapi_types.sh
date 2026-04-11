#!/bin/bash
set -e
# Start FastAPI server
uvicorn run_api:app --port 8000 &
PID=$!
# Wait for server to be ready
until curl -s http://localhost:8000/openapi.json > /dev/null; do
  sleep 1
done
# Fetch OpenAPI spec
curl -s http://localhost:8000/openapi.json > openapi.json
# Generate TypeScript types
npx openapi-typescript openapi.json --output shared/openapi-types.ts
# Clean up
kill $PID
