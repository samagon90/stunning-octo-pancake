from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

@dataclass
class Post:
    id: str
    source: str
    file_url: str
    preview_url: str
    sample_url: str = ""
    width: int = 0
    height: int = 0
    file_ext: str = "jpg"
    file_size: int = 0
    tags: List[str] = field(default_factory=list)
    rating: str = "explicit"  # explicit, questionable, sensitive, general, safe
    score: int = 0
    source_page_url: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "file_url": self.file_url,
            "preview_url": self.preview_url,
            "sample_url": self.sample_url or self.file_url,
            "width": self.width,
            "height": self.height,
            "file_ext": self.file_ext,
            "file_size": self.file_size,
            "tags": self.tags,
            "rating": self.rating,
            "score": self.score,
            "source_page_url": self.source_page_url,
            "created_at": self.created_at,
        }

class SearchRequest(BaseModel):
    query: str = ""
    source: str = "rule34"  # rule34, gelbooru, danbooru, yandere, konachan, waifu_im, all
    page: int = 1
    limit: int = 40
    rating: str = "all"  # all, explicit, questionable, safe
    min_width: int = 0
    min_height: int = 0
    aspect_ratio: str = "all"  # all, landscape, portrait, square
    sort: str = "recent"  # recent, score, random

class DownloadRequest(BaseModel):
    posts: List[Dict[str, Any]]
    destination_dir: str = "./downloads"
    naming_pattern: str = "{source}_{id}_{tags}"
    create_subfolders: bool = True
    subfolder_name: str = ""
    skip_existing: bool = True
    save_metadata: bool = True
    threads: int = 4
