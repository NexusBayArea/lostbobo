#!/bin/bash

set -e

API_URL=${API_URL:-http://localhost:8080}
HEALTH_ENDPOINT="$API_URL/health"

echo "⏳ Waiting for API health at $HEALTH_ENDPOINT..."

for i in {1..60}; do
  # Use curl to check status field in JSON
  RESPONSE=$(curl -s "$HEALTH_ENDPOINT" || echo '{"status": "down"}')
  STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)

  if [ "$STATUS" = "ok" ]; then
    echo "✅ API is healthy"
    exit 0
  fi

  echo "API not ready yet... ($i/60) - Status: $STATUS"
  sleep 2
done

echo "❌ API failed to become healthy"
exit 1
