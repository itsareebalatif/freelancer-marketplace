#!/bin/sh
# Runs the API in Docker with live code reload.
# Edit any file and the server restarts itself — no rebuild, no re-run.
set -e

docker build -t freelancer-marketplace .

# -v /app/.venv keeps the container's own Linux virtualenv instead of letting
# your host's (macOS) .venv leak in through the bind mount above it.
docker run --rm -it \
  --name freelancer-api-dev \
  --env-file .env \
  -p 8000:8000 \
  -v "$(pwd)":/app \
  -v /app/.venv \
  freelancer-marketplace \
  sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
