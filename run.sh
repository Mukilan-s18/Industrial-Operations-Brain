#!/bin/bash
# Enable exit on error
set -e

echo "=========================================================="
echo "🚀 Starting Industrial Copilot: Knowledge Graph Dashboard"
echo "=========================================================="

# Ensure PYTHONPATH includes the current directory
export PYTHONPATH=.

# Start the uvicorn development server
.venv/bin/uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
