@echo off
title NSFW Image Hunter & Downloader
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
python app_launcher.py --mode gui
if %errorlevel% neq 0 (
    python app_launcher.py --mode web
)
pause
