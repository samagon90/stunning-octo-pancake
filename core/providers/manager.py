import asyncio
import logging
from typing import Dict, List, Optional, Any
from core.models import Post, SearchRequest
from core.translit import is_cyrillic, expand_query_for_booru, transliterate
from core.providers.base import BaseProvider
from core.providers.meta_search import MetaSearchProvider
from core.providers.yandex import YandexImageProvider
from core.providers.bing import BingImageProvider
from core.providers.google import GoogleImageProvider
from core.providers.duckduckgo_images import DuckDuckGoImageProvider
from core.providers.reddit import RedditImageProvider
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
            "meta": MetaSearchProvider(),
            "yandex": YandexImageProvider(),
            "bing": BingImageProvider(),
            "google": GoogleImageProvider(),
            "duckduckgo": DuckDuckGoImageProvider(),
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
            {"id": "meta", "name": "🚀 ВСЕ ПОИСКОВИКИ ВМЕСТЕ (Яндекс + Bing + Google + Reddit + DuckDuckGo)"},
            {"id": "yandex", "name": "🇷🇺 Яндекс Картинки (Лучший поиск по моделям и именам)"},
            {"id": "bing", "name": "🌐 Bing Картинки (Без цензуры 18+)"},
            {"id": "google", "name": "🔍 Google Картинки"},
            {"id": "duckduckgo", "name": "🦆 DuckDuckGo Картинки"},
            {"id": "reddit", "name": "🔴 Reddit (Косплей, Фото, NSFW)"},
            {"id": "all", "name": "✨ Все поисковики + Все Booru сразу"},
            {"id": "realbooru", "name": "Realbooru (Косплей и реальные фото)"},
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

        if source == "all":
            # Search across Meta Search (Yandex+Bing+Google+Reddit) + Boorus simultaneously
            active_tasks = [
                self.providers["meta"].search(query, req.page, req.limit, req.rating),
                self.providers["realbooru"].search(booru_query, req.page, req.limit // 2, req.rating),
                self.providers["rule34"].search(booru_query, req.page, req.limit // 2, req.rating),
                self.providers["gelbooru"].search(booru_query, req.page, req.limit // 2, req.rating)
            ]
            
            gathered = await asyncio.gather(*active_tasks, return_exceptions=True)
            for res in gathered:
                if isinstance(res, list):
                    results.extend(res)
                elif isinstance(res, Exception):
                    errors.append(str(res))
            
            if not results:
                demo_res = await self.providers["demo"].search(query or "model", req.page, req.limit, req.rating)
                results.extend(demo_res)
                errors.append("Внимание: внешняя сеть недоступна, показаны демонстрационные результаты.")
        else:
            provider = self.providers.get(source)
            if not provider:
                provider = self.providers["meta"]
            
            # Use appropriate query
            active_q = query if provider.name in ("meta", "yandex", "bing", "google", "duckduckgo", "reddit") else booru_query
            
            try:
                results = await provider.search(active_q, req.page, req.limit, req.rating)
            except Exception as e:
                errors.append(f"Ошибка источника {provider.display_name}: {str(e)}")
                # If a specific search engine failed, try meta search or yandex
                if provider.name != "meta":
                    try:
                        fallback_res = await self.providers["meta"].search(query, req.page, req.limit, req.rating)
                        results.extend(fallback_res)
                    except Exception:
                        pass
                
                if not results:
                    demo_res = await self.providers["demo"].search(query or "model", req.page, req.limit, req.rating)
                    results.extend(demo_res)
                    errors.append("Показаны демонстрационные результаты.")

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
