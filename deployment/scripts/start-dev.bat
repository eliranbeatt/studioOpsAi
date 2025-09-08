@echo off
setlocal enabledelayedexpansion

REM StudioOps AI Development Environment Startup Script for Windows

echo 🚀 Starting StudioOps AI Development Environment
echo ================================================

REM Load environment variables
if exist .env (
    echo 📝 Loading environment variables from .env
    for /f "tokens=*" %%i in ('type .env ^| findstr /v "^#"') do set "%%i"
) else (
    echo ⚠️  No .env file found. Setting up development environment...
    python config_manager.py setup --env development
    for /f "tokens=*" %%i in ('type .env ^| findstr /v "^#"') do set "%%i"
)

REM Validate configuration
echo 🔍 Validating configuration...
python config_manager.py validate
if %errorlevel% neq 0 (
    echo ❌ Configuration validation failed. Please fix configuration issues.
    exit /b 1
)

REM Check PostgreSQL service
echo 🗄️  Checking PostgreSQL service...
sc query postgresql-x64-14 >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  PostgreSQL service not found. Please ensure PostgreSQL is installed.
) else (
    sc query postgresql-x64-14 | findstr "RUNNING" >nul
    if %errorlevel% neq 0 (
        echo Starting PostgreSQL service...
        net start postgresql-x64-14
    ) else (
        echo ✅ PostgreSQL is already running
    )
)

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
for /l %%i in (1,1,30) do (
    pg_isready -h %API_HOST% -p 5432 -U studioops >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ PostgreSQL is ready
        goto postgres_ready
    )
    timeout /t 1 /nobreak >nul
)
:postgres_ready

REM Run database migrations
echo 🔄 Running database migrations...
python database_migration_script.py

REM Start MinIO if configured for localhost
if defined MINIO_ENDPOINT (
    echo %MINIO_ENDPOINT% | findstr "localhost" >nul
    if !errorlevel! equ 0 (
        echo 🗂️  Starting MinIO server...
        tasklist /fi "imagename eq minio.exe" 2>nul | findstr "minio.exe" >nul
        if !errorlevel! neq 0 (
            if not exist minio-data mkdir minio-data
            start /b minio server minio-data --console-address ":9001"
            echo MinIO started
            
            REM Wait for MinIO to be ready
            echo ⏳ Waiting for MinIO to be ready...
            for /l %%i in (1,1,30) do (
                curl -s http://localhost:9000/minio/health/live >nul 2>&1
                if !errorlevel! equ 0 (
                    echo ✅ MinIO is ready
                    goto minio_ready
                )
                timeout /t 1 /nobreak >nul
            )
        ) else (
            echo ✅ MinIO is already running
        )
    )
)
:minio_ready

REM Check service connectivity
echo 🔍 Checking service connectivity...
python config_manager.py check-services

REM Start API server
echo 🖥️  Starting API server...
cd apps\api
start /b uvicorn main:app --host %API_HOST% --port %API_PORT% --reload
cd ..\..

REM Wait for API server to be ready
echo ⏳ Waiting for API server to be ready...
for /l %%i in (1,1,60) do (
    curl -s http://%API_HOST%:%API_PORT%/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ API server is ready
        goto api_ready
    )
    timeout /t 1 /nobreak >nul
)
:api_ready

REM Start frontend development server
echo 🌐 Starting frontend development server...
cd apps\web
if not exist node_modules (
    echo 📦 Installing frontend dependencies...
    npm install
)
start /b npm run dev
cd ..\..

REM Wait for frontend to be ready
echo ⏳ Waiting for frontend to be ready...
for /l %%i in (1,1,60) do (
    curl -s http://localhost:3000 >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Frontend is ready
        goto web_ready
    )
    timeout /t 1 /nobreak >nul
)
:web_ready

REM Run system validation
echo 🔍 Running system validation...
python test_startup_validation.py

echo.
echo 🎉 StudioOps AI Development Environment is ready!
echo ================================================
echo 🌐 Frontend: http://localhost:3000
echo 🖥️  API Server: http://%API_HOST%:%API_PORT%
echo 📚 API Docs: http://%API_HOST%:%API_PORT%/docs
if defined MINIO_ENDPOINT (
    echo %MINIO_ENDPOINT% | findstr "localhost" >nul
    if !errorlevel! equ 0 (
        echo 🗂️  MinIO Console: http://localhost:9001
    )
)
echo.
echo 📊 Service Status:
python config_manager.py check-services | findstr /r "✅\|❌\|⚠️"
echo.
echo 🛑 To stop all services, run: deployment\scripts\stop-services.bat
echo.
echo Press any key to stop all services...
pause >nul

REM Stop services
echo.
echo 🛑 Shutting down services...

REM Stop processes by port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%API_PORT%') do taskkill /f /pid %%a >nul 2>&1
echo 🖥️  API server stopped

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
echo 🌐 Frontend stopped

tasklist /fi "imagename eq minio.exe" 2>nul | findstr "minio.exe" >nul
if !errorlevel! equ 0 (
    taskkill /f /im minio.exe >nul 2>&1
    echo 🗂️  MinIO stopped
)

echo ✅ All services stopped