#!/bin/bash

# StudioOps AI Development Runner
# Starts both the web app and API server concurrently

echo "🚀 Starting StudioOps AI Development Environment..."
echo "=================================================="

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $WEB_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set up trap to handle Ctrl+C
trap cleanup SIGINT SIGTERM

# Check if we're in the right directory
if [ ! -d "apps/web" ] || [ ! -d "apps/api" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed or not in PATH"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if API dependencies are installed
if [ ! -d "apps/api/venv" ]; then
    echo "⚠️  API virtual environment not found. Setting up..."
    cd apps/api
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../..
fi

# Start API server in background
echo "🔧 Starting API server on port 8001..."
cd apps/api
source venv/bin/activate
uvicorn simple_main:app --host 0.0.0.0 --port 8001 --reload >> ../../app.log 2>&1 &
API_PID=$!
cd ../..

# Wait a moment for API to start
sleep 2

# Start web app in background
echo "🌐 Starting web app on port 3000..."
cd apps/web
npm run dev >> ../../app.log 2>&1 &
WEB_PID=$!
cd ../..

echo ""
echo "✅ Both services started successfully!"
echo ""
echo "📊 Services running:"
echo "   - Web App: http://localhost:3000"
echo "   - API Server: http://localhost:8001"
echo "   - API Documentation: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop both services"
echo "=================================================="

# Wait for both processes
wait $WEB_PID $API_PID