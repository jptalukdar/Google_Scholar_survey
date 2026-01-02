@echo off
echo 🚀 Starting FastAPI Server on port 8000...
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
pause
