# StudioOps AI Development Runner (PowerShell)
# Starts both the web app and API server

Write-Host "🚀 Starting StudioOps AI Development Environment..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "apps/web") -or -not (Test-Path "apps/api")) {
    Write-Host "❌ Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
try {
    $null = Get-Command node -ErrorAction Stop
} catch {
    Write-Host "❌ Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Python is available
try {
    $null = Get-Command python -ErrorAction Stop
} catch {
    Write-Host "❌ Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if API dependencies are installed
if (-not (Test-Path "apps/api/venv")) {
    Write-Host "⚠️  API virtual environment not found. Setting up..." -ForegroundColor Yellow
    Set-Location "apps/api"
    python -m venv venv
    & "venv/Scripts/activate.ps1"
    pip install -r requirements.txt
    Set-Location "../../"
}

# Start API server
Write-Host "🔧 Starting API server on port 8001..." -ForegroundColor Cyan
$apiProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd apps/api && call venv/Scripts/activate.bat && uvicorn simple_main:app --host 0.0.0.0 --port 8001 --reload" -PassThru -WindowStyle Normal

# Wait a moment for API to start
Start-Sleep -Seconds 2

# Start web app
Write-Host "🌐 Starting web app on port 3000..." -ForegroundColor Cyan
$webProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd apps/web && npm run dev" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "✅ Both services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services running:" -ForegroundColor White
Write-Host "   - Web App: http://localhost:3000" -ForegroundColor Yellow
Write-Host "   - API Server: http://localhost:8001" -ForegroundColor Yellow
Write-Host "   - API Documentation: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop this script (services will continue running)" -ForegroundColor Gray
Write-Host "==================================================" -ForegroundColor Cyan

# Wait for user input to keep the window open
Read-Host "Press Enter to exit" | Out-Null