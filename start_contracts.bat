@echo off
cd /d "%~dp0contracts"
echo Starting Hardhat Local Blockchain Node on http://127.0.0.1:8545...
npx hardhat node
pause
