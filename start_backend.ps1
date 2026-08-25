# start_backend.ps1
Set-Location "$PSScriptRoot\backend"
Write-Host "Starting Bhoomi Setu FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
python -m uvicorn main:app --reload --port 8000
