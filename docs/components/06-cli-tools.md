# CLI Tools and Utilities Component

## 🛠️ Overview

The **CLI Tools and Utilities** component provides command-line interfaces, automation scripts, and development utilities that support StudioOps AI development, testing, and operational workflows.

### Purpose and Role in StudioOps AI

CLI Tools serve as the **automation and utilities layer** that:
- Provides command-line interfaces for system management
- Automates development workflow tasks
- Supports testing and validation processes
- Handles environment setup and configuration
- Manages database operations and migrations
- Facilitates deployment and operational tasks

## 🏗️ Architecture Overview

```mermaid
graph TB
    Developer[👩‍💻 Developer] --> CLI[🛠️ CLI Tools]
    
    CLI --> DevScripts[📜 Development Scripts]
    CLI --> TestUtils[🧪 Test Utilities]
    CLI --> DbTools[🗄️ Database Tools]
    CLI --> EnvSetup[⚙️ Environment Setup]
    
    DevScripts --> RunDev[🚀 run_dev.*]
    DevScripts --> BuildScripts[🔨 Build Scripts]
    
    TestUtils --> TestRunner[🏃 Test Runners]
    TestUtils --> ValidationTools[✅ Validation Tools]
    
    DbTools --> Migrations[📋 Migration Runner]
    DbTools --> Seeding[🌱 Data Seeding]
    
    EnvSetup --> EnvCheck[🔍 Environment Check]
    EnvSetup --> ConfigSetup[⚙️ Configuration Setup]
```

## 🚀 Development Scripts

### **Quick Start Scripts**

**Windows Command Prompt** (`run_dev.bat`):
```batch
@echo off
echo Starting StudioOps AI Development Environment...

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running or not installed
    pause
    exit /b 1
)

REM Start infrastructure services
echo Starting infrastructure services...
docker-compose -f infra/docker-compose.yaml up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Run database migrations
echo Running database migrations...
python infra/migrations/run_migrations.py

REM Start API server
echo Starting API server...
start "API Server" cmd /c "cd apps/api && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Start web server
echo Starting web development server...
start "Web Server" cmd /c "cd apps/web && npm install && npm run dev"

echo.
echo Development environment started!
echo Web App: http://localhost:3000
echo API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo MinIO Console: http://localhost:9001
echo Langfuse: http://localhost:3100
echo.
pause
```

**PowerShell** (`run_dev.ps1`):
```powershell
Write-Host "Starting StudioOps AI Development Environment..." -ForegroundColor Green

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✓ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running or not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Start infrastructure
Write-Host "Starting infrastructure services..." -ForegroundColor Yellow
docker-compose -f infra/docker-compose.yaml up -d

# Wait for services
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
python infra/migrations/run_migrations.py

# Start API server
Write-Host "Starting API server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Start web server
Write-Host "Starting web development server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web; npm install; npm run dev"

Write-Host "`nDevelopment environment started!" -ForegroundColor Green
Write-Host "Web App: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "Langfuse: http://localhost:3100" -ForegroundColor Cyan

Read-Host "`nPress Enter to continue"
```

**Linux/Mac** (`run_dev.sh`):
```bash
#!/bin/bash
set -e

echo "🚀 Starting StudioOps AI Development Environment..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    exit 1
fi

echo "✅ Docker is available"

# Start infrastructure services
echo "🐳 Starting infrastructure services..."
docker-compose -f infra/docker-compose.yaml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 10

# Run database migrations
echo "📋 Running database migrations..."
python infra/migrations/run_migrations.py

# Check if API dependencies are installed
if [ ! -d "apps/api/venv" ]; then
    echo "📦 Setting up API virtual environment..."
    cd apps/api
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../..
fi

# Check if web dependencies are installed
if [ ! -d "apps/web/node_modules" ]; then
    echo "📦 Installing web dependencies..."
    cd apps/web
    npm install
    cd ../..
fi

# Start API server in background
echo "🔌 Starting API server..."
cd apps/api
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!
cd ../..

# Start web server in background
echo "🌐 Starting web development server..."
cd apps/web
npm run dev &
WEB_PID=$!
cd ../..

echo ""
echo "🎉 Development environment started!"
echo "🌐 Web App: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📦 MinIO Console: http://localhost:9001"
echo "📊 Langfuse: http://localhost:3100"
echo ""
echo "💡 Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $API_PID $WEB_PID 2>/dev/null; docker-compose -f infra/docker-compose.yaml down; echo 'Services stopped.'; exit 0" INT

wait
```

## 🗄️ Database Management Tools

### **Migration Runner** (`run_migration.py`)

```python
#!/usr/bin/env python3
"""Database migration runner with enhanced features"""

import os
import sys
import psycopg2
import argparse
from pathlib import Path
from datetime import datetime

class MigrationRunner:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        self.migrations_dir = Path('infra/migrations')
        
    def run_migrations(self, target=None):
        """Run all pending migrations or up to a specific target"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Ensure migrations table exists
            self._ensure_migrations_table(cursor)
            
            # Get executed migrations
            executed = self._get_executed_migrations(cursor)
            
            # Get available migrations
            available = self._get_available_migrations()
            
            # Filter to pending migrations
            pending = [m for m in available if m.name not in executed]
            
            if target:
                # Run only up to target
                target_idx = next((i for i, m in enumerate(pending) if m.stem == target), None)
                if target_idx is not None:
                    pending = pending[:target_idx + 1]
                else:
                    print(f"Migration '{target}' not found in pending migrations")
                    return False
            
            if not pending:
                print("No pending migrations to run")
                return True
                
            print(f"Running {len(pending)} migration(s)...")
            
            for migration_file in pending:
                print(f"Applying: {migration_file.name}")
                self._run_migration(cursor, migration_file)
                conn.commit()
                
            print("All migrations completed successfully")
            return True
            
        except Exception as e:
            print(f"Migration failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def _ensure_migrations_table(self, cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL UNIQUE,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(32)
            )
        """)

    def _get_executed_migrations(self, cursor):
        cursor.execute("SELECT filename FROM migrations ORDER BY executed_at")
        return {row[0] for row in cursor.fetchall()}

    def _get_available_migrations(self):
        return sorted(self.migrations_dir.glob("*.sql"))

    def _run_migration(self, cursor, migration_file):
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
            
        # Execute migration
        cursor.execute(migration_sql)
        
        # Record in migrations table
        cursor.execute(
            "INSERT INTO migrations (filename) VALUES (%s)",
            (migration_file.name,)
        )

def main():
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--target', help='Target migration to run up to')
    parser.add_argument('--db-url', help='Database URL override')
    
    args = parser.parse_args()
    
    runner = MigrationRunner(args.db_url)
    success = runner.run_migrations(args.target)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## 🧪 Testing Utilities

### **Test Runner Script** (`run_tests.sh`)

```bash
#!/bin/bash
"""Comprehensive testing script for all components"""

set -e

echo "🧪 StudioOps AI Test Suite"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
API_TESTS_PASSED=false
WEB_TESTS_PASSED=false
E2E_TESTS_PASSED=false

# Function to run tests with error handling
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    
    echo -e "\n${YELLOW}Running $suite_name tests...${NC}"
    
    if eval $test_command; then
        echo -e "${GREEN}✅ $suite_name tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $suite_name tests failed${NC}"
        return 1
    fi
}

# Start infrastructure if not running
echo "🐳 Ensuring infrastructure is running..."
docker-compose -f infra/docker-compose.yaml up -d postgres minio
sleep 5

# Run database migrations
echo "📋 Running database migrations..."
python run_migration.py

# API Tests
echo -e "\n${YELLOW}Testing API Backend...${NC}"
cd apps/api

if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

if run_test_suite "API Backend" "pytest tests/ -v --cov=. --cov-report=html"; then
    API_TESTS_PASSED=true
fi

cd ../..

# Web Tests
echo -e "\n${YELLOW}Testing Web Frontend...${NC}"
cd apps/web

if [ ! -d "node_modules" ]; then
    npm install
fi

if run_test_suite "Web Frontend" "npm test -- --coverage --watchAll=false"; then
    WEB_TESTS_PASSED=true
fi

cd ../..

# E2E Tests
echo -e "\n${YELLOW}Running End-to-End Tests...${NC}"
cd apps/web

# Start application for E2E tests
echo "Starting application for E2E tests..."
npm run build &
BUILD_PID=$!
wait $BUILD_PID

npm start &
APP_PID=$!
sleep 10

if run_test_suite "End-to-End" "npm run test:e2e"; then
    E2E_TESTS_PASSED=true
fi

# Cleanup
kill $APP_PID 2>/dev/null || true
cd ../..

# Test Results Summary
echo -e "\n${YELLOW}Test Results Summary${NC}"
echo "===================="

if [ "$API_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✅ API Backend Tests: PASSED${NC}"
else
    echo -e "${RED}❌ API Backend Tests: FAILED${NC}"
fi

if [ "$WEB_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✅ Web Frontend Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Web Frontend Tests: FAILED${NC}"
fi

if [ "$E2E_TESTS_PASSED" = true ]; then
    echo -e "${GREEN}✅ End-to-End Tests: PASSED${NC}"
else
    echo -e "${RED}❌ End-to-End Tests: FAILED${NC}"
fi

# Overall result
if [ "$API_TESTS_PASSED" = true ] && [ "$WEB_TESTS_PASSED" = true ] && [ "$E2E_TESTS_PASSED" = true ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some tests failed${NC}"
    exit 1
fi
```

## ⚙️ Environment Setup Tools

### **Environment Checker** (`SuperClaude_Framework/bin/checkEnv.js`)

```javascript
#!/usr/bin/env node
/**
 * Environment validation tool for StudioOps AI
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

class EnvironmentChecker {
    constructor() {
        this.checks = [];
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0
        };
    }

    async runChecks() {
        console.log('🔍 StudioOps AI Environment Check');
        console.log('==================================\n');

        await this.checkNode();
        await this.checkPython();
        await this.checkDocker();
        await this.checkDependencies();
        await this.checkPorts();
        await this.checkEnvironmentFiles();

        this.printSummary();
    }

    async checkNode() {
        try {
            const version = await this.execCommand('node --version');
            const majorVersion = parseInt(version.replace('v', '').split('.')[0]);
            
            if (majorVersion >= 16) {
                this.logSuccess(`Node.js ${version.trim()} ✅`);
                this.results.passed++;
            } else {
                this.logError(`Node.js ${version.trim()} (requires >= 16) ❌`);
                this.results.failed++;
            }
        } catch (error) {
            this.logError('Node.js not found ❌');
            this.results.failed++;
        }
    }

    async checkPython() {
        try {
            const version = await this.execCommand('python3 --version');
            const versionNumber = version.replace('Python ', '').trim();
            const [major, minor] = versionNumber.split('.').map(Number);
            
            if (major >= 3 && minor >= 9) {
                this.logSuccess(`Python ${versionNumber} ✅`);
                this.results.passed++;
            } else {
                this.logError(`Python ${versionNumber} (requires >= 3.9) ❌`);
                this.results.failed++;
            }
        } catch (error) {
            this.logError('Python 3 not found ❌');
            this.results.failed++;
        }
    }

    async checkDocker() {
        try {
            const version = await this.execCommand('docker --version');
            this.logSuccess(`Docker ${version.trim()} ✅`);
            this.results.passed++;

            try {
                await this.execCommand('docker info');
                this.logSuccess('Docker daemon is running ✅');
                this.results.passed++;
            } catch (error) {
                this.logError('Docker daemon is not running ❌');
                this.results.failed++;
            }
        } catch (error) {
            this.logError('Docker not found ❌');
            this.results.failed++;
        }
    }

    async checkDependencies() {
        const webDepsPath = path.join(process.cwd(), 'apps/web/node_modules');
        const apiVenvPath = path.join(process.cwd(), 'apps/api/venv');

        if (fs.existsSync(webDepsPath)) {
            this.logSuccess('Web dependencies installed ✅');
            this.results.passed++;
        } else {
            this.logWarning('Web dependencies not installed ⚠️');
            this.results.warnings++;
        }

        if (fs.existsSync(apiVenvPath)) {
            this.logSuccess('API virtual environment exists ✅');
            this.results.passed++;
        } else {
            this.logWarning('API virtual environment not found ⚠️');
            this.results.warnings++;
        }
    }

    async checkPorts() {
        const ports = [3000, 8000, 5432, 9000, 3100];
        
        for (const port of ports) {
            try {
                await this.checkPort(port);
                this.logWarning(`Port ${port} is in use ⚠️`);
                this.results.warnings++;
            } catch (error) {
                this.logSuccess(`Port ${port} is available ✅`);
                this.results.passed++;
            }
        }
    }

    async checkEnvironmentFiles() {
        const envFiles = [
            '.env.example',
            'apps/web/.env.local',
            'apps/api/.env'
        ];

        for (const envFile of envFiles) {
            if (fs.existsSync(path.join(process.cwd(), envFile))) {
                this.logSuccess(`${envFile} exists ✅`);
                this.results.passed++;
            } else {
                this.logWarning(`${envFile} not found ⚠️`);
                this.results.warnings++;
            }
        }
    }

    async execCommand(command) {
        return new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout);
                }
            });
        });
    }

    async checkPort(port) {
        return new Promise((resolve, reject) => {
            const net = require('net');
            const server = net.createServer();
            
            server.listen(port, () => {
                server.once('close', () => resolve());
                server.close();
            });
            
            server.on('error', (err) => {
                reject(err);
            });
        });
    }

    logSuccess(message) {
        console.log(`\x1b[32m${message}\x1b[0m`);
    }

    logError(message) {
        console.log(`\x1b[31m${message}\x1b[0m`);
    }

    logWarning(message) {
        console.log(`\x1b[33m${message}\x1b[0m`);
    }

    printSummary() {
        console.log('\n📊 Summary');
        console.log('==========');
        console.log(`✅ Passed: ${this.results.passed}`);
        console.log(`❌ Failed: ${this.results.failed}`);
        console.log(`⚠️  Warnings: ${this.results.warnings}`);

        if (this.results.failed === 0) {
            console.log('\n🎉 Environment is ready for development!');
        } else {
            console.log('\n🔧 Please fix the failed checks before proceeding.');
        }
    }
}

// Run if called directly
if (require.main === module) {
    const checker = new EnvironmentChecker();
    checker.runChecks().catch(console.error);
}

module.exports = EnvironmentChecker;
```

## 🎯 Key CLI Tools Summary

### **Development Workflow**
- **Quick Start Scripts**: One-command development environment setup
- **Cross-Platform Support**: Windows, Mac, and Linux compatibility
- **Dependency Management**: Automatic dependency installation and validation
- **Service Orchestration**: Coordinated startup of all required services

### **Database Management**
- **Migration Runner**: Robust database migration system
- **Rollback Support**: Safe migration rollback capabilities
- **Seed Data Management**: Consistent test data setup
- **Schema Validation**: Database schema consistency checking

### **Testing Automation**
- **Comprehensive Test Runner**: All test types in one script
- **Coverage Reporting**: Automatic test coverage generation
- **E2E Test Integration**: Complete workflow testing
- **CI/CD Ready**: Scripts optimized for automation

### **Environment Validation**
- **Dependency Checking**: Validate all required tools and versions
- **Port Availability**: Check for port conflicts
- **Configuration Validation**: Verify environment file setup
- **Health Monitoring**: Service health check automation

These CLI tools provide essential automation and utilities that streamline the development experience, reduce setup complexity, and ensure consistent environments across the StudioOps AI development lifecycle.