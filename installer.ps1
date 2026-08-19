# PowerShell Automated Setup for Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

try {
    $Host.UI.RawUI.WindowTitle = 'NSFW Image Hunter - Setup'
} catch {}

Clear-Host
Write-Host '=================================================================' -ForegroundColor Magenta
Write-Host '   NSFW Image Hunter and Downloader - Setup' -ForegroundColor Magenta
Write-Host '=================================================================' -ForegroundColor Magenta
Write-Host ''

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Get-WorkingPython {
    $candidates = @(
        'python',
        'py',
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310\python.exe'),
        'C:\Python312\python.exe',
        'C:\Python311\python.exe',
        'C:\Python310\python.exe'
    )
    foreach ($c in $candidates) {
        try {
            $out = & $c --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $out -match 'Python 3') {
                return $c
            }
        } catch {}
    }
    return $null
}

$pyCmd = Get-WorkingPython

if (-not $pyCmd) {
    Write-Host '[1/5] Python is not installed on this PC.' -ForegroundColor Yellow
    Write-Host '      Downloading official Python 3.11 for Windows...' -ForegroundColor Cyan
    
    $installerPath = Join-Path $env:TEMP 'python-3.11.9-amd64.exe'
    $pythonUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe'
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        $client = New-Object System.Net.WebClient
        $client.DownloadFile($pythonUrl, $installerPath)
        Write-Host '  -> Download completed.' -ForegroundColor Green
        
        Write-Host '[2/5] Installing Python 3.11 silently in background...' -ForegroundColor Cyan
        $argsList = '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1'
        Start-Process -FilePath $installerPath -ArgumentList $argsList -Wait
        
        Start-Sleep -Seconds 2
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        
        $localPy = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311'
        $localPyScripts = Join-Path $localPy 'Scripts'
        
        $env:Path = "$localPy;$localPyScripts;" + [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
        
        $pyCmd = Get-WorkingPython
        if (-not $pyCmd) {
            $candidatePy = Join-Path $localPy 'python.exe'
            if (Test-Path $candidatePy) {
                $pyCmd = $candidatePy
            }
        }
        Write-Host '  -> Python installed successfully.' -ForegroundColor Green
    } catch {
        Write-Host "  [!] Error downloading Python: $_" -ForegroundColor Red
        Write-Host '  Please install Python from https://www.python.org/downloads/' -ForegroundColor Yellow
        Pause
        exit 1
    }
} else {
    Write-Host "[+] Python found: $pyCmd" -ForegroundColor Green
}

Write-Host ''
Write-Host '[3/5] Installing required packages (PyQt6, FastAPI, Pillow, PyInstaller)...' -ForegroundColor Cyan
try {
    & $pyCmd -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $pyCmd -m pip install -r requirements.txt --quiet --disable-pip-version-check
    & $pyCmd -m pip install pyinstaller --quiet --disable-pip-version-check
    Write-Host '  -> Packages installed successfully.' -ForegroundColor Green
} catch {
    Write-Host "  [!] Note: $_" -ForegroundColor Yellow
}

Write-Host ''
Write-Host '[4/5] Building standalone EXE application...' -ForegroundColor Cyan
try {
    & $pyCmd build_exe.py
} catch {
    Write-Host "  [!] Build note: $_" -ForegroundColor Yellow
}

$exeDir = Join-Path $scriptDir 'dist\NSFW_Image_Hunter'
$exePath = Join-Path $exeDir 'NSFW_Image_Hunter.exe'

Write-Host ''
Write-Host '[5/5] Creating Desktop Shortcut...' -ForegroundColor Cyan
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [System.Environment]::GetFolderPath('Desktop')
    $Shortcut = $WshShell.CreateShortcut((Join-Path $DesktopPath 'NSFW Image Hunter.lnk'))
    
    if (Test-Path $exePath) {
        $Shortcut.TargetPath = $exePath
        $Shortcut.WorkingDirectory = $exeDir
    } else {
        $Shortcut.TargetPath = (Join-Path $scriptDir 'Start_App_Windows.bat')
        $Shortcut.WorkingDirectory = $scriptDir
    }
    $Shortcut.Description = 'NSFW Image Hunter and Downloader'
    $Shortcut.Save()
    Write-Host '  -> [OK] Desktop Shortcut created on your Desktop!' -ForegroundColor Green
} catch {
    Write-Host "  [!] Could not create shortcut: $_" -ForegroundColor Yellow
}

Write-Host ''
Write-Host '=================================================================' -ForegroundColor Green
Write-Host '   SUCCESS! Setup completed.' -ForegroundColor Green
Write-Host '=================================================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Starting application...' -ForegroundColor Cyan

if (Test-Path $exePath) {
    Start-Process -FilePath $exePath
} else {
    & $pyCmd app_launcher.py --mode gui
}
