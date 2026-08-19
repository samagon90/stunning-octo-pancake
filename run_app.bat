@echo off
title NSFW Image Hunter & Downloader
python app_launcher.py --mode gui
if %errorlevel% neq 0 (
    python app_launcher.py --mode web
)
pause
