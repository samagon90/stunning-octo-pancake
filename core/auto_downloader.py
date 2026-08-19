import os
import re
import json
import time
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from core.models import Post
from core.providers.adult_meta import AdultMetaSearchProvider
from core.providers.direct_search import search_yandex_touch, search_google_gbv
from core.providers.coomer import CoomerModelProvider
from core.providers.erome import EroMeProvider
from core.downloader import get_referer_for_url, sanitize_filename

logger = logging.getLogger(__name__)

MAX_STORAGE_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GB

class AutoModelDownloader:
    def __init__(self, target_dir: str = "./Milena_Lisitsyna_Photos", max_bytes: int = MAX_STORAGE_LIMIT_BYTES):
        self.target_dir = Path(target_dir)
        self.max_bytes = max_bytes
        self.downloaded_bytes = 0
        self.downloaded_count = 0
        self.is_running = False
        self.should_stop = False

    def get_current_folder_size(self) -> int:
        total = 0
        if self.target_dir.exists():
            for f in self.target_dir.glob("*.*"):
                if f.is_file():
                    total += f.stat().st_size
        return total

    async def gather_all_candidate_photos(self, progress_callback: Optional[Callable] = None) -> List[Post]:
        search_queries = [
            "Милена Лисицына",
            "Milena Lisitsyna",
            "Milena Fox",
            "Милена Лисицына эротика",
            "Милена Лисицына фотосет",
            "Milena Fox photoshoot",
            "Milena Lisitsyna onlyfans"
        ]

        provider = AdultMetaSearchProvider()
        all_posts: List[Post] = []
        seen_urls = set()

        if progress_callback:
            progress_callback({"status": "searching", "message": "Поиск фотосетов Милены Лисицыной во всех базах..."})

        tasks = []
        for q in search_queries:
            for page in range(1, 4):
                tasks.append(provider.search(q, page=page, limit=40))

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for g in gathered:
            if isinstance(g, list):
                for p in g:
                    if p.file_url and p.file_url not in seen_urls:
                        seen_urls.add(p.file_url)
                        all_posts.append(p)

        logger.info(f"Total candidate photos gathered: {len(all_posts)}")
        return all_posts

    async def run_auto_download(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        self.is_running = True
        self.should_stop = False
        self.target_dir.mkdir(parents=True, exist_ok=True)

        existing_bytes = self.get_current_folder_size()
        self.downloaded_bytes = existing_bytes

        posts = await self.gather_all_candidate_photos(progress_callback)
        if not posts:
            msg = "Не удалось найти фото. Проверьте интернет-соединение."
            if progress_callback:
                progress_callback({"status": "error", "message": msg})
            return {"status": "error", "message": msg}

        if progress_callback:
            progress_callback({
                "status": "downloading",
                "message": f"Найдено {len(posts)} фото. Скачивание (лимит 1 GB)...",
                "count": 0,
                "size_mb": round(self.downloaded_bytes / (1024*1024), 1),
                "total_candidates": len(posts)
            })

        semaphore = asyncio.Semaphore(6)
        connector = aiohttp.TCPConnector(ssl=False, limit=20)
        start_time = time.time()

        async def download_single(idx: int, post: Post, session: aiohttp.ClientSession):
            if self.should_stop or self.downloaded_bytes >= self.max_bytes:
                return

            async with semaphore:
                if self.should_stop or self.downloaded_bytes >= self.max_bytes:
                    return

                ext = post.file_ext or "jpg"
                if len(ext) > 4:
                    ext = "jpg"
                filename = f"Milena_Lisitsyna_{idx+1:03d}_{post.id}.{ext}"
                filepath = self.target_dir / filename

                if filepath.exists() and filepath.stat().st_size > 1024:
                    return

                url = post.file_url or post.sample_url
                if not url:
                    return

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "Referer": get_referer_for_url(url),
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                }

                for attempt in range(2):
                    if self.should_stop or self.downloaded_bytes >= self.max_bytes:
                        break

                    try:
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                file_size = len(data)
                                
                                if file_size > 1024 and (self.downloaded_bytes + file_size <= self.max_bytes):
                                    with open(filepath, "wb") as f:
                                        f.write(data)
                                    
                                    self.downloaded_bytes += file_size
                                    self.downloaded_count += 1

                                    if progress_callback:
                                        mb = round(self.downloaded_bytes / (1024 * 1024), 1)
                                        speed = round((self.downloaded_bytes - existing_bytes) / 1024 / max(0.1, time.time() - start_time), 1)
                                        progress_callback({
                                            "status": "downloading",
                                            "count": self.downloaded_count,
                                            "size_mb": mb,
                                            "max_mb": 1024,
                                            "speed_kbps": speed,
                                            "current_file": filename,
                                            "percent": min(100.0, round((self.downloaded_bytes / self.max_bytes) * 100, 1))
                                        })
                                    break
                    except Exception:
                        pass

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                tasks = [download_single(i, p, session) for i, p in enumerate(posts)]
                await asyncio.gather(*tasks)
        finally:
            self.is_running = False

        total_mb = round(self.downloaded_bytes / (1024 * 1024), 1)
        res = {
            "status": "completed",
            "downloaded_count": self.downloaded_count,
            "total_size_mb": total_mb,
            "folder": str(self.target_dir.resolve()),
            "limit_respected": self.downloaded_bytes <= self.max_bytes
        }

        if progress_callback:
            progress_callback({
                "status": "completed",
                "message": f"Сохранено {self.downloaded_count} фото (Всего: {total_mb} MB из 1024 MB).",
                "folder": str(self.target_dir.resolve()),
                "size_mb": total_mb,
                "count": self.downloaded_count
            })

        return res
