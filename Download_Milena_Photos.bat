@echo off
title Auto Download - Milena Lisitsyna Photos (1 GB Limit)
cd /d "%~dp0"

:: Check python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python download_milena.py
    pause
    exit /b
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    py download_milena.py
    pause
    exit /b
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" download_milena.py
    pause
    exit /b
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" download_milena.py
    pause
    exit /b
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
python download_milena.py
pause
