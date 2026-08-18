# Akiya Scout - PowerShell Run Script
# This script sets up and runs the application

Write-Host "Starting Akiya Scout..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -q

# Run the application
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Application will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Health check at: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000