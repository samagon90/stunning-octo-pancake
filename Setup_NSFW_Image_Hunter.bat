@echo off
setlocal EnableDelayedExpansion
title NSFW Image Hunter - Setup & Installer
cd /d "%~dp0"

echo ===================================================================
echo   NSFW Image Hunter & Downloader - Automatic Setup
echo ===================================================================
echo.

:: 1. Check if Python is already available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    echo [+] Found Python in PATH
    goto :INSTALL_DEPS
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    echo [+] Found Python Launcher (py)
    goto :INSTALL_DEPS
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
    echo [+] Found Python 3.11 in LocalAppData
    goto :INSTALL_DEPS
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    echo [+] Found Python 3.12 in LocalAppData
    goto :INSTALL_DEPS
)

:: 2. Download official Python 3.11 for Windows
echo [1/4] Python not found. Downloading official Python 3.11 installer...
if exist "%SystemRoot%\System32\curl.exe" (
    "%SystemRoot%\System32\curl.exe" -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
) else (
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', '$env:TEMP\python_installer.exe')"
)

if not exist "%TEMP%\python_installer.exe" (
    echo.
    echo [ERROR] Failed to download Python.
    echo Please install Python manually from https://www.python.org/downloads/
    echo Make sure to check the box "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [2/4] Installing Python 3.11 silently in background...
start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1
del /f /q "%TEMP%\python_installer.exe" >nul 2>&1

:: Locate installed python
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
) else (
    set "PY_CMD=python"
)

:INSTALL_DEPS
echo.
echo [3/4] Installing application dependencies...
"%PY_CMD%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%PY_CMD%" -m pip install -r requirements.txt --quiet --disable-pip-version-check
"%PY_CMD%" -m pip install pyinstaller --quiet --disable-pip-version-check

echo.
echo [4/4] Building standalone Windows .EXE application...
"%PY_CMD%" build_exe.py

:: Create Desktop Shortcut via VBScript
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'NSFW Image Hunter.lnk')); $s.TargetPath = (Join-Path '%~dp0' 'dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe'); $s.WorkingDirectory = (Join-Path '%~dp0' 'dist\NSFW_Image_Hunter'); $s.Description = 'NSFW Image Hunter & Downloader'; $s.Save()" >nul 2>&1

echo.
echo ===================================================================
echo   [SUCCESS] Setup completed!
echo   Application EXE is ready at: dist\NSFW_Image_Hunter\
echo ===================================================================
echo.
echo Launching application...
if exist "%~dp0dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe" (
    start "" "%~dp0dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe"
) else (
    "%PY_CMD%" app_launcher.py --mode gui
)

timeout /t 5 >nul
