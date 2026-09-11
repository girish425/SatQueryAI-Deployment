@echo off
echo ===================================================
echo   SatQuery AI - Production Build and Launch
echo ===================================================

echo [1/3] Building Frontend React SPA...
cd frontend
call npm install
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo Frontend build failed!
    exit /b %ERRORLEVEL%
)
cd ..

echo [2/3] Installing Backend Dependencies...
cd backend
call .\venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..

echo [3/3] Starting Production Server on http://localhost:8000 ...
.\backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
