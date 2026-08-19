import hashlib
from typing import List
from core.models import Post
from core.providers.base import BaseProvider

class MockProvider(BaseProvider):
    name = "demo"
    display_name = "Demo / Offline Mode"

    async def search(self, query: str, page: int = 1, limit: int = 40, rating: str = "all") -> List[Post]:
        # Return empty list in demo so we never show unrelated placeholder art
        return []
