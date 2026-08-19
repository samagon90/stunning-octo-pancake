import re
import html
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post

logger = logging.getLogger(__name__)

async def search_bing_direct(query: str, page: int = 1, limit: int = 50) -> List[Post]:
    """Search Bing Images with proper pagination offset."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    first_idx = (page - 1) * limit + 1
    url = f"https://www.bing.com/images/async?q={encoded_q}&first={first_idx}&count={limit}&mmasync=1&adlt=off"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.bing.com/",
        "Cookie": "SRCHHPGUSR=ADLT=OFF&NRSLT=50; _EDGE_S=F=1;"
    }
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    raw_text = await resp.text()
                    clean_text = html.unescape(raw_text)
                    
                    murls = re.findall(r'"murl"\s*:\s*"(https?://[^"]+)"', clean_text)
                    turls = re.findall(r'"turl"\s*:\s*"(https?://[^"]+)"', clean_text)
                    descs = re.findall(r'"desc"\s*:\s*"([^"]+)"', clean_text)
                    
                    seen = set()
                    for idx, murl in enumerate(murls):
                        if murl in seen or not murl.startswith("http"):
                            continue
                        seen.add(murl)
                        
                        thumb = turls[idx] if idx < len(turls) else murl
                        desc = descs[idx] if idx < len(descs) else query
                        
                        post = Post(
                            id=f"bing_{abs(hash(murl)) % 10000000}",
                            source="Bing",
                            file_url=murl,
                            preview_url=thumb,
                            sample_url=murl,
                            width=1920,
                            height=1080,
                            file_ext=murl.split(".")[-1].split("?")[0].lower() if "." in murl else "jpg",
                            tags=[t for t in re.findall(r'[\w\-]+', f"{query} {desc}".lower()) if len(t) > 2][:8],
                            rating="explicit",
                            score=950,
                            source_page_url=murl,
                            created_at=f"bing_p{page}"
                        )
                        posts.append(post)
                        if len(posts) >= limit:
                            break
    except Exception as e:
        logger.warning(f"Bing search error: {e}")
        
    return posts

async def search_yahoo_direct(query: str, page: int = 1, limit: int = 50) -> List[Post]:
    """Search Yahoo Images with proper pagination offset."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    start_idx = (page - 1) * limit + 1
    url = f"https://images.search.yahoo.com/search/images?p={encoded_q}&b={start_idx}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    raw_text = await resp.text()
                    clean_text = html.unescape(raw_text)
                    
                    imgurls = re.findall(r'"imgurl"\s*:\s*"(https?://[^"]+)"', clean_text)
                    thurls = re.findall(r'"th"\s*:\s*"(https?://[^"]+)"', clean_text)
                    titles = re.findall(r'"tit"\s*:\s*"([^"]+)"', clean_text)
                    
                    seen = set()
                    for idx, img_url in enumerate(imgurls):
                        if img_url in seen or not img_url.startswith("http"):
                            continue
                        seen.add(img_url)
                        
                        thumb = thurls[idx] if idx < len(thurls) else img_url
                        tit = titles[idx] if idx < len(titles) else query
                        
                        post = Post(
                            id=f"yahoo_{abs(hash(img_url)) % 10000000}",
                            source="Yahoo",
                            file_url=img_url,
                            preview_url=thumb,
                            sample_url=img_url,
                            width=1920,
                            height=1080,
                            file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                            tags=[t for t in re.findall(r'[\w\-]+', f"{query} {tit}".lower()) if len(t) > 2][:8],
                            rating="explicit",
                            score=900,
                            source_page_url=img_url,
                            created_at=f"yahoo_p{page}"
                        )
                        posts.append(post)
                        if len(posts) >= limit:
                            break
    except Exception as e:
        logger.warning(f"Yahoo search error: {e}")
        
    return posts

async def search_google_gbv(query: str, page: int = 1, limit: int = 50) -> List[Post]:
    """Search Google Images with pagination."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    start_idx = (page - 1) * limit
    url = f"https://www.google.com/search?q={encoded_q}&tbm=isch&gbv=1&hl=ru&gl=ru&start={start_idx}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    raw_text = await resp.text()
                    clean_text = html.unescape(raw_text)
                    
                    imgurls = re.findall(r'imgurl=(https?://[^&"\'\s]+)', clean_text)
                    seen = set()
                    for raw_u in imgurls:
                        img_url = urllib.parse.unquote(raw_u)
                        if img_url in seen or "gstatic.com" in img_url or "google.com" in img_url:
                            continue
                        seen.add(img_url)
                        
                        post = Post(
                            id=f"google_{abs(hash(img_url)) % 10000000}",
                            source="Google",
                            file_url=img_url,
                            preview_url=img_url,
                            sample_url=img_url,
                            width=1920,
                            height=1080,
                            file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                            tags=[query],
                            rating="explicit",
                            score=960,
                            source_page_url=img_url,
                            created_at=f"google_p{page}"
                        )
                        posts.append(post)
                        if len(posts) >= limit:
                            break
    except Exception as e:
        logger.warning(f"Google error: {e}")
        
    return posts

async def search_yandex_touch(query: str, page: int = 1, limit: int = 50) -> List[Post]:
    """Search Yandex Images mobile/touch endpoint with pagination."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    p_offset = page - 1
    url = f"https://yandex.ru/images/touch/search?text={encoded_q}&p={p_offset}&nomisspell=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://yandex.ru/"
    }
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    raw_text = await resp.text()
                    clean_text = html.unescape(raw_text)
                    
                    urls = re.findall(r'"(?:originUrl|thumbUrl|img_href)"\s*:\s*"(https?://[^"]+)"', clean_text)
                    seen = set()
                    for img_url in urls:
                        if img_url in seen:
                            continue
                        seen.add(img_url)
                        
                        post = Post(
                            id=f"yandex_{abs(hash(img_url)) % 10000000}",
                            source="Яндекс",
                            file_url=img_url,
                            preview_url=img_url,
                            sample_url=img_url,
                            width=1920,
                            height=1080,
                            file_ext=img_url.split(".")[-1].split("?")[0].lower() if "." in img_url else "jpg",
                            tags=[query],
                            rating="explicit",
                            score=980,
                            source_page_url=img_url,
                            created_at=f"yandex_p{page}"
                        )
                        posts.append(post)
                        if len(posts) >= limit:
                            break
    except Exception as e:
        logger.warning(f"Yandex touch error: {e}")
        
    return posts
