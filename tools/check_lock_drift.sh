#!/usr/bin/env bash
set -e

uv pip compile backend/pyproject.toml -o backend/requirements.lock.tmp

if ! diff -q backend/requirements.lock backend/requirements.lock.tmp > /dev/null; then
  echo "❌ Dependency drift detected. Run: uv pip compile backend/pyproject.toml -o backend/requirements.lock"
  rm backend/requirements.lock.tmp
  exit 1
fi

rm backend/requirements.lock.tmp
echo "✅ Dependencies locked and consistent"
