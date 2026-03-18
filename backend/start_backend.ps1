# Start Backend Server
Write-Host "Starting backend server..." -ForegroundColor Green
Set-Location "C:\Users\lala\Desktop\毕设\bishi\bishe\backend"

$env:PYTHONUNBUFFERED = "1"

# Start uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info