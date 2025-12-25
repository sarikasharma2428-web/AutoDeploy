#!/bin/bash
set -e

API_URL=${1:-http://localhost:8000}

echo "🏁 Running API benchmarks..."

# Test health endpoint
echo "Testing /health..."
ab -n 1000 -c 10 $API_URL/health

# Test status endpoint
echo "Testing /api/v1/status..."
ab -n 1000 -c 10 $API_URL/api/v1/status

echo "✅ Benchmark completed!"
