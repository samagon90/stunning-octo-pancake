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

class BingImageProvider(BaseProvider):
    name = "bing"
    display_name = "🌐 Bing Картинки (Bing Images - 18+ Без цензуры)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model photoshoot"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.bing.com/",
            "Cookie": "SRCHHPGUSR=ADLT=OFF&NRSLT=50;"  # ADLT=OFF disables SafeSearch in Bing!
        }

        posts: List[Post] = []
        first_index = (page - 1) * limit + 1
        search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote_plus(query)}&first={first_index}&count={limit}&adlt=off&safesearch=off"

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(search_url) as resp:
                    if resp.status == 200:
                        content = await resp.text()

                        # Extract m="..." JSON data
                        m_matches = re.findall(r'class="iusc"[^>]*m=[\'"](.*?)[\'"]', content)
                        if not m_matches:
                            m_matches = re.findall(r'm=[\'"](\{"murl":.*?\})[\'"]', content)

                        for raw_m in m_matches:
                            if len(posts) >= limit:
                                break
                            try:
                                unescaped = html.unescape(raw_m)
                                m_data = json.loads(unescaped)
                                murl = m_data.get("murl")
                                if not murl or not murl.startswith("http"):
                                    continue
                                
                                turl = m_data.get("turl") or murl
                                desc = m_data.get("desc", "") or m_data.get("t", "") or query
                                page_url = m_data.get("purl", murl)

                                tags = [t for t in re.findall(r'[\w\-]+', f"{query} {desc}".lower()) if len(t) > 2][:8]

                                post = Post(
                                    id=f"bing_{abs(hash(murl)) % 10000000}",
                                    source="bing",
                                    file_url=murl,
                                    preview_url=turl,
                                    sample_url=murl,
                                    width=1920,
                                    height=1080,
                                    file_ext=murl.split(".")[-1].split("?")[0].lower() if "." in murl else "jpg",
                                    tags=tags,
                                    rating="explicit" if rating in ("explicit", "all") else "safe",
                                    score=900,
                                    source_page_url=page_url,
                                    created_at="bing_search"
                                )
                                posts.append(post)
                            except Exception:
                                continue

                        # Fallback: extract direct murl regex
                        if not posts:
                            direct_urls = re.findall(r'"murl"\s*:\s*"([^"]+)"', content)
                            for u in direct_urls[:limit]:
                                clean_u = u.replace("\\/", "/")
                                post = Post(
                                    id=f"bing_{abs(hash(clean_u)) % 10000000}",
                                    source="bing",
                                    file_url=clean_u,
                                    preview_url=clean_u,
                                    sample_url=clean_u,
                                    width=1920,
                                    height=1080,
                                    file_ext="jpg",
                                    tags=[query],
                                    rating="explicit",
                                    score=900,
                                    source_page_url=clean_u,
                                    created_at="bing_search"
                                )
                                posts.append(post)

        except Exception as e:
            logger.warning(f"Bing search error: {e}")
            raise e

        return posts
