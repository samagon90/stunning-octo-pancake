import asyncio
import logging
import re
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.web_engines import search_bing_async, search_yahoo_images
from core.providers.reddit import RedditImageProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class UniversalWebSearchProvider(BaseProvider):
    name = "universal_web"
    display_name = "🌐 Поиск в интернете (Яндекс, Bing, Yahoo, DuckDuckGo, Reddit)"

    async def search(self, query: str, page: int = 1, limit: int = 50, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "красивые модели фото"

        queries = [query]
        if is_cyrillic(query):
            latin_q = transliterate(query)
            if latin_q != query:
                queries.append(latin_q)

        results: List[Post] = []
        tasks = []

        # Run Bing async search for both Russian and English queries
        for q in queries:
            tasks.append(search_bing_async(q, limit=limit // 2))
            tasks.append(search_yahoo_images(q, limit=limit // 2))
        
        # Also run Reddit
        reddit = RedditImageProvider()
        for q in queries:
            tasks.append(reddit.search(q, page=page, limit=20, rating=rating))

        # Run DDGS if available
        try:
            from ddgs import DDGS
            def ddgs_search_sync(k):
                dd_posts = []
                try:
                    with DDGS() as ddgs:
                        res = ddgs.images(keywords=k, safesearch="off", max_results=30)
                        if res:
                            for item in res:
                                img = item.get("image")
                                if img and img.startswith("http"):
                                    dd_posts.append(Post(
                                        id=f"dd_{abs(hash(img)) % 10000000}",
                                        source=f"Web ({item.get('source', 'DuckDuckGo')})",
                                        file_url=img,
                                        preview_url=item.get("thumbnail") or img,
                                        sample_url=img,
                                        width=int(item.get("width", 1920) or 1920),
                                        height=int(item.get("height", 1080) or 1080),
                                        file_ext=img.split(".")[-1].split("?")[0].lower() if "." in img else "jpg",
                                        tags=[query],
                                        rating="explicit",
                                        score=920,
                                        source_page_url=item.get("url", img),
                                        created_at="ddgs"
                                    ))
                except Exception:
                    pass
                return dd_posts

            loop = asyncio.get_event_loop()
            for q in queries:
                tasks.append(loop.run_in_executor(None, ddgs_search_sync, q))
        except Exception:
            pass

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for g in gathered:
            if isinstance(g, list):
                results.extend(g)
            elif isinstance(g, Exception):
                logger.debug(f"Search task warning: {g}")

        # Deduplicate
        seen = set()
        deduped = []
        for p in results:
            if p.file_url and p.file_url not in seen:
                seen.add(p.file_url)
                deduped.append(p)

        return deduped
