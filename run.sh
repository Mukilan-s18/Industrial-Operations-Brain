#!/bin/bash
# Enable exit on error
set -e

echo "=========================================================="
echo "🚀 Starting Industrial Copilot: Knowledge Graph Dashboard"
echo "=========================================================="

# Ensure PYTHONPATH includes the current directory
export PYTHONPATH=.

echo "Starting FastAPI Backend..."
python -m uvicorn src.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait briefly for backend to boot
sleep 2

echo "Starting Streamlit Frontend..."
python -m streamlit run app.py --server.headless true

# Cleanup background process on exit
kill $BACKEND_PID
