import asyncio
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.direct_search import search_yandex_touch, search_google_gbv, search_bing_direct, search_yahoo_direct
from core.providers.reddit import RedditImageProvider
from core.providers.adult_meta import is_garbage_image
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class UniversalWebSearchProvider(BaseProvider):
    name = "universal_web"
    display_name = "🌐 Поиск в интернете (Яндекс, Google, Yahoo, Reddit)"

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

        reddit = RedditImageProvider()
        for q in queries:
            tasks.append(search_yandex_touch(q, page=page, limit=35))
            tasks.append(search_google_gbv(q, page=page, limit=25))
            tasks.append(search_yahoo_direct(q, page=page, limit=25))
            tasks.append(reddit.search(q, page=page, limit=20, rating=rating))

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for g in gathered:
            if isinstance(g, list):
                results.extend(g)
            elif isinstance(g, Exception):
                logger.debug(f"Search task warning: {g}")

        # Deduplicate and filter out garbage
        seen = set()
        deduped = []
        for p in results:
            if p.file_url and p.file_url not in seen:
                if not is_garbage_image(p.file_url):
                    seen.add(p.file_url)
                    deduped.append(p)

        return deduped
