# start_contracts.ps1
Set-Location "$PSScriptRoot\contracts"
Write-Host "Starting Hardhat Local Blockchain Node on http://127.0.0.1:8545..." -ForegroundColor Yellow
npx hardhat node
