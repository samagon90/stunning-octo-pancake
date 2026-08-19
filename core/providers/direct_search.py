import re
import html
import urllib.parse
import aiohttp
import logging
from typing import List
from core.models import Post

logger = logging.getLogger(__name__)

async def search_google_gbv(query: str, limit: int = 40) -> List[Post]:
    """Search Google Images using the reliable gbv=1 basic HTML endpoint."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_q}&tbm=isch&gbv=1&hl=ru&gl=ru"
    
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
                    # Google with gbv=1 has links like href="/imgres?imgurl=https://...&imgrefurl=..."
                    matches = re.findall(r'href=[\'"]/imgres\?imgurl=([^&\'"]+)&(?:amp;)?imgrefurl=([^&\'"]+)', text)
                    for raw_imgurl, raw_ref in matches:
                        try:
                            img_url = urllib.parse.unquote(raw_imgurl)
                            ref_url = urllib.parse.unquote(raw_ref)
                            
                            if not img_url.startswith("http") or "gstatic.com" in img_url or "google.com" in img_url:
                                continue
                            
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
                                source_page_url=ref_url,
                                created_at="google"
                            )
                            posts.append(post)
                            if len(posts) >= limit:
                                break
                        except Exception:
                            continue
    except Exception as e:
        logger.warning(f"Google gbv error: {e}")
        
    return posts

async def search_yandex_touch(query: str, limit: int = 40) -> List[Post]:
    """Search Yandex Images using the mobile/touch endpoint (avoids SmartCaptcha)."""
    posts = []
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://yandex.ru/images/touch/search?text={encoded_q}&nomisspell=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://yandex.ru/"
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Extract data-bem json from mobile serp items
                    matches = re.findall(r'data-bem=[\'"](.*?)[\'"]', text)
                    for raw_bem in matches:
                        try:
                            unescaped = html.unescape(raw_bem)
                            data = json.loads(unescaped)
                            serp = data.get("serp-item", {})
                            
                            # Origin or preview or thumbUrl
                            img_url = serp.get("origin", {}).get("url") or serp.get("thumbUrl")
                            if not img_url:
                                prevs = serp.get("preview", [])
                                if prevs and isinstance(prevs, list):
                                    img_url = prevs[0].get("url")
                            
                            if not img_url or not img_url.startswith("http"):
                                continue

                            # If thumb is protocol-relative
                            if img_url.startswith("//"):
                                img_url = "https:" + img_url

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
                                source_page_url=serp.get("snippet", {}).get("url", img_url),
                                created_at="yandex"
                            )
                            posts.append(post)
                            if len(posts) >= limit:
                                break
                        except Exception:
                            continue
    except Exception as e:
        logger.warning(f"Yandex touch error: {e}")
        
    return posts

async def search_bing_direct(query: str, limit: int = 40) -> List[Post]:
    """Search Bing Images with exact query (NO 'model' keyword appended)."""
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
        logger.warning(f"Bing direct error: {e}")
        
    return posts
