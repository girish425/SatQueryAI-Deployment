@echo off
title SatQuery AI - Public HTTPS Tunnel
echo ===================================================
echo     SatQuery AI - Instant Public Tunnel Deploy
echo ===================================================
echo.
echo Checking local server on port 8000...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Starting backend & frontend unified production server on port 8000...
    start /B python backend/run_backend.py
    timeout /t 3 /nobreak >nul
)

echo [OK] Unified server is active on http://localhost:8000
echo.
echo Launching high-speed Cloudflare Public HTTPS Tunnel...
echo.
.\cloudflared.exe tunnel --url http://localhost:8000
