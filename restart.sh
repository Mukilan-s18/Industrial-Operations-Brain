#!/bin/bash
# restart.sh — Kill uvicorn and restart instantly
# Usage: ./restart.sh

echo "Stopping uvicorn..."
pkill -f "uvicorn ingestion.main:app" 2>/dev/null || true
sleep 1

echo "Starting uvicorn..."
uvicorn ingestion.main:app --host 0.0.0.0 --port 8000 --reload &

echo "Service restarted on port 8000"
echo "Docs: http://localhost:8000/docs"
echo "Health: http://localhost:8000/health"
