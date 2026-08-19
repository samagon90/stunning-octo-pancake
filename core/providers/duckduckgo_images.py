import re
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class DuckDuckGoImageProvider(BaseProvider):
    name = "duckduckgo"
    display_name = "🌐 Web Search (DuckDuckGo Images - 18+)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model photoshoot wallpaper"

        # Headers to look like a standard desktop browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://duckduckgo.com/"
        }

        posts: List[Post] = []
        timeout = aiohttp.ClientTimeout(total=15)

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                # Step 1: Get VQD token from search page
                token_url = f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}"
                vqd = None
                
                async with session.get(token_url) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Search for vqd=... or vqd="..."
                        match = re.search(r'vqd=([\d\-]+)', html)
                        if not match:
                            match = re.search(r'vqd=([\'"])(.*?)\1', html)
                            if match:
                                vqd = match.group(2)
                        else:
                            vqd = match.group(1)

                if not vqd:
                    # Alternative regex for vqd in script tags
                    match = re.search(r'vqd:\s*["\']([^"\']+)["\']', html)
                    if match:
                        vqd = match.group(1)

                if not vqd:
                    vqd = "4-12345678901234567890"

                # Step 2: Request images with SafeSearch OFF (p=-1 / kp=-2)
                offset = (page - 1) * limit
                img_url = f"https://duckduckgo.com/i.js?l=wt-wt&o=json&q={urllib.parse.quote_plus(query)}&vqd={vqd}&f=,,,&p=-1&s={offset}"

                async with session.get(img_url) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        results = data.get("results", [])
                        
                        for idx, item in enumerate(results[:limit]):
                            image_url = item.get("image")
                            if not image_url or not image_url.startswith("http"):
                                continue
                            
                            thumb_url = item.get("thumbnail") or image_url
                            title = item.get("title", "") or query
                            width = int(item.get("width", 0) or 0)
                            height = int(item.get("height", 0) or 0)
                            source_domain = item.get("source", "web")
                            page_url = item.get("url", image_url)
                            
                            # Clean tags from title and query
                            clean_words = re.findall(r'[\w\-]+', f"{query} {title}".lower())
                            tags = list(dict.fromkeys([w for w in clean_words if len(w) > 2]))[:8]

                            post = Post(
                                id=f"web_{abs(hash(image_url)) % 10000000}",
                                source=f"web ({source_domain})",
                                file_url=image_url,
                                preview_url=thumb_url,
                                sample_url=image_url,
                                width=width,
                                height=height,
                                file_ext=image_url.split(".")[-1].split("?")[0].lower() if "." in image_url else "jpg",
                                tags=tags,
                                rating="explicit" if rating in ("explicit", "all") else "questionable",
                                score=width * height // 10000 if width and height else 500,
                                source_page_url=page_url,
                                created_at="web_search"
                            )
                            posts.append(post)

        except Exception as e:
            logger.warning(f"DuckDuckGo image search error: {e}")
            raise e

        return posts
