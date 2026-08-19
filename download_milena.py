import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Ensure root dir in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.auto_downloader import AutoModelDownloader

def print_banner():
    print("=" * 68)
    print("   🔥 Автоматический сборщик фото Милены Лисицыной (Лимит: 1 ГБ)")
    print("=" * 68)
    print()

def main():
    print_banner()

    target_dir = Path("./Milena_Lisitsyna_Photos").resolve()
    print(f"[INFO] Целевая папка для сохранения: {target_dir}")
    print(f"[INFO] Максимальный объём на диске: 1.0 ГБ (1024 МБ)")
    print()

    downloader = AutoModelDownloader(target_dir=str(target_dir), max_bytes=1024 * 1024 * 1024)

    def on_progress(data):
        status = data.get("status")
        if status == "searching":
            print("[1/2] Поиск всех фотосессий и альбомов Милены Лисицыной в сети...")
        elif status == "downloading":
            count = data.get("count", 0)
            size_mb = data.get("size_mb", 0)
            percent = data.get("percent", 0)
            speed = data.get("speed_kbps", 0)
            cur_file = data.get("current_file", "")
            sys.stdout.write(f"\r[Скачивание] Фото: {count:03d} | Занято: {size_mb:6.1f} MB / 1024 MB ({percent:4.1f}%) | {speed:5.1f} KB/s | {cur_file[:30]:30s}")
            sys.stdout.flush()
        elif status == "completed":
            print("\n")
            print("=" * 68)
            print(f"  [✓] УСПЕШНО ЗАВЕРШЕНО!")
            print(f"  Скачано новых фото: {data.get('count')} шт.")
            print(f"  Общий размер папки: {data.get('size_mb')} MB (строго до 1 ГБ)")
            print(f"  Папка с фото: {data.get('folder')}")
            print("=" * 68)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(downloader.run_auto_download(progress_callback=on_progress))
    except KeyboardInterrupt:
        print("\n[!] Загрузка остановлена пользователем.")
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
    finally:
        loop.close()

    print()
    print("Открытие папки с фотографиями...")
    try:
        if os.name == "nt":
            os.startfile(str(target_dir))
        else:
            subprocess.run(["xdg-open", str(target_dir)], check=False)
    except Exception:
        pass

if __name__ == "__main__":
    main()
