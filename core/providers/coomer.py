import re
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class CoomerModelProvider(BaseProvider):
    name = "coomer"
    display_name = "⭐ Coomer / OnlyFans / Fansly Archive (Модели и Фотосеты)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model"

        queries = [query]
        if is_cyrillic(query):
            latin = transliterate(query)
            if latin != query:
                queries.append(latin)

        posts: List[Post] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            for q in queries:
                if len(posts) >= limit:
                    break
                
                encoded_q = urllib.parse.quote_plus(q)
                url = f"https://coomer.su/api/v1/posts?q={encoded_q}&o={(page - 1) * limit}"
                
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            if isinstance(data, list):
                                for item in data:
                                    if len(posts) >= limit:
                                        break
                                    
                                    post_id = str(item.get("id", ""))
                                    title = item.get("title", "") or item.get("user", "") or q
                                    service = item.get("service", "onlyfans")
                                    user = item.get("user", "")
                                    
                                    # Collect files from item
                                    files_to_add = []
                                    main_file = item.get("file", {})
                                    if main_file and isinstance(main_file, dict) and main_file.get("path"):
                                        files_to_add.append(main_file.get("path"))
                                    
                                    for att in item.get("attachments", []):
                                        if isinstance(att, dict) and att.get("path"):
                                            files_to_add.append(att.get("path"))
                                    
                                    for path in files_to_add:
                                        if not any(path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4"]):
                                            continue
                                        
                                        file_url = f"https://coomer.su/data{path}"
                                        preview_url = f"https://coomer.su/data{path}"
                                        
                                        tags = [t for t in re.findall(r'[\w\-]+', f"{q} {user} {title}".lower()) if len(t) > 2][:8]
                                        
                                        post = Post(
                                            id=f"coomer_{post_id}_{abs(hash(path)) % 10000}",
                                            source=f"Coomer ({service})",
                                            file_url=file_url,
                                            preview_url=preview_url,
                                            sample_url=file_url,
                                            width=1920,
                                            height=1080,
                                            file_ext=path.split(".")[-1].lower() if "." in path else "jpg",
                                            tags=tags,
                                            rating="explicit",
                                            score=990,
                                            source_page_url=f"https://coomer.su/{service}/user/{user}/post/{post_id}",
                                            created_at=item.get("published", "")
                                        )
                                        posts.append(post)
                                        if len(posts) >= limit:
                                            break
                except Exception as e:
                    logger.debug(f"Coomer query failed: {e}")

        return posts
