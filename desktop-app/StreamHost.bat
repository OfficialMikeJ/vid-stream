@echo off
title StreamHost Desktop Application
color 0A

echo.
echo  ========================================
echo     StreamHost Desktop Application
echo     Version: 2025.12.17
echo  ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Check if virtual environment exists, create if not
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

:: Install/upgrade dependencies
echo [INFO] Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: Run the application
echo [INFO] Starting StreamHost Desktop...
echo.
echo  ========================================
echo     Launching Application...
echo  ========================================
echo.

python streamhost_desktop.py

:: Deactivate when done
deactivate

echo.
echo [INFO] Application closed.
pause
