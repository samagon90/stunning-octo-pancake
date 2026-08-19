@echo off
title NSFW Image Hunter Launcher
cd /d "%~dp0"
if exist "%~dp0dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe" (
    start "" "%~dp0dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe"
    exit /b
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
if %errorlevel% neq 0 (
    pause
)
