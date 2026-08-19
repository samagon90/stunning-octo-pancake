import re
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class EroMeProvider(BaseProvider):
    name = "erome"
    display_name = "🔥 EroMe (Альбомы и фотосеты моделей)"

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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            for q in queries:
                if len(posts) >= limit:
                    break
                
                url = f"https://www.erome.com/search?q={urllib.parse.quote_plus(q)}&p={page}"
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            html_text = await resp.text()
                            
                            # Extract album covers / images
                            img_matches = re.findall(r'<img[^>]+(?:data-src|src)=[\'"](https://[^\'"]+\.(?:jpg|jpeg|png|webp))[\'"][^>]*title=[\'"]([^\'"]*)[\'"]', html_text, re.IGNORECASE)
                            if not img_matches:
                                img_matches = re.findall(r'<img[^>]+(?:data-src|src)=[\'"](https://s\d+\.erome\.com/[^\'"]+)[\'"]', html_text, re.IGNORECASE)
                                img_matches = [(m, q) for m in img_matches]
                            
                            for item in img_matches:
                                if isinstance(item, tuple):
                                    img_url, title = item
                                else:
                                    img_url, title = item, q
                                
                                if "placeholder" in img_url or "avatar" in img_url:
                                    continue

                                tags = [t for t in re.findall(r'[\w\-]+', f"{q} {title}".lower()) if len(t) > 2][:8]

                                post = Post(
                                    id=f"erome_{abs(hash(img_url)) % 10000000}",
                                    source="EroMe",
                                    file_url=img_url,
                                    preview_url=img_url,
                                    sample_url=img_url,
                                    width=1920,
                                    height=1080,
                                    file_ext="jpg",
                                    tags=tags,
                                    rating="explicit",
                                    score=960,
                                    source_page_url=url,
                                    created_at="erome"
                                )
                                posts.append(post)
                                if len(posts) >= limit:
                                    break
                except Exception as e:
                    logger.debug(f"EroMe query failed: {e}")

        return posts
