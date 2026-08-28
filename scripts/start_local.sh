#!/bin/bash
# ================================================================
# AWS Bedrock AI Gateway - Start Script
# Backend -> AWS RDS PostgreSQL + ElastiCache Redis (VPC)
# Frontend -> localhost:3000
# ================================================================
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/venv/bin/activate"

# Load local .env if available
if [ -f "$ROOT/.env" ]; then
    export $(grep -v '^#' "$ROOT/.env" | xargs)
fi

export ENVIRONMENT=${ENVIRONMENT:-production}
export AWS_REGION=${AWS_REGION:-us-east-1}
export NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-"http://localhost:8000"}


echo "🚀 AWS Bedrock AI Gateway başlatılıyor..."
echo "   📦 Database: AWS RDS PostgreSQL @ bedrock-gateway-db.cobqqmqcs7xh.us-east-1.rds.amazonaws.com"
echo "   📦 Redis:    AWS ElastiCache  @ bedrock-gateway-redis.hmoplf.0001.use1.cache.amazonaws.com"
echo ""

# Kill existing processes
echo "🧹 Eski süreçler temizleniyor..."
kill -9 $(lsof -t -i:8000) 2>/dev/null || true
kill -9 $(lsof -t -i:3000) 2>/dev/null || true
sleep 1

# Start backend
echo "⚙️  Backend başlatılıyor (port 8000)..."
source "$VENV"
cd "$ROOT/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend
sleep 5

# Start frontend
echo "🌐 Frontend başlatılıyor (port 3000)..."
cd "$ROOT/frontend"
NEXT_PUBLIC_API_URL="http://localhost:8000" npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Sistem hazır!"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📖 API Docs:  http://localhost:8000/docs"
echo ""
echo "Durdurmak için: Ctrl+C veya 'kill $BACKEND_PID $FRONTEND_PID'"

# Wait for both
wait
