import aiohttp
import logging
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class SafebooruProvider(BaseProvider):
    name = "safebooru"
    display_name = "Safebooru"
    base_url = "https://safebooru.org/index.php"

    def get_rating_tag(self, rating: str):
        return None

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        tags = self.build_tags(query, "all")
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": "1",
            "tags": tags,
            "pid": page - 1,
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
                                directory = item.get("directory", "")
                                image_name = item.get("image", "")
                                if not image_name:
                                    continue
                                file_url = f"https://safebooru.org/images/{directory}/{image_name}"
                                preview_url = f"https://safebooru.org/thumbnails/{directory}/thumbnail_{image_name}"
                                sample_url = item.get("sample_url") or file_url
                                
                                raw_tags = item.get("tags", "")
                                tag_list = raw_tags.split() if isinstance(raw_tags, str) else []
                                
                                post = Post(
                                    id=post_id,
                                    source=self.name,
                                    file_url=file_url,
                                    preview_url=preview_url,
                                    sample_url=sample_url,
                                    width=int(item.get("width", 0) or 0),
                                    height=int(item.get("height", 0) or 0),
                                    file_ext=image_name.split(".")[-1].lower() if "." in image_name else "jpg",
                                    tags=tag_list,
                                    rating="safe",
                                    score=int(item.get("score", 0) or 0),
                                    source_page_url=f"https://safebooru.org/index.php?page=post&s=view&id={post_id}",
                                    created_at=str(item.get("created_at", ""))
                                )
                                posts.append(post)
        except Exception as e:
            logger.warning(f"Error fetching from {self.name}: {e}")
            raise e

        return posts


class WaifuImProvider(BaseProvider):
    name = "waifu_im"
    display_name = "Waifu.im (Anime & NSFW)"
    base_url = "https://api.waifu.im/search"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        is_nsfw = "true" if rating in ("explicit", "questionable", "all") else "false"
        params = {
            "is_nsfw": is_nsfw,
            "limit": min(limit, 30)
        }
        clean_query = query.strip().lower()
        valid_tags = ["hentai", "milf", "oral", "paizuri", "ecchi", "ero", "ass", "maid", "waifu", "oppai", "uniform"]
        matched_tags = [t for t in valid_tags if t in clean_query]
        if matched_tags:
            params["included_tags"] = matched_tags[0]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NSFWImageSearcher/1.0"
        }

        posts: List[Post] = []
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        images = data.get("images", [])
                        for item in images:
                            image_id = str(item.get("image_id", ""))
                            file_url = item.get("url", "")
                            if not file_url:
                                continue
                            tags_data = item.get("tags", [])
                            tags = [t.get("name", "") for t in tags_data if isinstance(t, dict)]
                            is_nsfw_item = item.get("is_nsfw", True)
                            
                            post = Post(
                                id=image_id,
                                source=self.name,
                                file_url=file_url,
                                preview_url=file_url,
                                sample_url=file_url,
                                width=int(item.get("width", 0) or 0),
                                height=int(item.get("height", 0) or 0),
                                file_ext=item.get("extension", ".jpg").replace(".", "").lower(),
                                tags=tags,
                                rating="explicit" if is_nsfw_item else "safe",
                                score=int(item.get("favorites", 0) or 0),
                                source_page_url=item.get("source", file_url),
                                created_at=str(item.get("uploaded_at", ""))
                            )
                            posts.append(post)
        except Exception as e:
            logger.warning(f"Error fetching from {self.name}: {e}")
            raise e

        return posts
