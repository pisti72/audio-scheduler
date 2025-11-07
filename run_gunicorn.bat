@echo off
REM Audio Scheduler - Production Run Script with Gunicorn for Windows

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run install.bat first.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if gunicorn is installed
python -c "import gunicorn" 2>nul
if errorlevel 1 (
    echo Gunicorn not installed. Installing...
    pip install gunicorn>=21.0.0
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set environment variables
set FLASK_ENV=production
set PYTHONUNBUFFERED=1

echo Starting Audio Scheduler with Gunicorn...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run with Gunicorn
REM -w 1: Use only 1 worker (CRITICAL: prevents duplicate schedulers!)
REM -b 0.0.0.0:5000: Bind to all interfaces on port 5000
REM --timeout 120: Allow 2 minutes for long-running requests
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 120 --log-level info --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --capture-output wsgi:app

pause
