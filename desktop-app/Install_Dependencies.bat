@echo off
title StreamHost - Install Dependencies
color 0E

echo.
echo  ========================================
echo     StreamHost - Dependency Installer
echo  ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

:: Create venv
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate and install
call venv\Scripts\activate.bat
echo [INFO] Installing packages...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo  ========================================
echo     Installation Complete!
echo  ========================================
echo.
echo You can now run StreamHost.bat or StreamHost_QuickStart.bat
echo.
pause
