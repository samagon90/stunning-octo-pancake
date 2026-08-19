# Auto-installer and Environment Setup for Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "NSFW Image Hunter - Автоматическая установка"

Clear-Host
Write-Host "=================================================================" -ForegroundColor Magenta
Write-Host "   NSFW Image Hunter and Downloader - Автоматическая установка" -ForegroundColor Magenta
Write-Host "=================================================================" -ForegroundColor Magenta
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Function to test if Python executable works
function Get-WorkingPython {
    $pythonCandidates = @(
        "python",
        "py",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "$scriptDir\python_runtime\python.exe"
    )

    foreach ($cmd in $pythonCandidates) {
        try {
            $ver = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
                return $cmd
            }
        } catch {}
    }
    return $null
}

# 1. Check Python
$pyCmd = Get-WorkingPython

if (-not $pyCmd) {
    Write-Host "[1/5] Python не обнаружен на вашем ПК." -ForegroundColor Yellow
    Write-Host "      Загружаем официальный Python 3.11 для Windows..." -ForegroundColor Cyan
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installerPath = "$env:TEMP\python-3.11.9-amd64.exe"
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        $webclient = New-Object System.Net.WebClient
        $webclient.DownloadFile($pythonUrl, $installerPath)
        Write-Host "  -> Загрузка завершена." -ForegroundColor Green
        
        Write-Host "[2/5] Автоматическая тихая установка Python..." -ForegroundColor Cyan
        $proc = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1" -Wait -PassThru
        
        Start-Sleep -Seconds 2
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $localPy = "$env:LOCALAPPDATA\Programs\Python\Python311"
        if (Test-Path "$localPy\python.exe") {
            $env:Path = "$localPy;$localPy\Scripts;" + $env:Path
        }

        $pyCmd = Get-WorkingPython
        if ($pyCmd) {
            Write-Host "  -> Python успешно установлен в систему!" -ForegroundColor Green
        } else {
            $pyCmd = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        }
    } catch {
        Write-Host "  [!] Ошибка при автоматической загрузке: $_" -ForegroundColor Red
        Write-Host "  Пожалуйста, установите Python с сайта https://www.python.org/downloads/ (отметив галочку 'Add Python to PATH')" -ForegroundColor Yellow
        Pause
        exit 1
    }
} else {
    Write-Host "[✓] Найден Python ($pyCmd)" -ForegroundColor Green
}

# 2. Install Dependencies
Write-Host ""
Write-Host "[3/5] Установка необходимых библиотек (PyQt6, FastAPI, Pillow, PyInstaller)..." -ForegroundColor Cyan
try {
    & $pyCmd -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $pyCmd -m pip install -r requirements.txt --quiet --disable-pip-version-check
    & $pyCmd -m pip install pyinstaller --quiet --disable-pip-version-check
    Write-Host "  -> Библиотеки успешно установлены." -ForegroundColor Green
} catch {
    Write-Host "  [!] Предупреждение при установке pip: $_" -ForegroundColor Yellow
}

# 3. Build EXE
Write-Host ""
Write-Host "[4/5] Сборка исполняемого файла .EXE..." -ForegroundColor Cyan
try {
    & $pyCmd build_exe.py
} catch {
    Write-Host "  [!] Ошибка вызова build_exe.py: $_" -ForegroundColor Yellow
}

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
        $Shortcut.TargetPath = "$scriptDir\Setup_NSFW_Image_Hunter.bat"
        $Shortcut.WorkingDirectory = "$scriptDir"
    }
    
    $Shortcut.Description = "NSFW Image Hunter and Downloader"
    $Shortcut.Save()
    Write-Host "  -> [✓] Ярлык создан на Рабочем столе!" -ForegroundColor Green
} catch {
    Write-Host "  [!] Не удалось создать ярлык: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "   УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Запуск программы..." -ForegroundColor Cyan

if (Test-Path $exePath) {
    Start-Process -FilePath $exePath
} else {
    & $pyCmd app_launcher.py --mode gui
}
