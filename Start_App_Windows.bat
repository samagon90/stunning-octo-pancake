@echo off
chcp 65001 > nul
title NSFW Image Hunter & Downloader v1.0
echo ===================================================================
echo     🔥 NSFW Image Hunter & Downloader для Windows v1.0
echo ===================================================================
echo.

:: Check python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Python не найден на вашем компьютере!
    echo.
    echo Чтобы приложение работало:
    echo 1. Скачайте и установите Python с официального сайта: https://www.python.org/downloads/
    echo 2. При установке ОБЯЗАТЕЛЬНО отметьте галочку: [X] "Add Python to PATH"
    echo 3. После установки перезапустите этот файл.
    echo.
    pause
    exit /b
)

echo [1/2] Проверка необходимых библиотек...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Запуск приложения...
echo.
echo Открытие графического интерфейса...
python app_launcher.py --mode gui

if %errorlevel% neq 0 (
    echo [INFO] Графический интерфейс Qt не смог открыться, запуск веб-версии...
    start http://localhost:8000
    python app_launcher.py --mode web --host 127.0.0.1 --port 8000
)

pause
