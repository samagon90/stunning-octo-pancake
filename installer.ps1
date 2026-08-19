# PowerShell Automated Installer for NSFW Image Hunter & Downloader
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=================================================================" -ForegroundColor Magenta
Write-Host "   🔥 NSFW Image Hunter & Downloader - Автоматический установщик" -ForegroundColor Magenta
Write-Host "=================================================================" -ForegroundColor Magenta
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Function to check if python is working
function Test-Python {
    try {
        $ver = & python --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
            return $true
        }
    } catch {}
    return $false
}

# 1. Check Python
$hasPython = Test-Python

if (-not $hasPython) {
    # Check default AppData locations
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310",
        "C:\Python312",
        "C:\Python311",
        "C:\Python310"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path "$p\python.exe") {
            $env:Path = "$p;$p\Scripts;" + $env:Path
            $hasPython = Test-Python
            if ($hasPython) { break }
        }
    }
}

if (-not $hasPython) {
    Write-Host "[1/5] Python не обнаружен на вашем ПК." -ForegroundColor Yellow
    Write-Host "      Начинаем автоматическую загрузку официального Python 3.11 с python.org..." -ForegroundColor Cyan
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installerPath = "$env:TEMP\python-3.11.9-amd64.exe"
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        $webclient = New-Object System.Net.WebClient
        $webclient.DownloadFile($pythonUrl, $installerPath)
        Write-Host "  -> Загрузка Python завершена." -ForegroundColor Green
        
        Write-Host "[2/5] Автоматическая установка Python 3.11 в систему (тихий режим)..." -ForegroundColor Cyan
        $process = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1" -Wait -PassThru
        
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        # Refresh environment variables in current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $localPy = "$env:LOCALAPPDATA\Programs\Python\Python311"
        if (Test-Path "$localPy\python.exe") {
            $env:Path = "$localPy;$localPy\Scripts;" + $env:Path
        }
        
        Write-Host "  -> Python успешно установлен!" -ForegroundColor Green
    } catch {
        Write-Host "  [!] Не удалось автоматически скачать Python: $_" -ForegroundColor Red
        Write-Host "  Пожалуйста, установите Python с сайта https://www.python.org/downloads/ (отметив галочку 'Add Python to PATH')" -ForegroundColor Yellow
        Pause
        exit 1
    }
} else {
    Write-Host "[✓] Найден установленный Python." -ForegroundColor Green
}

# 2. Install Dependencies
Write-Host ""
Write-Host "[3/5] Установка библиотек приложения (PyQt6, FastAPI, Pillow, PyInstaller)..." -ForegroundColor Cyan
try {
    & python -m pip install --upgrade pip --quiet --disable-pip-version-check
    & python -m pip install -r requirements.txt --quiet --disable-pip-version-check
    & python -m pip install pyinstaller --quiet --disable-pip-version-check
    Write-Host "  -> Все библиотеки успешно установлены." -ForegroundColor Green
} catch {
    Write-Host "  [!] Ошибка при установке библиотек. Пробуем продолжить..." -ForegroundColor Yellow
}

# 3. Build EXE
Write-Host ""
Write-Host "[4/5] Сборка самостоятельного .EXE файла приложения..." -ForegroundColor Cyan
& python build_exe.py

$exePath = "$scriptDir\dist\NSFW_Image_Hunter\NSFW_Image_Hunter.exe"

# 4. Create Desktop Shortcut
Write-Host ""
Write-Host "[5/5] Создание ярлыка на Рабочем столе..." -ForegroundColor Cyan
try {
    $WshShell = New-Object -comObject WScript.Shell
    $DesktopPath = [System.Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\NSFW Image Hunter.lnk")
    
    if (Test-Path $exePath) {
        $Shortcut.TargetPath = $exePath
        $Shortcut.WorkingDirectory = "$scriptDir\dist\NSFW_Image_Hunter"
    } else {
        $Shortcut.TargetPath = "$scriptDir\Start_App_Windows.bat"
        $Shortcut.WorkingDirectory = "$scriptDir"
    }
    
    $Shortcut.Description = "NSFW Image Hunter & Downloader"
    $Shortcut.Save()
    Write-Host "  -> [✓] Ярлык 'NSFW Image Hunter' создан на Рабочем столе!" -ForegroundColor Green
} catch {
    Write-Host "  [!] Не удалось создать ярлык: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "   🎉 УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Программа готова к использованию."
Write-Host "Запуск приложения..." -ForegroundColor Cyan

if (Test-Path $exePath) {
    Start-Process -FilePath $exePath
} else {
    & python app_launcher.py --mode gui
}
