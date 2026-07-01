#!/bin/bash
# Enable exit on error
set -e

echo "=========================================================="
echo "🚀 Starting Industrial Copilot: Knowledge Graph Dashboard"
echo "=========================================================="

# Ensure PYTHONPATH includes the current directory
export PYTHONPATH=.

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting Live IoT/SCADA Simulator..."
python3 backend/src/iot_simulator.py &
IOT_PID=$!

echo "Starting Unified FastAPI Backend (Graph + Chat + API)..."
python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait briefly for backend to boot and build the knowledge graph
echo "Waiting for backend to initialize..."
sleep 5

echo "Starting Streamlit Frontend..."
python3 -m streamlit run frontend/app.py --server.headless true

# Cleanup background process on exit
kill $BACKEND_PID
kill $IOT_PID
