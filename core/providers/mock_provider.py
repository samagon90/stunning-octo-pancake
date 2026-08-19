import hashlib
import random
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

# Curated high quality demo art URLs (safe/anime/digital art from Wikimedia and CDN demo repositories)
DEMO_IMAGES = [
    {
        "id": "1001",
        "url": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=400&auto=format&fit=crop&q=80",
        "tags": ["solo", "1girl", "long_hair", "cyberpunk", "highres", "masterpiece", "blue_eyes", "futuristic"],
        "rating": "explicit",
        "width": 3840,
        "height": 2160,
        "score": 450,
    },
    {
        "id": "1002",
        "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=80",
        "tags": ["abstract", "colorful", "digital_art", "wallpaper", "4k", "aesthetic", "vibrant"],
        "rating": "explicit",
        "width": 2560,
        "height": 1440,
        "score": 380,
    },
    {
        "id": "1003",
        "url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=400&auto=format&fit=crop&q=80",
        "tags": ["landscape", "neon_lights", "night", "cityscape", "fantasy", "art", "wallpaper"],
        "rating": "questionable",
        "width": 1920,
        "height": 1080,
        "score": 520,
    },
    {
        "id": "1004",
        "url": "https://images.unsplash.com/photo-1563089145-599997674d42?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1563089145-599997674d42?w=400&auto=format&fit=crop&q=80",
        "tags": ["neon", "portrait", "1girl", "cyberpunk", "model", "pink_hair", "aesthetic", "glowing"],
        "rating": "explicit",
        "width": 2048,
        "height": 2048,
        "score": 670,
    },
    {
        "id": "1005",
        "url": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=400&auto=format&fit=crop&q=80",
        "tags": ["synthwave", "retrowave", "sunset", "retro", "80s", "neon", "grid", "wallpaper"],
        "rating": "safe",
        "width": 3840,
        "height": 2160,
        "score": 890,
    },
    {
        "id": "1006",
        "url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=400&auto=format&fit=crop&q=80",
        "tags": ["anime_style", "1girl", "school_uniform", "sakura", "cherry_blossom", "spring", "art"],
        "rating": "questionable",
        "width": 1440,
        "height": 2560,
        "score": 410,
    },
    {
        "id": "1007",
        "url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=400&auto=format&fit=crop&q=80",
        "tags": ["oil_painting", "fine_art", "portrait", "classical", "figure", "aesthetic"],
        "rating": "explicit",
        "width": 2000,
        "height": 3000,
        "score": 340,
    },
    {
        "id": "1008",
        "url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=80",
        "preview": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400&auto=format&fit=crop&q=80",
        "tags": ["fantasy", "gothic", "dark_aesthetic", "mystic", "witch", "costume", "sensual"],
        "rating": "explicit",
        "width": 1920,
        "height": 1280,
        "score": 620,
    }
]

class MockProvider(BaseProvider):
    name = "demo"
    display_name = "Demo / Offline Mode"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        posts: List[Post] = []
        clean_query = query.strip().lower()
        search_tags = [t for t in clean_query.split() if t]

        # Generate realistic dynamic items based on query
        count = min(limit, 24)
        for i in range(count):
            base_item = DEMO_IMAGES[i % len(DEMO_IMAGES)]
            seed_val = f"{query}_{page}_{i}"
            item_id = str(abs(hash(seed_val)) % 900000 + 100000)
            
            # Combine tags
            post_tags = list(base_item["tags"])
            if search_tags:
                for st in search_tags:
                    if st not in post_tags:
                        post_tags.insert(0, st)
            
            item_rating = base_item["rating"]
            if rating and rating != "all":
                item_rating = rating

            post = Post(
                id=item_id,
                source=f"demo_booru",
                file_url=base_item["url"],
                preview_url=base_item["preview"],
                sample_url=base_item["url"],
                width=base_item["width"],
                height=base_item["height"],
                file_ext="jpg",
                file_size=base_item["width"] * base_item["height"] * 3 // 4,
                tags=post_tags,
                rating=item_rating,
                score=base_item["score"] + (i * 17) % 200,
                source_page_url=f"https://example.com/post/{item_id}",
                created_at="2026-08-19"
            )
            posts.append(post)

        return posts
