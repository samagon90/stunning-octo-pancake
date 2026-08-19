@echo off
chcp 65001 > nul
title Сборка EXE - NSFW Image Hunter
echo ========================================================
echo   Сборка самостоятельного .EXE для Windows
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден!
    pause
    exit /b
)

echo [INFO] Установка зависимостей сборки...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo [INFO] Запуск PyInstaller для сборки standalone GUI .exe...
pyinstaller --noconfirm --onedir --windowed ^
    --name "NSFW_Image_Hunter" ^
    --add-data "core;core" ^
    --add-data "static;static" ^
    --hidden-import "PyQt6" ^
    --hidden-import "aiohttp" ^
    --hidden-import "fastapi" ^
    --hidden-import "uvicorn" ^
    app_gui_qt.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   СБОРКА УСПЕШНО ЗАВЕРШЕНА!
    echo   Готовая программа находится в папке: dist\NSFW_Image_Hunter\
    echo   Файл запуска: dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe
    echo ========================================================
) else (
    echo [ERROR] Ошибка сборки. Проверьте вывод выше.
)

pause
