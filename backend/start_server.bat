@echo off
echo ========================================
echo Starting College English Assistant Backend
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONUNBUFFERED=1

echo Starting server on http://127.0.0.1:8001
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info

pause