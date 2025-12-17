@echo off
title StreamHost Desktop
color 0A

:: Quick start - assumes dependencies are already installed
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python streamhost_desktop.py
    deactivate
) else (
    echo First time setup required. Running full installer...
    call StreamHost.bat
)
