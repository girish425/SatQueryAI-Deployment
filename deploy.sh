#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  SatQuery AI - Production Build and Launch"
echo "==================================================="

echo "[1/3] Building Frontend React SPA..."
cd frontend
npm install
npm run build
cd ..

echo "[2/3] Installing Backend Dependencies..."
cd backend
python3 -m pip install -r requirements.txt
cd ..

echo "[3/3] Starting Production Server on http://0.0.0.0:${PORT:-8000} ..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
