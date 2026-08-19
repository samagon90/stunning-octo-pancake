import re
import html
import urllib.parse
import aiohttp
import logging
from typing import List, Dict, Any
from core.models import Post

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.jfif')

async def extract_images_from_url(url: str, custom_headers: Dict[str, str] = None) -> List[Post]:
    """Fetch any web page or search URL and extract all full-resolution images."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": url
    }
    if custom_headers:
        headers.update(custom_headers)

    posts: List[Post] = []
    seen_urls = set()

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Fetch failed with status {resp.status} for {url}")
                    return []
                
                content = await resp.text()

                # 1. Search for JSON attributes with image URLs (e.g. Bing murl, Yandex img_href, Yahoo imgurl)
                json_img_matches = re.findall(r'["\'](?:murl|img_href|imgurl|originUrl|file_url|large_file_url|fullUrl)["\']\s*:\s*["\'](https?://[^"\']+)["\']', content)
                for raw_u in json_img_matches:
                    clean_u = html.unescape(raw_u).replace("\\/", "/")
                    if clean_u not in seen_urls:
                        seen_urls.add(clean_u)
                        posts.append(Post(
                            id=f"grab_{abs(hash(clean_u)) % 10000000}",
                            source="Page Grubber",
                            file_url=clean_u,
                            preview_url=clean_u,
                            sample_url=clean_u,
                            width=1920,
                            height=1080,
                            file_ext=clean_u.split(".")[-1].split("?")[0].lower() if "." in clean_u else "jpg",
                            tags=["captured_image"],
                            rating="explicit",
                            score=950,
                            source_page_url=url,
                            created_at="browser_capture"
                        ))

                # 2. Extract standard <img> tags with data-src, data-original, src
                img_tags = re.findall(r'<img[^>]+(?:data-src|data-original|data-full|data-highres|src)=[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                for raw_u in img_tags:
                    clean_u = html.unescape(raw_u).strip()
                    if clean_u.startswith("//"):
                        clean_u = "https:" + clean_u
                    elif clean_u.startswith("/"):
                        parsed = urllib.parse.urlparse(url)
                        clean_u = f"{parsed.scheme}://{parsed.netloc}{clean_u}"
                    
                    if not clean_u.startswith("http"):
                        continue
                    
                    # Filter out tiny icons / avatars
                    if any(bad in clean_u.lower() for bad in ["favicon", "icon", "logo", "pixel.gif", "spacer", "button"]):
                        continue

                    if clean_u not in seen_urls:
                        seen_urls.add(clean_u)
                        posts.append(Post(
                            id=f"grab_{abs(hash(clean_u)) % 10000000}",
                            source="Page Image",
                            file_url=clean_u,
                            preview_url=clean_u,
                            sample_url=clean_u,
                            width=1920,
                            height=1080,
                            file_ext=clean_u.split(".")[-1].split("?")[0].lower() if "." in clean_u else "jpg",
                            tags=["captured_image"],
                            rating="explicit",
                            score=900,
                            source_page_url=url,
                            created_at="browser_capture"
                        ))

                # 3. Extract <a> links that directly link to images
                a_tags = re.findall(r'<a[^>]+href=[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                for raw_u in a_tags:
                    clean_u = html.unescape(raw_u).strip()
                    if any(clean_u.lower().endswith(ext) or ext + "?" in clean_u.lower() for ext in IMAGE_EXTENSIONS):
                        if clean_u.startswith("//"):
                            clean_u = "https:" + clean_u
                        elif clean_u.startswith("/"):
                            parsed = urllib.parse.urlparse(url)
                            clean_u = f"{parsed.scheme}://{parsed.netloc}{clean_u}"
                        
                        if clean_u.startswith("http") and clean_u not in seen_urls:
                            seen_urls.add(clean_u)
                            posts.append(Post(
                                id=f"grab_{abs(hash(clean_u)) % 10000000}",
                                source="Direct Link",
                                file_url=clean_u,
                                preview_url=clean_u,
                                sample_url=clean_u,
                                width=1920,
                                height=1080,
                                file_ext=clean_u.split(".")[-1].split("?")[0].lower() if "." in clean_u else "jpg",
                                tags=["captured_image"],
                                rating="explicit",
                                score=980,
                                source_page_url=url,
                                created_at="browser_capture"
                            ))

    except Exception as e:
        logger.error(f"Error scraping images from {url}: {e}")

    return posts
