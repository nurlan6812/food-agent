#!/bin/bash
# 백엔드와 프론트엔드 동시 실행

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting Korean Food Agent..."

# 백엔드 시작 (백그라운드)
echo "📦 Starting FastAPI backend on port 8000..."
cd "$SCRIPT_DIR"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 프론트엔드 시작 (백그라운드)
echo "🎨 Starting Next.js frontend on port 3000..."
cd "$SCRIPT_DIR/frontend/app"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# 종료 시 모든 프로세스 정리
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# 대기
wait
