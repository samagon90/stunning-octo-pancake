import asyncio
import logging
import re
from typing import List
from core.models import Post
from core.providers.base import BaseProvider
from core.translit import transliterate, is_cyrillic

logger = logging.getLogger(__name__)

class WebSearchProvider(BaseProvider):
    name = "web"
    display_name = "🌐 Поиск в интернете (Фотосессии, Модели, Знаменитости 18+)"

    def _sync_search(self, query: str, limit: int = 50, rating: str = "all") -> List[Post]:
        posts: List[Post] = []
        
        # Try DDGS / duckduckgo_search first
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                DDGS = None

        if DDGS:
            queries_to_try = [query]
            if is_cyrillic(query):
                queries_to_try.append(transliterate(query))

            for q in queries_to_try:
                if len(posts) >= limit:
                    break
                try:
                    with DDGS() as ddgs:
                        # safesearch='off' retrieves uncensored results
                        results = ddgs.images(
                            keywords=q,
                            region="wt-wt",
                            safesearch="off",
                            size="Large",
                            max_results=min(limit, 60)
                        )
                        if results:
                            for item in results:
                                img_url = item.get("image")
                                if not img_url or not img_url.startswith("http"):
                                    continue
                                
                                thumb_url = item.get("thumbnail") or img_url
                                title = item.get("title", "") or query
                                width = int(item.get("width", 0) or 0)
                                height = int(item.get("height", 0) or 0)
                                source_site = item.get("source", "Web")
                                page_url = item.get("url", img_url)

                                tags = [t for t in re.findall(r'[\w\-]+', f"{query} {title}".lower()) if len(t) > 2][:8]

                                post = Post(
                                    id=f"web_{abs(hash(img_url)) % 10000000}",
                                    source=f"Web ({source_site})",
                                    file_url=img_url,
                                    preview_url=thumb_url,
                                    sample_url=img_url,
                                    width=width or 1920,
                                    height=height or 1080,
                                    file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                                    tags=tags,
                                    rating="explicit" if rating in ("explicit", "all") else "safe",
                                    score=880,
                                    source_page_url=page_url,
                                    created_at="web"
                                )
                                posts.append(post)
                except Exception as e:
                    logger.warning(f"DDGS query '{q}' failed: {e}")

        return posts

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model photoshoot"

        # Run synchronous DDGS search in background thread pool
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(None, self._sync_search, query, limit, rating)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Web search error: {e}")

        # Fallback to direct Reddit / Bing
        from core.providers.reddit import RedditImageProvider
        reddit = RedditImageProvider()
        try:
            reddit_posts = await reddit.search(query, page, limit, rating)
            if reddit_posts:
                return reddit_posts
        except Exception:
            pass

        return []
