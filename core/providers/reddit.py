import re
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class RedditImageProvider(BaseProvider):
    name = "reddit"
    display_name = "🔴 Reddit (NSFW, Модели, Косплей)"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        if not query.strip():
            query = "model"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 NSFWImageHunter/1.0"
        }

        posts: List[Post] = []
        search_url = f"https://www.reddit.com/search.json?q={urllib.parse.quote_plus(query)}&include_over_18=on&sort=top&limit={min(limit, 100)}"

        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(search_url) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        children = data.get("data", {}).get("children", [])
                        
                        for item in children:
                            pdata = item.get("data", {})
                            url = pdata.get("url", "")
                            
                            # Filter image URLs
                            if not any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]) and "i.redd.it" not in url and "imgur.com" not in url:
                                # Check preview
                                preview = pdata.get("preview", {}).get("images", [])
                                if preview:
                                    url = preview[0].get("source", {}).get("url", "").replace("&amp;", "&")
                            
                            if not url or not url.startswith("http"):
                                continue

                            thumb = pdata.get("thumbnail")
                            if not thumb or not thumb.startswith("http"):
                                thumb = url

                            title = pdata.get("title", "")
                            subreddit = pdata.get("subreddit", "reddit")
                            score = int(pdata.get("ups", 0) or 0)
                            over_18 = pdata.get("over_18", True)

                            tags = [t for t in re.findall(r'[\w\-]+', f"{query} {title} {subreddit}".lower()) if len(t) > 2][:8]

                            post = Post(
                                id=f"reddit_{pdata.get('id', abs(hash(url)) % 1000000)}",
                                source=f"r/{subreddit}",
                                file_url=url,
                                preview_url=thumb,
                                sample_url=url,
                                width=1920,
                                height=1080,
                                file_ext=url.split(".")[-1].split("?")[0].lower() if "." in url else "jpg",
                                tags=tags,
                                rating="explicit" if over_18 else "safe",
                                score=score,
                                source_page_url=f"https://reddit.com{pdata.get('permalink', '')}",
                                created_at="reddit"
                            )
                            posts.append(post)

        except Exception as e:
            logger.warning(f"Reddit search error: {e}")
            raise e

        return posts
