import asyncio
import logging
import re
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.providers.direct_search import search_yandex_touch, search_google_gbv
from core.providers.coomer import CoomerModelProvider
from core.providers.erome import EroMeProvider
from core.providers.reddit import RedditImageProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

def is_post_relevant(post: Post, query: str) -> bool:
    """Filter out garbage results like parliament buildings, news, or unrelated stock photos."""
    tokens = [t.lower() for t in re.findall(r'[\w\-]+', query) if len(t) > 2]
    if not tokens:
        return True

    latin_tokens = [transliterate(t).lower() for t in tokens]
    all_tokens = set(tokens + latin_tokens)

    # Search space includes tags, URL, and source page
    combined_info = " ".join(post.tags).lower() + " " + post.file_url.lower() + " " + post.source_page_url.lower()

    # Discard obvious non-NSFW / non-model noise (parliament, government, news, furniture, politics)
    garbage_words = ["parliament", "minister", "politics", "president", "assembly", "congress", "building", "statue", "furniture"]
    if any(gb in combined_info for gb in garbage_words) and not any(tok in combined_info for tok in all_tokens):
        return False

    # Check if at least one query token matches
    return any(tok in combined_info for tok in all_tokens)

class AdultMetaSearchProvider(BaseProvider):
    name = "adult_meta"
    display_name = "👑 ПОИСК МОДЕЛЕЙ И ФОТОСЕТОВ 18+ (Яндекс + Coomer + EroMe + Reddit + Google)"

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
            # 1. Yandex Touch (Most accurate for Russian models and photos)
            tasks.append(search_yandex_touch(q, page=page, limit=35))
            
            # 2. Coomer.su (OnlyFans / Fansly / Patreon sets)
            tasks.append(self.coomer.search(q, page=page, limit=35, rating=rating))
            
            # 3. EroMe (Model albums & photosets)
            tasks.append(self.erome.search(q, page=page, limit=25, rating=rating))
            
            # 4. Reddit NSFW (Cosplay & model subs)
            tasks.append(self.reddit.search(q, page=page, limit=25, rating=rating))
            
            # 5. Google Images
            tasks.append(search_google_gbv(q, page=page, limit=20))

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[Post] = []

        for g in gathered:
            if isinstance(g, list):
                results.extend(g)
            elif isinstance(g, Exception):
                logger.debug(f"Sub-provider error: {g}")

        # Filter strictly for relevance and deduplicate
        seen = set()
        deduped: List[Post] = []
        
        for p in results:
            if not p.file_url or p.file_url in seen:
                continue
            
            # Filter out irrelevant noise (e.g. parliament, news)
            if not is_post_relevant(p, query):
                continue

            seen.add(p.file_url)
            deduped.append(p)

        # If strict relevance filtered too much, add remaining without garbage
        if len(deduped) < 10:
            for p in results:
                if p.file_url and p.file_url not in seen:
                    combined = (p.file_url + " " + p.source_page_url).lower()
                    if not any(gb in combined for gb in ["parliament", "politics", "minister", "congress"]):
                        seen.add(p.file_url)
                        deduped.append(p)

        return deduped
