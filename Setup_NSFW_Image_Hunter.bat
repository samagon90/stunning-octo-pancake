@echo off
title NSFW Image Hunter - Setup & Auto-Installer
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation encountered an issue.
    pause
)
