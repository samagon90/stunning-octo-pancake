import asyncio
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.yandex import YandexImageProvider
from core.providers.bing import BingImageProvider
from core.providers.google import GoogleImageProvider
from core.providers.duckduckgo_images import DuckDuckGoImageProvider
from core.providers.reddit import RedditImageProvider

logger = logging.getLogger(__name__)

class MetaSearchProvider(BaseProvider):
    name = "meta"
    display_name = "🚀 ВСЕ ПОИСКОВИКИ ВМЕСТЕ (Яндекс + Bing + Google + Reddit + DuckDuckGo)"

    def __init__(self):
        self.sub_providers = [
            YandexImageProvider(),
            BingImageProvider(),
            GoogleImageProvider(),
            DuckDuckGoImageProvider(),
            RedditImageProvider()
        ]

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        per_provider = max(10, limit // len(self.sub_providers))
        tasks = [
            p.search(query, page, per_provider, rating)
            for p in self.sub_providers
        ]

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[Post] = []
        
        for res in gathered:
            if isinstance(res, list):
                results.extend(res)
            elif isinstance(res, Exception):
                logger.debug(f"Sub-provider search warning: {res}")

        # Deduplicate
        seen = set()
        deduped = []
        for p in results:
            if p.file_url and p.file_url not in seen:
                seen.add(p.file_url)
                deduped.append(p)

        return deduped
