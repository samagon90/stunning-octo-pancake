import asyncio
import logging
from typing import Dict, List, Optional, Any
from core.models import Post, SearchRequest
from core.providers.base import BaseProvider
from core.providers.rule34 import Rule34Provider
from core.providers.gelbooru import GelbooruProvider
from core.providers.danbooru import DanbooruProvider
from core.providers.yandere import YandereProvider
from core.providers.konachan import KonachanProvider
from core.providers.realbooru import RealbooruProvider
from core.providers.safebooru import SafebooruProvider
from core.providers.waifu_im import WaifuImProvider
from core.providers.mock_provider import MockProvider

logger = logging.getLogger(__name__)

class ProviderManager:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "rule34": Rule34Provider(),
            "gelbooru": GelbooruProvider(),
            "danbooru": DanbooruProvider(),
            "yandere": YandereProvider(),
            "konachan": KonachanProvider(),
            "realbooru": RealbooruProvider(),
            "safebooru": SafebooruProvider(),
            "waifu_im": WaifuImProvider(),
            "demo": MockProvider()
        }

    def get_providers_list(self) -> List[Dict[str, str]]:
        return [
            {"id": k, "name": v.display_name}
            for k, v in self.providers.items()
        ]

    async def search(self, req: SearchRequest) -> Dict[str, Any]:
        source = req.source.lower()
        results: List[Post] = []
        errors: List[str] = []

        if source == "all":
            # Search across top providers concurrently
            active_sources = ["rule34", "gelbooru", "yandere", "danbooru"]
            tasks = []
            per_limit = max(10, req.limit // len(active_sources))
            for s in active_sources:
                provider = self.providers.get(s)
                if provider:
                    tasks.append(provider.search(req.query, req.page, per_limit, req.rating))
            
            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            for s, res in zip(active_sources, gathered):
                if isinstance(res, Exception):
                    errors.append(f"{s}: {str(res)}")
                elif isinstance(res, list):
                    results.extend(res)
            
            # If all external failed and no results, fallback to demo provider
            if not results and errors:
                logger.info("External providers failed, falling back to demo mode.")
                demo_results = await self.providers["demo"].search(req.query, req.page, req.limit, req.rating)
                results.extend(demo_results)
                errors.append("Внимание: внешние API недоступны, показаны демонстрационные результаты.")
        else:
            provider = self.providers.get(source)
            if not provider:
                provider = self.providers["rule34"]
            
            try:
                results = await provider.search(req.query, req.page, req.limit, req.rating)
            except Exception as e:
                errors.append(f"Ошибка загрузки с {provider.display_name}: {str(e)}")
                # Auto-fallback to demo for testing if offline
                demo_results = await self.providers["demo"].search(req.query, req.page, req.limit, req.rating)
                results.extend(demo_results)
                errors.append("Внимание: сервис временно недоступен или заблокирован сетью. Загружен демонстрационный каталог.")

        # Filter by minimum resolution
        if req.min_width > 0 or req.min_height > 0:
            results = [
                p for p in results
                if (p.width == 0 or p.width >= req.min_width) and
                   (p.height == 0 or p.height >= req.min_height)
            ]

        # Filter by aspect ratio
        if req.aspect_ratio == "landscape":
            results = [p for p in results if p.width == 0 or p.width >= p.height]
        elif req.aspect_ratio == "portrait":
            results = [p for p in results if p.width == 0 or p.height > p.width]
        elif req.aspect_ratio == "square":
            results = [p for p in results if p.width == 0 or abs(p.width - p.height) < (p.width * 0.1)]

        # Sorting
        if req.sort == "score":
            results.sort(key=lambda x: x.score, reverse=True)
        elif req.sort == "random":
            import random
            random.shuffle(results)

        # Deduplicate by file_url or id
        seen = set()
        deduped = []
        for p in results:
            key = (p.source, p.id)
            if key not in seen:
                seen.add(key)
                deduped.append(p)

        return {
            "posts": [p.to_dict() for p in deduped],
            "total": len(deduped),
            "page": req.page,
            "query": req.query,
            "source": req.source,
            "errors": errors
        }
