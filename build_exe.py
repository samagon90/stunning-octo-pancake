import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    print("=" * 65)
    print("   NSFW Image Hunter & Downloader - Windows EXE Builder")
    print("=" * 65)
    print()

def check_and_install_dependencies():
    print("[1/3] Проверка и установка зависимостей...")
    requirements = [
        "pyinstaller>=6.4.0",
        "PyQt6>=6.6.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.28.0",
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "pydantic>=2.6.0",
        "Pillow>=10.2.0"
    ]
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + requirements)
        print("  -> Зависимости успешно установлены.")
    except Exception as e:
        print(f"  [!] Ошибка при установке зависимостей: {e}")
        print("  Пробуем продолжить сборку...")

def build_executable():
    print()
    print("[2/3] Запуск сборки EXE через PyInstaller...")
    
    # Import PyInstaller directly inside Python to avoid PATH issues
    try:
        import PyInstaller.__main__
    except ImportError:
        print("  [!] PyInstaller не найден, устанавливаем...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        import PyInstaller.__main__

    project_root = Path(__file__).resolve().parent
    core_dir = project_root / "core"
    static_dir = project_root / "static"
    main_script = project_root / "app_gui_qt.py"

    # Data separator for Windows is ';'
    sep = ";" if os.name == "nt" or sys.platform.startswith("win") else ":"

    add_data_core = f"{core_dir}{sep}core"
    add_data_static = f"{static_dir}{sep}static"

    pyinstaller_args = [
        str(main_script),
        "--name=NSFW_Image_Hunter",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--add-data={add_data_core}",
        f"--add-data={add_data_static}",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=aiohttp",
        "--hidden-import=fastapi",
        "--hidden-import=uvicorn",
        "--hidden-import=pydantic",
        "--hidden-import=PIL",
        "--hidden-import=core",
        "--hidden-import=core.models",
        "--hidden-import=core.downloader",
        "--hidden-import=core.tag_suggest",
        "--hidden-import=core.settings",
        "--hidden-import=core.providers",
        "--hidden-import=core.providers.manager",
        "--hidden-import=ddgs",
        "--hidden-import=duckduckgo_search",
        "--hidden-import=primp",
        "--hidden-import=httpx",
        "--hidden-import=core.translit",
        "--hidden-import=core.providers.web_ddgs",
        "--hidden-import=core.providers.yandex",
        "--hidden-import=core.providers.bing",
        "--hidden-import=core.providers.google",
        "--hidden-import=core.providers.duckduckgo_images",
        "--hidden-import=core.providers.reddit",
        "--hidden-import=core.providers.rule34",
        "--hidden-import=core.providers.gelbooru",
        "--hidden-import=core.providers.danbooru",
        "--hidden-import=core.providers.yandere",
        "--hidden-import=core.providers.konachan",
        "--hidden-import=core.providers.realbooru",
        "--hidden-import=core.providers.safebooru",
        "--hidden-import=core.providers.waifu_im",
        "--hidden-import=core.providers.mock_provider"
    ]

    print("  Выполняется сборка...")
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("  -> Сборка PyInstaller завершена успешно.")
    except Exception as e:
        print(f"  [ERROR] Ошибка сборки: {e}")
        return False

    return True

def finalize_release():
    print()
    print("[3/3] Подготовка готовой папки приложения...")
    project_root = Path(__file__).resolve().parent
    dist_dir = project_root / "dist" / "NSFW_Image_Hunter"
    
    if not dist_dir.exists():
        print("  [!] Папка dist/NSFW_Image_Hunter не найдена.")
        return

    # Copy README and runner
    shutil.copy(project_root / "README.md", dist_dir / "README.md")
    
    # Create simple direct launcher bat inside dist
    with open(dist_dir / "Запустить_NSFW_Hunter.bat", "w", encoding="utf-8") as f:
        f.write('@start "" "%~dp0NSFW_Image_Hunter.exe"\n')

    print()
    print("=" * 65)
    print("   [УСПЕХ] Сборка полностью завершена!")
    print(f"   Готовая программа находится в папке:")
    print(f"   -> {dist_dir}")
    print()
    print("   Исполняемый файл:")
    print(f"   -> {dist_dir / 'NSFW_Image_Hunter.exe'}")
    print("=" * 65)

def main():
    print_banner()
    check_and_install_dependencies()
    success = build_executable()
    if success:
        finalize_release()
    else:
        print("[!] Сборка не удалась. Проверьте сообщения об ошибках выше.")

if __name__ == "__main__":
    main()
