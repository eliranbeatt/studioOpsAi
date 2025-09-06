@echo off
chcp 65001 >nul

echo 🚀 Starting StudioOps AI Development Environment...
echo ==================================================

REM Check if we're in the right directory
if not exist "apps\web" (
    echo ❌ Error: Please run this script from the project root directory
    pause
    exit /b 1
)

if not exist "apps\api" (
    echo ❌ Error: Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if API dependencies are installed
if not exist "apps\api\venv" (
    echo ⚠️  API virtual environment not found. Setting up...
    cd apps\api
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..\..
)

REM Start API server
echo 🔧 Starting API server on port 8001...
start "StudioOps API" cmd /k "cd apps\api && call venv\Scripts\activate.bat && uvicorn simple_main:app --host 0.0.0.0 --port 8001 --reload"

REM Wait a moment for API to start
timeout /t 2 /nobreak >nul

REM Start web app
echo 🌐 Starting web app on port 3000...
start "StudioOps Web" cmd /k "cd apps\web && npm run dev"

echo.
echo ✅ Both services started successfully!
echo.
echo 📊 Services running:
echo    - Web App: http://localhost:3000
echo    - API Server: http://localhost:8001
echo    - API Documentation: http://localhost:8001/docs
echo.
echo Press any key to exit this window (services will continue running)
echo ==================================================
pause >nul