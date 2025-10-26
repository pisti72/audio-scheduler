@echo off
setlocal enabledelayedexpansion

REM Audio Scheduler - Automated Installation Script for Windows
REM This script will set up a virtual environment and install all dependencies

echo.
echo 🎵 Audio Scheduler - Automated Installation 🎵
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [ERROR] This script should not be run as administrator
    echo Please run as a regular user
    pause
    exit /b 1
)

echo [INFO] Starting installation process...
echo.

REM Step 1: Check Python installation
echo [INFO] Step 1/4: Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found ✓
echo.

REM Step 2: Check for Visual C++ Build Tools
echo [INFO] Step 2/4: Checking for Visual C++ Build Tools...
echo.
echo [WARNING] This application requires Visual C++ Build Tools for pygame compilation
echo.
echo If you encounter build errors, please install:
echo 1. Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
echo 2. Or Visual Studio Community with C++ workload
echo.
pause

REM Step 3: Create virtual environment
echo [INFO] Step 3/4: Setting up virtual environment...

if exist "venv" (
    echo [WARNING] Virtual environment already exists
    set /p "recreate=Do you want to recreate it? (y/N): "
    if /i "!recreate!"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo [INFO] Using existing virtual environment
        goto install_deps
    )
)

echo [INFO] Creating virtual environment...
python -m venv venv
if %errorLevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    echo Please ensure Python is properly installed with venv module
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created ✓
echo.

:install_deps
REM Step 4: Install Python dependencies
echo [INFO] Step 4/4: Installing Python dependencies...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Failed to install some dependencies
    echo.
    echo Common solutions:
    echo 1. Install Visual C++ Build Tools
    echo 2. Try: pip install --only-binary=all -r requirements.txt
    echo 3. For pygame issues, try: pip install pygame==2.6.1 --force-reinstall
    echo.
    pause
    exit /b 1
)
echo [SUCCESS] Python dependencies installed ✓
echo.

REM Initialize application
echo [INFO] Initializing application...

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "instance" mkdir instance

REM Initialize database if it doesn't exist
if not exist "schedules.db" (
    echo [INFO] Initializing database...
    start /b python app.py
    timeout /t 3 >nul
    taskkill /f /im python.exe >nul 2>&1
    echo [SUCCESS] Database initialized ✓
)

echo [SUCCESS] Application initialized ✓
echo.

REM Create run script
echo [INFO] Setting up run script...
if exist "run.bat" (
    echo [SUCCESS] Run script already exists ✓
    goto installation_complete
)

echo [INFO] Creating run script...
(
echo @echo off
echo REM Audio Scheduler - Run Script
echo.
echo cd /d "%%~dp0"
echo.
echo REM Check if virtual environment exists
echo if not exist "venv" ^(
echo     echo ❌ Virtual environment not found!
echo     echo Please run install.bat first
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Activate virtual environment
echo call venv\Scripts\activate.bat
echo.
echo REM Check if all dependencies are installed
echo python -c "import flask, pygame, sqlalchemy" >nul 2>&1
echo if %%errorLevel%% neq 0 ^(
echo     echo ❌ Dependencies not properly installed!
echo     echo Please run install.bat again
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo 🎵 Starting Audio Scheduler...
echo echo 📡 Server will be available at: http://localhost:5000
echo echo 🛑 Press Ctrl+C to stop the server
echo echo.
echo.
echo REM Run the application
echo python app.py
echo pause
) > run.bat

echo [SUCCESS] Run script created ✓
echo.

REM Installation complete
echo.
echo 🎉 Installation completed successfully! 🎉
echo.
echo 📋 Next steps:
echo   1. Run the application:  run.bat
echo   2. Open your browser:    http://localhost:5000
echo   3. Default credentials:  admin / admin
echo.
echo 📚 For more information, check the README.md file
echo.

REM Ask if user wants to start the application now
set /p "start_now=Do you want to start the application now? (y/N): "
if /i "!start_now!"=="y" (
    echo [INFO] Starting Audio Scheduler...
    call run.bat
) else (
    echo.
    echo You can start the application later by running: run.bat
    pause
)