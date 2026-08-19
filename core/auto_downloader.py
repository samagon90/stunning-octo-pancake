import os
import sys
import re
import json
import time
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

MAX_STORAGE_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GB

class AutoModelDownloader:
    def __init__(self, target_dir: str = "./Milena_Lisitsyna_Photos", max_bytes: int = MAX_STORAGE_LIMIT_BYTES):
        self.target_dir = Path(target_dir).resolve()
        self.max_bytes = max_bytes
        self.downloaded_bytes = 0
        self.downloaded_count = 0
        self.is_running = False
        self.should_stop = False

    def get_current_folder_size(self) -> int:
        total = 0
        if self.target_dir.exists():
            for f in self.target_dir.rglob("*.*"):
                if f.is_file():
                    total += f.stat().st_size
        return total

    def run_gallery_dl_download(self, urls: List[str], progress_callback: Optional[Callable] = None) -> int:
        """Download using gallery-dl engine with strict size limit."""
        self.target_dir.mkdir(parents=True, exist_ok=True)
        initial_size = self.get_current_folder_size()
        self.downloaded_bytes = initial_size
        
        for url in urls:
            if self.should_stop or self.downloaded_bytes >= self.max_bytes:
                break
            
            if progress_callback:
                progress_callback({
                    "status": "downloading",
                    "message": f"Загрузка из {url}...",
                    "count": self.downloaded_count,
                    "size_mb": round(self.downloaded_bytes / (1024 * 1024), 1)
                })

            cmd = [
                sys.executable, "-m", "gallery_dl",
                "--dest", str(self.target_dir),
                "--directory", "",
                "--filename", "Milena_Lisitsyna_{id}_{num}.{extension}",
                "--no-mtime",
                "--retries", "3",
                "--timeout", "30",
                "--write-metadata",
                url
            ]

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )

                for line in proc.stdout:
                    clean_line = line.strip()
                    if "#" in clean_line or "." in clean_line:
                        # Check disk size every file
                        cur_size = self.get_current_folder_size()
                        self.downloaded_bytes = cur_size
                        self.downloaded_count = len([f for f in self.target_dir.glob("*.*") if not f.name.endswith(".json")])
                        
                        if cur_size >= self.max_bytes:
                            self.should_stop = True
                            proc.terminate()
                            break

                        if progress_callback:
                            mb = round(cur_size / (1024 * 1024), 1)
                            progress_callback({
                                "status": "downloading",
                                "count": self.downloaded_count,
                                "size_mb": mb,
                                "max_mb": 1024,
                                "percent": min(100.0, round((cur_size / self.max_bytes) * 100, 1)),
                                "current_file": clean_line[:40]
                            })

                proc.wait()
            except Exception as e:
                logger.debug(f"Gallery-dl batch error: {e}")

        return self.downloaded_count

    async def run_auto_download(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Auto download Milena Lisitsyna photosets from all sources with 1GB cap."""
        self.is_running = True
        self.should_stop = False
        self.target_dir.mkdir(parents=True, exist_ok=True)

        target_sources = [
            "https://coomer.su/onlyfans/user/milenalisitsyna",
            "https://coomer.su/posts?q=milena+lisitsyna",
            "https://coomer.su/posts?q=lisitsyna",
            "https://www.erome.com/search?q=milena+lisitsyna",
            "https://www.erome.com/search?q=milena+fox",
            "https://realbooru.com/index.php?page=post&s=list&tags=milena_lisitsyna",
            "https://rule34.xxx/index.php?page=post&s=list&tags=milena_lisitsyna"
        ]

        # Run gallery-dl extraction in background thread
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.run_gallery_dl_download, target_sources, progress_callback)

        total_size = self.get_current_folder_size()
        total_mb = round(total_size / (1024 * 1024), 1)
        count = len([f for f in self.target_dir.glob("*.*") if not f.name.endswith(".json") and not f.name.endswith(".tmp")])

        res = {
            "status": "completed",
            "downloaded_count": count,
            "total_size_mb": total_mb,
            "folder": str(self.target_dir),
            "limit_respected": total_size <= self.max_bytes
        }

        if progress_callback:
            progress_callback({
                "status": "completed",
                "message": f"Загрузка завершена! Сохранено {count} фото ({total_mb} MB из 1024 MB).",
                "folder": str(self.target_dir),
                "size_mb": total_mb,
                "count": count
            })

        return res
