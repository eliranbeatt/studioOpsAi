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

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to start...
    timeout /t 10 /nobreak >nul
    
    REM Wait for Docker to be ready
    :wait_docker
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo Still waiting for Docker...
        timeout /t 5 /nobreak >nul
        goto wait_docker
    )
)

REM Start infrastructure services
echo 🐳 Starting infrastructure services (PostgreSQL, MinIO, Langfuse)...
cd infra
docker-compose up -d
cd ..

REM Wait for services to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 10 /nobreak >nul

REM Run database migrations
echo 🗄️  Running database migrations...
cd infra\migrations
python run_migrations.py
cd ..\..

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
echo 🔧 Starting API server on port 8000...
start "StudioOps API" cmd /k "cd apps\api && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for API to start
timeout /t 3 /nobreak >nul

REM Check if web dependencies are installed
if not exist "apps\web\node_modules" (
    echo ⚠️  Web dependencies not found. Installing...
    cd apps\web
    npm install
    cd ..\..
)

REM Start web app
echo 🌐 Starting web app on port 3000...
start "StudioOps Web" cmd /k "cd apps\web && npm run dev"

echo.
echo ✅ All services started successfully!
echo.
echo 📊 Services running:
echo    - Web App: http://localhost:3000
echo    - API Server: http://localhost:8000
echo    - API Documentation: http://localhost:8000/docs
echo    - PostgreSQL: localhost:5432
echo    - MinIO Console: http://localhost:9001
echo    - Langfuse: http://localhost:3100
echo.
echo Press any key to exit this window (services will continue running)
echo ==================================================
pause >nul