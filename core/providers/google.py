import re
import json
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class GoogleImageProvider(BaseProvider):
    name = "google"
    display_name = "🔍 Google Картинки (Google Images)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model photography"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }

        posts: List[Post] = []
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&tbm=isch&safe=off&hl=ru&gl=ru"

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(search_url) as resp:
                    if resp.status == 200:
                        html = await resp.text()

                        # Extract high-res image URLs from Google scripts
                        # Pattern matches ["http...", width, height]
                        matches = re.findall(r'\["(http[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)",\s*(\d+),\s*(\d+)\]', html, re.IGNORECASE)
                        
                        seen = set()
                        for m in matches:
                            if len(posts) >= limit:
                                break
                            img_url, h, w = m
                            img_url = img_url.replace("\\u003d", "=").replace("\\u0026", "&").replace("\\/", "/")
                            
                            # Filter out Google domain internal assets
                            if "gstatic.com" in img_url or "google.com" in img_url:
                                continue
                            
                            if img_url in seen:
                                continue
                            seen.add(img_url)

                            post = Post(
                                id=f"google_{abs(hash(img_url)) % 10000000}",
                                source="google",
                                file_url=img_url,
                                preview_url=img_url,
                                sample_url=img_url,
                                width=int(w or 1200),
                                height=int(h or 800),
                                file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                                tags=[query],
                                rating="explicit" if rating in ("explicit", "all") else "safe",
                                score=920,
                                source_page_url=img_url,
                                created_at="google_search"
                            )
                            posts.append(post)

        except Exception as e:
            logger.warning(f"Google search error: {e}")
            raise e

        return posts
