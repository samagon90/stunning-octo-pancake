import asyncio
import logging
from typing import Dict, List, Optional, Any
from core.models import Post, SearchRequest
from core.translit import is_cyrillic, expand_query_for_booru, transliterate
from core.providers.base import BaseProvider
from core.providers.adult_meta import AdultMetaSearchProvider
from core.providers.coomer import CoomerModelProvider
from core.providers.erome import EroMeProvider
from core.providers.universal_search import UniversalWebSearchProvider
from core.providers.web_engines import search_bing_async, search_yahoo_images
from core.providers.reddit import RedditImageProvider
from core.providers.realbooru import RealbooruProvider
from core.providers.rule34 import Rule34Provider
from core.providers.gelbooru import GelbooruProvider
from core.providers.danbooru import DanbooruProvider
from core.providers.yandere import YandereProvider
from core.providers.konachan import KonachanProvider
from core.providers.safebooru import SafebooruProvider
from core.providers.waifu_im import WaifuImProvider
from core.providers.mock_provider import MockProvider

logger = logging.getLogger(__name__)

class ProviderManager:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "adult_meta": AdultMetaSearchProvider(),
            "coomer": CoomerModelProvider(),
            "erome": EroMeProvider(),
            "web": UniversalWebSearchProvider(),
            "reddit": RedditImageProvider(),
            "realbooru": RealbooruProvider(),
            "rule34": Rule34Provider(),
            "gelbooru": GelbooruProvider(),
            "danbooru": DanbooruProvider(),
            "yandere": YandereProvider(),
            "konachan": KonachanProvider(),
            "waifu_im": WaifuImProvider(),
            "safebooru": SafebooruProvider(),
            "demo": MockProvider()
        }

    def get_providers_list(self) -> List[Dict[str, str]]:
        return [
            {"id": "adult_meta", "name": "👑 ПОИСК МОДЕЛЕЙ И ФОТОСЕТОВ 18+ (Coomer + OnlyFans + EroMe + Bing + Reddit)"},
            {"id": "coomer", "name": "⭐ Coomer / OnlyFans / Fansly (Архив моделей)"},
            {"id": "erome", "name": "🔥 EroMe (Альбомы и фотосеты)"},
            {"id": "web", "name": "🌐 Поиск в интернете (Яндекс, Bing, Yahoo, DuckDuckGo)"},
            {"id": "reddit", "name": "🔴 Reddit (NSFW, Косплей, Фото)"},
            {"id": "realbooru", "name": "Realbooru (Косплей и реальные фото)"},
            {"id": "all", "name": "✨ Все источники сразу"},
            {"id": "rule34", "name": "Rule34 (xxx)"},
            {"id": "gelbooru", "name": "Gelbooru (Аниме)"},
            {"id": "danbooru", "name": "Danbooru"},
            {"id": "yandere", "name": "Yande.re (4K обои)"},
            {"id": "konachan", "name": "Konachan"},
            {"id": "waifu_im", "name": "Waifu.im (AI и Аниме)"},
            {"id": "safebooru", "name": "Safebooru (Safe)"},
            {"id": "demo", "name": "Демо-режим (Offline)"}
        ]

    async def search(self, req: SearchRequest) -> Dict[str, Any]:
        source = req.source.lower()
        results: List[Post] = []
        errors: List[str] = []

        query = req.query.strip()
        booru_query = expand_query_for_booru(query) if is_cyrillic(query) else query

        if source in ("adult_meta", "meta", "web", "all"):
            # Use multi-engine adult aggregator
            active_provider = self.providers.get(source) or self.providers["adult_meta"]
            try:
                results = await active_provider.search(query, req.page, req.limit, req.rating)
            except Exception as e:
                errors.append(f"Ошибка поиска: {str(e)}")

            # If booru requested in all
            if source == "all":
                try:
                    booru_res = await self.providers["realbooru"].search(booru_query, req.page, req.limit // 2, req.rating)
                    results.extend(booru_res)
                except Exception:
                    pass
            
            if not results and not errors:
                errors.append(f"По запросу '{query}' ничего не найдено. Попробуйте написать имя на латинице (например: {transliterate(query)}) или выбрать другой источник.")
        else:
            provider = self.providers.get(source)
            if not provider:
                provider = self.providers["adult_meta"]
            
            active_q = query if provider.name in ("adult_meta", "coomer", "erome", "web", "universal_web", "reddit") else booru_query
            
            try:
                results = await provider.search(active_q, req.page, req.limit, req.rating)
            except Exception as e:
                errors.append(f"Ошибка источника {provider.display_name}: {str(e)}")
                # Try fallback to adult_meta
                try:
                    fallback_res = await self.providers["adult_meta"].search(query, req.page, req.limit, req.rating)
                    results.extend(fallback_res)
                except Exception:
                    pass

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

        # Deduplicate by file_url
        seen = set()
        deduped = []
        for p in results:
            if p.file_url and p.file_url not in seen:
                seen.add(p.file_url)
                deduped.append(p)

        return {
            "posts": [p.to_dict() for p in deduped],
            "total": len(deduped),
            "page": req.page,
            "query": req.query,
            "source": req.source,
            "errors": errors
        }
