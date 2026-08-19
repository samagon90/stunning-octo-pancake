import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class KonachanProvider(BaseProvider):
    name = "konachan"
    display_name = "Konachan (Konachan.com)"
    base_url = "https://konachan.com/post.json"

    def get_rating_tag(self, rating: str):
        mapping = {
            "explicit": "rating:e",
            "questionable": "rating:q",
            "safe": "rating:s"
        }
        return mapping.get(rating.lower())

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        tags = self.build_tags(query, rating)
        params = {
            "tags": tags,
            "page": page,
            "limit": min(limit, 100)
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 NSFWImageSearcher/1.0"
        }

        posts: List[Post] = []
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        if isinstance(data, list):
                            for item in data:
                                if not isinstance(item, dict):
                                    continue
                                post_id = str(item.get("id", ""))
                                file_url = item.get("file_url") or item.get("jpeg_url") or ""
                                if not file_url:
                                    continue
                                preview_url = item.get("preview_url") or item.get("sample_url") or file_url
                                sample_url = item.get("sample_url") or file_url
                                
                                raw_tags = item.get("tags", "")
                                tag_list = raw_tags.split() if isinstance(raw_tags, str) else []
                                
                                rating_val = str(item.get("rating", "e")).lower()
                                if rating_val in ("e", "explicit"):
                                    rating_str = "explicit"
                                elif rating_val in ("q", "questionable"):
                                    rating_str = "questionable"
                                elif rating_val in ("s", "safe"):
                                    rating_str = "safe"
                                else:
                                    rating_str = rating_val

                                post = Post(
                                    id=post_id,
                                    source=self.name,
                                    file_url=file_url,
                                    preview_url=preview_url,
                                    sample_url=sample_url,
                                    width=int(item.get("width", 0) or 0),
                                    height=int(item.get("height", 0) or 0),
                                    file_ext=file_url.split(".")[-1].split("?")[0].lower() if "." in file_url else "jpg",
                                    file_size=int(item.get("file_size", 0) or 0),
                                    tags=tag_list,
                                    rating=rating_str,
                                    score=int(item.get("score", 0) or 0),
                                    source_page_url=f"https://konachan.com/post/show/{post_id}",
                                    created_at=str(item.get("created_at", ""))
                                )
                                posts.append(post)
        except Exception as e:
            logger.warning(f"Error fetching from {self.name}: {e}")
            raise e

        return posts
