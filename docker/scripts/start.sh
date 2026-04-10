#!/bin/bash
set -e

echo "[SimHPC] Starting unified services with supervisord..."

cd /app
export PYTHONPATH=/app

exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
