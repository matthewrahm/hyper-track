#!/bin/bash
set -e

trap 'kill 0' EXIT

echo "Starting hyper-track..."
echo "  API:    http://localhost:8003"
echo "  Web:    http://localhost:3004"
echo ""

# Start FastAPI backend
uv run uvicorn api.main:app --reload --port 8003 &

# Start Next.js frontend
cd web && npm run dev -- --port 3004 &

wait
