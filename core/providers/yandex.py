import re
import json
import html
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class YandexImageProvider(BaseProvider):
    name = "yandex"
    display_name = "🇷🇺 Яндекс Картинки (Yandex Images)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "красивые девушки фото"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://yandex.ru/"
        }

        posts: List[Post] = []
        p_offset = page - 1
        search_url = f"https://yandex.ru/images/search?text={urllib.parse.quote_plus(query)}&p={p_offset}&isize=medium&nomisspell=1"

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(search_url) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        
                        # Method 1: Extract data-bem json blocks
                        bem_matches = re.findall(r'class="[^"]*serp-item[^"]*"[^>]*data-bem=[\'"](.*?)[\'"]', content)
                        for raw_bem in bem_matches:
                            if len(posts) >= limit:
                                break
                            try:
                                unescaped = html.unescape(raw_bem)
                                bem_data = json.loads(unescaped)
                                item = bem_data.get("serp-item", {})
                                
                                img_url = item.get("img_href")
                                if not img_url:
                                    origin = item.get("origin", {})
                                    img_url = origin.get("url")
                                if not img_url:
                                    dups = item.get("dups", [])
                                    if dups and isinstance(dups, list):
                                        img_url = dups[0].get("url")
                                
                                if not img_url or not img_url.startswith("http"):
                                    continue

                                preview_url = img_url
                                previews = item.get("preview", [])
                                if previews and isinstance(previews, list):
                                    preview_url = previews[0].get("url") or img_url
                                
                                w = int(item.get("preview", [{}])[0].get("w", 0) if item.get("preview") else 0)
                                h = int(item.get("preview", [{}])[0].get("h", 0) if item.get("preview") else 0)
                                title = item.get("snippet", {}).get("title", "") or query
                                
                                tags = [t for t in re.findall(r'[\w\-]+', f"{query} {title}".lower()) if len(t) > 2][:8]

                                post = Post(
                                    id=f"yandex_{abs(hash(img_url)) % 10000000}",
                                    source="yandex",
                                    file_url=img_url,
                                    preview_url=preview_url,
                                    sample_url=img_url,
                                    width=w or 1200,
                                    height=h or 800,
                                    file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                                    tags=tags,
                                    rating="explicit" if rating in ("explicit", "all") else "safe",
                                    score=850,
                                    source_page_url=item.get("snippet", {}).get("url", img_url),
                                    created_at="yandex_search"
                                )
                                posts.append(post)
                            except Exception:
                                continue

                        # Method 2: Direct img_href regex fallback if data-bem format changed
                        if not posts:
                            urls = re.findall(r'"img_href"\s*:\s*"([^"]+)"', content)
                            for u in urls[:limit]:
                                clean_u = u.replace("\\/", "/")
                                post = Post(
                                    id=f"yandex_{abs(hash(clean_u)) % 10000000}",
                                    source="yandex",
                                    file_url=clean_u,
                                    preview_url=clean_u,
                                    sample_url=clean_u,
                                    width=1920,
                                    height=1080,
                                    file_ext=clean_u.split(".")[-1].split("?")[0].lower() if "." in clean_u else "jpg",
                                    tags=[query],
                                    rating="explicit",
                                    score=800,
                                    source_page_url=clean_u,
                                    created_at="yandex_search"
                                )
                                posts.append(post)

        except Exception as e:
            logger.warning(f"Yandex search error: {e}")
            raise e

        return posts
