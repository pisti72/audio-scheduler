@echo off
REM Audio Scheduler - Run Script

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if all dependencies are installed
python -c "import flask, pygame, sqlalchemy" >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Dependencies not properly installed!
    echo Please run install.bat again
    pause
    exit /b 1
)

echo 🎵 Starting Audio Scheduler...
echo 📡 Server will be available at: http://localhost:5000
echo 🛑 Press Ctrl+C to stop the server
echo.

REM Run the application
python app.py
pause