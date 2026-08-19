import urllib.parse
import aiohttp
import re
import json
import html
import logging
from typing import List
from core.models import Post

logger = logging.getLogger(__name__)

async def search_bing_async(query: str, limit: int = 40) -> List[Post]:
    """Search Bing Images using the async endpoint (most reliable scraper)."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.bing.com/images/async?q={encoded_q}&first=1&count={limit}&mmasync=1&adlt=off"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.bing.com/",
        "Cookie": "SRCHHPGUSR=ADLT=OFF&NRSLT=50;"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Find all m="{...}" attributes
                    matches = re.findall(r'm=[\'"](\{[^>]+?\})[\'"]', text)
                    for raw_m in matches:
                        try:
                            unescaped = html.unescape(raw_m)
                            data = json.loads(unescaped)
                            murl = data.get("murl")
                            if not murl or not murl.startswith("http"):
                                continue
                            
                            turl = data.get("turl") or murl
                            desc = data.get("desc", "") or data.get("t", "") or query
                            purl = data.get("purl", murl)
                            w = int(data.get("w", 0) or data.get("ow", 1920))
                            h = int(data.get("h", 0) or data.get("oh", 1080))
                            
                            post = Post(
                                id=f"bing_{abs(hash(murl)) % 10000000}",
                                source="Bing",
                                file_url=murl,
                                preview_url=turl,
                                sample_url=murl,
                                width=w,
                                height=h,
                                file_ext=murl.split(".")[-1].split("?")[0].lower() if "." in murl else "jpg",
                                tags=[t for t in re.findall(r'[\w\-]+', f"{query} {desc}".lower()) if len(t) > 2][:8],
                                rating="explicit",
                                score=950,
                                source_page_url=purl,
                                created_at="bing"
                            )
                            posts.append(post)
                            if len(posts) >= limit:
                                break
                        except Exception:
                            continue
    except Exception as e:
        logger.warning(f"Bing async error: {e}")
        
    return posts

async def search_yahoo_images(query: str, limit: int = 40) -> List[Post]:
    """Search Yahoo Images."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://images.search.yahoo.com/search/images?p={encoded_q}&b=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Find all class="ld" and data attributes
                    matches = re.findall(r'class="ld"[^>]*>([^<]+)<', text)
                    for raw_json in matches:
                        try:
                            unescaped = html.unescape(raw_json)
                            data = json.loads(unescaped)
                            imgurl = data.get("imgurl")
                            if not imgurl or not imgurl.startswith("http"):
                                continue
                            
                            th = data.get("th") or imgurl
                            tit = data.get("tit", "") or query
                            rurl = data.get("rurl", imgurl)
                            w = int(data.get("w", 1920) or 1920)
                            h = int(data.get("h", 1080) or 1080)
                            
                            post = Post(
                                id=f"yahoo_{abs(hash(imgurl)) % 10000000}",
                                source="Yahoo",
                                file_url=imgurl,
                                preview_url=th,
                                sample_url=imgurl,
                                width=w,
                                height=h,
                                file_ext=imgurl.split(".")[-1].split("?")[0].lower() if "." in imgurl else "jpg",
                                tags=[t for t in re.findall(r'[\w\-]+', f"{query} {tit}".lower()) if len(t) > 2][:8],
                                rating="explicit",
                                score=900,
                                source_page_url=rurl,
                                created_at="yahoo"
                            )
                            posts.append(post)
                            if len(posts) >= limit:
                                break
                        except Exception:
                            continue
    except Exception as e:
        logger.warning(f"Yahoo search error: {e}")
        
    return posts
