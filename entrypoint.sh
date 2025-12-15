#!/usr/bin/env bash
set -euo pipefail

echo "Running alembic migrations..."
alembic upgrade head

echo "Starting FastAPI"
exec fastapi dev src/main.py --host 0.0.0.0 --port 80
