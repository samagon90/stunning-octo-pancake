import re
import html
import urllib.parse
import aiohttp
import logging
from typing import List, Dict, Any
from core.models import Post

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.jfif')

def upgrade_to_highres_url(img_url: str) -> str:
    """Convert thumbnail URLs to full high-resolution image URLs where possible."""
    # Yandex avatar thumb to orig
    if "avatars.mds.yandex.net/get-images-cbir" in img_url:
        img_url = re.sub(r'/(?:[0-9a-z_]+)$', '/orig', img_url)
    elif "avatars.mds.yandex.net" in img_url:
        img_url = re.sub(r'/(?:x\d+|\d+x\d+|orig)$', '/orig', img_url)
    
    # Reddit preview to i.redd.it full
    if "preview.redd.it" in img_url:
        img_url = img_url.replace("preview.redd.it", "i.redd.it")
        img_url = img_url.split("?")[0]
        
    return img_url

async def extract_images_from_url(url: str, custom_headers: Dict[str, str] = None) -> List[Post]:
    """Fetch any webpage, gallery, search result, or album and extract ALL full-resolution images."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://google.com/"
    }
    if custom_headers:
        headers.update(custom_headers)

    posts: List[Post] = []
    seen_urls = set()

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Fetch status {resp.status} for {url}")
                    return []
                
                raw_content = await resp.text()
                content = html.unescape(raw_content)

                # 1. Search for JSON attributes with high-res image URLs (Bing murl, Yandex img_href, Yahoo imgurl, etc.)
                json_img_matches = re.findall(r'["\'](?:murl|img_href|imgurl|originUrl|file_url|large_file_url|fullUrl|thumbUrl|img_url|media_url)["\']\s*:\s*["\'](https?://[^"\']+)["\']', content)
                for raw_u in json_img_matches:
                    clean_u = raw_u.replace("\\/", "/").strip()
                    highres_u = upgrade_to_highres_url(clean_u)
                    
                    if highres_u not in seen_urls and not any(bad in highres_u.lower() for bad in ["favicon", "pixel.gif", "spacer", "logo"]):
                        seen_urls.add(highres_u)
                        posts.append(Post(
                            id=f"grab_{abs(hash(highres_u)) % 10000000}",
                            source="Page Image",
                            file_url=highres_u,
                            preview_url=clean_u,
                            sample_url=highres_u,
                            width=1920,
                            height=1080,
                            file_ext=highres_u.split(".")[-1].split("?")[0].lower() if "." in highres_u else "jpg",
                            tags=["captured_image"],
                            rating="explicit",
                            score=980,
                            source_page_url=url,
                            created_at="browser_capture"
                        ))

                # 2. Extract standard <img> tags with data-src, data-original, data-highres, src
                img_tags = re.findall(r'<img[^>]+(?:data-src|data-original|data-full|data-highres|data-zoom-src|src)=[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                for raw_u in img_tags:
                    clean_u = raw_u.strip()
                    if clean_u.startswith("//"):
                        clean_u = "https:" + clean_u
                    elif clean_u.startswith("/"):
                        parsed = urllib.parse.urlparse(url)
                        clean_u = f"{parsed.scheme}://{parsed.netloc}{clean_u}"
                    
                    if not clean_u.startswith("http"):
                        continue
                    
                    if any(bad in clean_u.lower() for bad in ["favicon", "icon", "logo", "pixel.gif", "spacer", "button", "avatar"]):
                        continue

                    highres_u = upgrade_to_highres_url(clean_u)
                    if highres_u not in seen_urls:
                        seen_urls.add(highres_u)
                        posts.append(Post(
                            id=f"grab_{abs(hash(highres_u)) % 10000000}",
                            source="Web Image",
                            file_url=highres_u,
                            preview_url=clean_u,
                            sample_url=highres_u,
                            width=1920,
                            height=1080,
                            file_ext=highres_u.split(".")[-1].split("?")[0].lower() if "." in highres_u else "jpg",
                            tags=["captured_image"],
                            rating="explicit",
                            score=920,
                            source_page_url=url,
                            created_at="browser_capture"
                        ))

                # 3. Extract <a> direct links to images and google imgurl
                google_imgurls = re.findall(r'imgurl=(https?://[^&"\'\s]+)', content)
                for raw_u in google_imgurls:
                    clean_u = urllib.parse.unquote(raw_u)
                    if clean_u.startswith("http") and clean_u not in seen_urls and "gstatic.com" not in clean_u:
                        seen_urls.add(clean_u)
                        posts.append(Post(
                            id=f"grab_{abs(hash(clean_u)) % 10000000}",
                            source="Google Image",
                            file_url=clean_u,
                            preview_url=clean_u,
                            sample_url=clean_u,
                            width=1920,
                            height=1080,
                            file_ext=clean_u.split(".")[-1].split("?")[0].lower() if "." in clean_u else "jpg",
                            tags=["captured_image"],
                            rating="explicit",
                            score=990,
                            source_page_url=url,
                            created_at="browser_capture"
                        ))

    except Exception as e:
        logger.error(f"Error scraping images from {url}: {e}")

    return posts
