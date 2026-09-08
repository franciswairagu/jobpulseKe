#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/ui/jobpulse-backend/jobpulse-backend"
FRONTEND_DIR="$SCRIPT_DIR/ui/jobpulse-unified-app2.0"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  echo "Done."
}

trap cleanup EXIT INT TERM

echo "=== JobPulse ==="
echo ""

# --- Backend ---
echo "[1/2] Starting backend (FastAPI on :8000)..."
if [ ! -d "$BACKEND_DIR" ]; then
  echo "ERROR: Backend directory not found at $BACKEND_DIR"
  exit 1
fi

cd "$BACKEND_DIR"

if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
  echo "  No virtualenv found. Installing dependencies..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt --quiet
else
  VENV_DIR="venv"
  [ -d ".venv" ] && VENV_DIR=".venv"
  source "$VENV_DIR/bin/activate"
fi

# Use SQLite by default if no DATABASE_URL is set
export DATABASE_URL="${DATABASE_URL:-sqlite:///./dev.db}"
export SECRET_KEY="${SECRET_KEY:-dev-secret-change-in-production}"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# --- Frontend ---
echo "[2/2] Starting frontend (React + Vite on :5173)..."
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "ERROR: Frontend directory not found at $FRONTEND_DIR"
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "  No node_modules found. Installing dependencies..."
  npm install --silent
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "Services running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

wait
