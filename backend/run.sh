#!/bin/bash

echo "🚀 Starting GitHub Repo Analyzer..."

# Check if services are running
if ! docker ps | grep -q repo-analyzer-postgres; then
    echo "🐳 Starting Docker services..."
    docker-compose up -d
    sleep 5
fi

# Activate virtual environment and start backend
echo "🔧 Starting backend..."
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Application started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit" INT
wait
