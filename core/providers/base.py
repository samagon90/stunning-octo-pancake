import abc
from typing import List, Optional
from core.models import Post

class BaseProvider(abc.ABC):
    name: str = "base"
    display_name: str = "Base Provider"
    supports_ratings: bool = True
    default_rating: str = "explicit"

    @abc.abstractmethod
    async def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 40,
        rating: str = "all"
    ) -> List[Post]:
        """Search for posts matching query and filters."""
        pass

    def build_tags(self, query: str, rating: str = "all") -> str:
        """Combine user query with rating filter."""
        tags = [t.strip() for t in query.split() if t.strip()]
        if rating and rating != "all":
            rating_tag = self.get_rating_tag(rating)
            if rating_tag and not any(t.startswith("rating:") for t in tags):
                tags.append(rating_tag)
        return " ".join(tags)

    def get_rating_tag(self, rating: str) -> Optional[str]:
        mapping = {
            "explicit": "rating:explicit",
            "questionable": "rating:questionable",
            "safe": "rating:safe",
            "sensitive": "rating:sensitive"
        }
        return mapping.get(rating.lower())
