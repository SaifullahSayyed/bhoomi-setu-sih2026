# start_frontend.ps1
Set-Location "$PSScriptRoot\frontend"
Write-Host "Starting Bhoomi Setu React Frontend on http://localhost:5173..." -ForegroundColor Cyan
npm run dev
