@echo off
chcp 65001 > nul
title NSFW Image Hunter & Downloader
echo ========================================================
echo   NSFW Image Hunter & Downloader для Windows
echo ========================================================
echo.

:: Check python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден! Установите Python 3.10+ с сайта https://python.org
    echo Убедитесь, что поставили галочку "Add Python to PATH" при установке.
    pause
    exit /b
)

:: Install requirements if needed
echo [INFO] Проверка и установка зависимостей...
python -m pip install -r requirements.txt

echo.
echo [1] Запустить Desktop GUI (PyQt6)
echo [2] Запустить Web-интерфейс в браузере (FastAPI + Web UI)
echo.
set /p choice="Выберите режим запуска (1 или 2, по умолчанию 1): "

if "%choice%"=="2" (
    echo [INFO] Запуск веб-интерфейса...
    start http://localhost:8000
    python app_launcher.py --mode web --host 127.0.0.1 --port 8000
) else (
    echo [INFO] Запуск Desktop GUI...
    python app_gui_qt.py
)

pause
