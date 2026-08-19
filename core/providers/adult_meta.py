import asyncio
import logging
import re
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.direct_search import search_yandex_touch, search_google_gbv, search_bing_direct
from core.providers.coomer import CoomerModelProvider
from core.providers.erome import EroMeProvider
from core.providers.reddit import RedditImageProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

def is_garbage_image(url: str) -> bool:
    """Filter out tracking pixels, icons, and non-content noise."""
    lower_u = url.lower()
    bad_patterns = [
        "favicon", "pixel.gif", "spacer", "logo", "button", "avatar",
        "icon", "advert", "banner", "static/img", "parliament", "minister"
    ]
    return any(p in lower_u for p in bad_patterns)

class AdultMetaSearchProvider(BaseProvider):
    name = "adult_meta"
    display_name = "👑 ПОИСК МОДЕЛЕЙ И ФОТОСЕТОВ 18+ (Яндекс + EroMe + Coomer + Google + Reddit)"

    def __init__(self):
        self.coomer = CoomerModelProvider()
        self.erome = EroMeProvider()
        self.reddit = RedditImageProvider()

    async def search(self, query: str, page: int = 1, limit: int = 60, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model"

        queries = [query]
        if is_cyrillic(query):
            latin = transliterate(query)
            if latin != query:
                queries.append(latin)

        tasks = []
        for q in queries:
            # 1. Yandex (Top Russian search engine)
            tasks.append(search_yandex_touch(q, page=page, limit=40))
            
            # 2. EroMe (Album galleries)
            tasks.append(self.erome.search(q, page=page, limit=30, rating=rating))
            
            # 3. Coomer.su (OnlyFans / Fansly archives)
            tasks.append(self.coomer.search(q, page=page, limit=30, rating=rating))
            
            # 4. Reddit NSFW
            tasks.append(self.reddit.search(q, page=page, limit=25, rating=rating))
            
            # 5. Google Images
            tasks.append(search_google_gbv(q, page=page, limit=25))

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[Post] = []

        for g in gathered:
            if isinstance(g, list):
                results.extend(g)
            elif isinstance(g, Exception):
                logger.debug(f"Search provider error: {g}")

        # Deduplicate and keep all valid image URLs
        seen = set()
        deduped: List[Post] = []
        
        for p in results:
            if not p.file_url or p.file_url in seen:
                continue
            if is_garbage_image(p.file_url):
                continue

            seen.add(p.file_url)
            deduped.append(p)

        return deduped
