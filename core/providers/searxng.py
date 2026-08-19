import re
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

SEARXNG_INSTANCES = [
    "https://search.ononoki.org",
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://search.mdosch.de",
    "https://searx.work",
    "https://priv.au",
    "https://paulgo.io",
    "https://search.sapti.me"
]

class SearXNGImageProvider(BaseProvider):
    name = "searxng"
    display_name = "🌐 Глобальный Мета-Поиск (SearXNG: Google + Bing + Yahoo + Qwant)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        posts: List[Post] = []
        timeout = aiohttp.ClientTimeout(total=10)

        for instance in SEARXNG_INSTANCES:
            if len(posts) >= limit:
                break
            
            search_url = f"{instance}/search"
            params = {
                "q": query,
                "categories": "images",
                "format": "json",
                "pageno": page,
                "safesearch": "0"  # 0 = SafeSearch OFF
            }

            try:
                async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                    async with session.get(search_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            results = data.get("results", [])
                            
                            for item in results:
                                img_url = item.get("img_src") or item.get("url")
                                if not img_url or not img_url.startswith("http"):
                                    continue
                                
                                thumb_url = item.get("thumbnail_src") or item.get("thumbnail") or img_url
                                title = item.get("title", "") or query
                                engine = item.get("engine", "web")
                                
                                tags = [t for t in re.findall(r'[\w\-]+', f"{query} {title}".lower()) if len(t) > 2][:8]

                                post = Post(
                                    id=f"searx_{abs(hash(img_url)) % 10000000}",
                                    source=f"Web ({engine})",
                                    file_url=img_url,
                                    preview_url=thumb_url,
                                    sample_url=img_url,
                                    width=1920,
                                    height=1080,
                                    file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                                    tags=tags,
                                    rating="explicit",
                                    score=950,
                                    source_page_url=item.get("url", img_url),
                                    created_at="searxng"
                                )
                                posts.append(post)
                                if len(posts) >= limit:
                                    break
                            
                            if posts:
                                # Successfully got results from this instance
                                break
            except Exception as e:
                logger.debug(f"SearXNG instance {instance} failed: {e}")
                continue

        return posts
