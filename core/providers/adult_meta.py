import asyncio
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.direct_search import search_bing_direct, search_yahoo_direct, search_google_gbv, search_yandex_touch
from core.providers.coomer import CoomerModelProvider
from core.providers.erome import EroMeProvider
from core.providers.reddit import RedditImageProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class AdultMetaSearchProvider(BaseProvider):
    name = "adult_meta"
    display_name = "👑 ПОИСК МОДЕЛЕЙ И ФОТОСЕТОВ 18+ (Bing + Yahoo + Google + Яндекс + Coomer + EroMe + Reddit)"

    def __init__(self):
        self.coomer = CoomerModelProvider()
        self.erome = EroMeProvider()
        self.reddit = RedditImageProvider()

    async def search(self, query: str, page: int = 1, limit: int = 50, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model"

        queries = [query]
        if is_cyrillic(query):
            latin = transliterate(query)
            if latin != query:
                queries.append(latin)

        tasks = []
        for q in queries:
            tasks.append(search_bing_direct(q, limit=30))
            tasks.append(search_yahoo_direct(q, limit=25))
            tasks.append(search_google_gbv(q, limit=25))
            tasks.append(search_yandex_touch(q, limit=25))
            tasks.append(self.coomer.search(q, page=page, limit=30, rating=rating))
            tasks.append(self.erome.search(q, page=page, limit=20, rating=rating))
            tasks.append(self.reddit.search(q, page=page, limit=20, rating=rating))

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[Post] = []

        for g in gathered:
            if isinstance(g, list):
                results.extend(g)
            elif isinstance(g, Exception):
                logger.debug(f"Sub-provider error: {g}")

        # Deduplicate
        seen = set()
        deduped = []
        for p in results:
            if p.file_url and p.file_url not in seen:
                seen.add(p.file_url)
                deduped.append(p)

        return deduped
