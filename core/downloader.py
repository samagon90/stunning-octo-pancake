import os
import re
import json
import time
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

def sanitize_filename(name: str, max_length: int = 120) -> str:
    """Sanitize string to be valid Windows filename."""
    # Replace illegal characters: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name)
    cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned or "image"

class DownloadManager:
    def __init__(self):
        self.active_tasks: Dict[str, Any] = {}
        self.is_running = False
        self.should_cancel = False
        self.current_stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "current_file": "",
            "progress_percent": 0.0,
            "downloaded_bytes": 0,
            "speed_kbps": 0.0,
            "errors": [],
            "status": "idle"  # idle, downloading, completed, cancelled, error
        }

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.current_stats)

    def cancel(self):
        self.should_cancel = True
        self.current_stats["status"] = "cancelled"

    def format_filename(self, post: Dict[str, Any], pattern: str = "{source}_{id}_{tags}") -> str:
        source = post.get("source", "image")
        post_id = str(post.get("id", "0"))
        ext = post.get("file_ext", "jpg") or "jpg"
        
        tags = post.get("tags", [])
        if isinstance(tags, list):
            tags_str = "_".join(tags[:5])
        else:
            tags_str = str(tags)
        
        rating = post.get("rating", "nsfw")

        name = pattern.replace("{source}", source)
        name = name.replace("{id}", post_id)
        name = name.replace("{tags}", tags_str)
        name = name.replace("{rating}", rating)
        
        name = sanitize_filename(name)
        return f"{name}.{ext}"

    async def download_posts(
        self,
        posts: List[Dict[str, Any]],
        destination_dir: str = "./downloads",
        naming_pattern: str = "{source}_{id}_{tags}",
        create_subfolders: bool = False,
        subfolder_name: str = "",
        skip_existing: bool = True,
        save_metadata: bool = True,
        threads: int = 4,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        
        self.is_running = True
        self.should_cancel = False
        
        # Prepare target directory
        target_dir = Path(destination_dir)
        if create_subfolders and subfolder_name:
            safe_sub = sanitize_filename(subfolder_name, 50)
            target_dir = target_dir / safe_sub
        
        target_dir.mkdir(parents=True, exist_ok=True)

        total = len(posts)
        self.current_stats = {
            "total": total,
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "current_file": "",
            "progress_percent": 0.0,
            "downloaded_bytes": 0,
            "speed_kbps": 0.0,
            "errors": [],
            "status": "downloading"
        }

        semaphore = asyncio.Semaphore(max(1, min(threads, 10)))
        start_time = time.time()
        downloaded_bytes_session = 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 NSFWDownloader/1.0"
        }

        async def download_one(post: Dict[str, Any], session: aiohttp.ClientSession):
            nonlocal downloaded_bytes_session
            if self.should_cancel:
                return

            async with semaphore:
                if self.should_cancel:
                    return

                filename = self.format_filename(post, naming_pattern)
                filepath = target_dir / filename
                file_url = post.get("file_url") or post.get("sample_url")

                self.current_stats["current_file"] = filename

                if skip_existing and filepath.exists() and filepath.stat().st_size > 0:
                    self.current_stats["skipped"] += 1
                    self._update_progress(progress_callback, start_time, downloaded_bytes_session)
                    return

                if not file_url:
                    self.current_stats["failed"] += 1
                    self.current_stats["errors"].append(f"No URL for post {post.get('id')}")
                    self._update_progress(progress_callback, start_time, downloaded_bytes_session)
                    return

                try:
                    async with session.get(file_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(filepath, "wb") as f:
                                f.write(content)
                            
                            file_size = len(content)
                            downloaded_bytes_session += file_size
                            self.current_stats["downloaded_bytes"] += file_size
                            self.current_stats["completed"] += 1

                            if save_metadata:
                                meta_path = target_dir / f"{filepath.stem}_info.json"
                                with open(meta_path, "w", encoding="utf-8") as mf:
                                    json.dump(post, mf, ensure_ascii=False, indent=2)
                        else:
                            self.current_stats["failed"] += 1
                            self.current_stats["errors"].append(f"HTTP {response.status} for {filename}")
                except Exception as e:
                    self.current_stats["failed"] += 1
                    self.current_stats["errors"].append(f"Error downloading {filename}: {str(e)}")

                self._update_progress(progress_callback, start_time, downloaded_bytes_session)

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                tasks = [download_one(p, session) for p in posts]
                await asyncio.gather(*tasks)
        finally:
            self.is_running = False
            if self.should_cancel:
                self.current_stats["status"] = "cancelled"
            else:
                self.current_stats["status"] = "completed"
            self.current_stats["progress_percent"] = 100.0 if total > 0 else 0.0

        return self.get_stats()

    def _update_progress(self, callback: Optional[Callable], start_time: float, bytes_count: int):
        total = self.current_stats["total"]
        done = self.current_stats["completed"] + self.current_stats["skipped"] + self.current_stats["failed"]
        self.current_stats["progress_percent"] = round((done / total * 100.0) if total > 0 else 0.0, 1)
        
        elapsed = max(0.1, time.time() - start_time)
        self.current_stats["speed_kbps"] = round((bytes_count / 1024) / elapsed, 1)

        if callback:
            try:
                callback(self.get_stats())
            except Exception:
                pass
