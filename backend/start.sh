#!/bin/bash

echo "🚀 Starting RepoAnalyzer..."

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d
sleep 10

# Setup backend
echo "🔧 Setting up backend..."
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt -q

# Initialize database
echo "💾 Initializing database..."
python -c "from utils.database import engine, Base; from models.database_models import *; Base.metadata.create_all(bind=engine)" 2>/dev/null || echo "Database already initialized"

# Start backend
echo "🚀 Starting backend..."
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Setup and start frontend
echo "🎨 Setting up frontend..."
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ RepoAnalyzer is running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Frontend:  http://localhost:3000"
echo "🔌 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/api/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose down" EXIT

# Wait
wait
