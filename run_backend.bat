@echo off
echo ========================================================
echo Starting CrisisGuard Backend (FastAPI on http://localhost:8000)...
echo ========================================================
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
