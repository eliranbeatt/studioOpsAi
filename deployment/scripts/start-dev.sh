#!/bin/bash

# StudioOps AI Development Environment Startup Script

set -e

echo "🚀 Starting StudioOps AI Development Environment"
echo "================================================"

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Setting up development environment..."
    python config_manager.py setup --env development
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate configuration
echo "🔍 Validating configuration..."
python config_manager.py validate
if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed. Please fix configuration issues."
    exit 1
fi

# Start PostgreSQL if not running
echo "🗄️  Checking PostgreSQL service..."
if ! pgrep -x "postgres" > /dev/null; then
    echo "Starting PostgreSQL..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql
    elif command -v service &> /dev/null; then
        sudo service postgresql start
    else
        echo "⚠️  Please start PostgreSQL manually"
    fi
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h ${API_HOST:-localhost} -p 5432 -U studioops; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    sleep 1
done

# Run database migrations
echo "🔄 Running database migrations..."
python database_migration_script.py

# Start MinIO if configured
if [ ! -z "$MINIO_ENDPOINT" ] && [[ "$MINIO_ENDPOINT" == *"localhost"* ]]; then
    echo "🗂️  Starting MinIO server..."
    if ! pgrep -f "minio server" > /dev/null; then
        mkdir -p ./minio-data
        minio server ./minio-data --console-address ":9001" &
        MINIO_PID=$!
        echo "MinIO started with PID: $MINIO_PID"
        
        # Wait for MinIO to be ready
        echo "⏳ Waiting for MinIO to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
                echo "✅ MinIO is ready"
                break
            fi
            sleep 1
        done
    else
        echo "✅ MinIO is already running"
    fi
fi

# Check service connectivity
echo "🔍 Checking service connectivity..."
python config_manager.py check-services

# Start API server
echo "🖥️  Starting API server..."
cd apps/api
uvicorn main:app --host ${API_HOST:-127.0.0.1} --port ${API_PORT:-8003} --reload &
API_PID=$!
cd ../..

# Wait for API server to be ready
echo "⏳ Waiting for API server to be ready..."
for i in {1..60}; do
    if curl -s http://${API_HOST:-127.0.0.1}:${API_PORT:-8003}/health > /dev/null 2>&1; then
        echo "✅ API server is ready"
        break
    fi
    sleep 1
done

# Start frontend development server
echo "🌐 Starting frontend development server..."
cd apps/web
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
WEB_PID=$!
cd ../..

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is ready"
        break
    fi
    sleep 1
done

# Run system validation
echo "🔍 Running system validation..."
python test_startup_validation.py

echo ""
echo "🎉 StudioOps AI Development Environment is ready!"
echo "================================================"
echo "🌐 Frontend: http://localhost:3000"
echo "🖥️  API Server: http://${API_HOST:-127.0.0.1}:${API_PORT:-8003}"
echo "📚 API Docs: http://${API_HOST:-127.0.0.1}:${API_PORT:-8003}/docs"
if [ ! -z "$MINIO_ENDPOINT" ] && [[ "$MINIO_ENDPOINT" == *"localhost"* ]]; then
    echo "🗂️  MinIO Console: http://localhost:9001"
fi
echo ""
echo "📊 Service Status:"
python config_manager.py check-services | grep -E "(✅|❌|⚠️)"
echo ""
echo "🛑 To stop all services, run: ./scripts/stop-services.sh"
echo ""

# Keep script running and handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null || true
        echo "🌐 Frontend stopped"
    fi
    
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        echo "🖥️  API server stopped"
    fi
    
    if [ ! -z "$MINIO_PID" ]; then
        kill $MINIO_PID 2>/dev/null || true
        echo "🗂️  MinIO stopped"
    fi
    
    echo "✅ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Press Ctrl+C to stop all services..."
wait