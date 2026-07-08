$ErrorActionPreference = "Stop"

Write-Host "=========================================================="
Write-Host "🚀 Starting Industrial Copilot: Knowledge Graph Dashboard"
Write-Host "=========================================================="

$env:PYTHONPATH = "."

if (Test-Path ".venv") {
    . ".venv\Scripts\Activate.ps1"
}

Write-Host "Starting Live IoT/SCADA Simulator..."
$iotProc = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "backend/src/iot_simulator.py"

Write-Host "Starting Unified FastAPI Backend (Graph + Chat + API)..."
$backendProc = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-m uvicorn backend.app:app --host 127.0.0.1 --port 8000"

Write-Host "Waiting for backend to initialize..."
Start-Sleep -Seconds 5

Write-Host "Starting Streamlit Frontend..."
try {
    python -m streamlit run frontend/app.py --server.headless false
} finally {
    Write-Host "Cleaning up background processes..."
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $iotProc.Id -Force -ErrorAction SilentlyContinue
}
