import os
import io
import zipfile
import asyncio
import aiohttp
from typing import Dict, Any, List
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response, StreamingResponse
from core.models import SearchRequest, DownloadRequest
from core.providers.manager import ProviderManager
from core.downloader import DownloadManager, get_referer_for_url
from core.tag_suggest import suggest_tags, POPULAR_TAGS
from core.settings import load_settings, save_settings
from core.scraper_engine import extract_images_from_url

app = FastAPI(title="NSFW Image Hunter & Downloader", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

provider_manager = ProviderManager()
download_manager = DownloadManager()

@app.get("/api/providers")
async def get_providers():
    providers = provider_manager.get_providers_list()
    return {"providers": providers}

@app.get("/api/search")
async def search_images(
    query: str = "",
    source: str = "adult_meta",
    page: int = 1,
    limit: int = 50,
    rating: str = "all",
    min_width: int = 0,
    min_height: int = 0,
    aspect_ratio: str = "all",
    sort: str = "recent"
):
    req = SearchRequest(
        query=query,
        source=source,
        page=page,
        limit=limit,
        rating=rating,
        min_width=min_width,
        min_height=min_height,
        aspect_ratio=aspect_ratio,
        sort=sort
    )
    result = await provider_manager.search(req)
    return result

@app.get("/api/extract-url")
async def extract_images_endpoint(url: str = Query(..., description="Target webpage URL to grab images from")):
    """Extract all full-size images from any website or search URL."""
    if not url:
        raise HTTPException(status_code=400, detail="Missing url")
    
    posts = await extract_images_from_url(url)
    return {
        "posts": [p.to_dict() for p in posts],
        "total": len(posts),
        "url": url,
        "errors": [] if posts else ["На указанной странице не удалось обнаружить изображения."]
    }

@app.get("/api/tags/suggest")
async def get_tag_suggestions(q: str = "", limit: int = 12):
    return {"suggestions": suggest_tags(q, limit=limit), "popular": POPULAR_TAGS[:20]}

@app.post("/api/download/start")
async def start_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    if download_manager.is_running:
        return JSONResponse(status_code=400, content={"error": "Загрузка уже выполняется"})
    
    background_tasks.add_task(
        download_manager.download_posts,
        posts=req.posts,
        destination_dir=req.destination_dir,
        naming_pattern=req.naming_pattern,
        create_subfolders=req.create_subfolders,
        subfolder_name=req.subfolder_name,
        skip_existing=req.skip_existing,
        save_metadata=req.save_metadata,
        threads=req.threads
    )
    return {"status": "started", "total": len(req.posts), "destination": req.destination_dir}

@app.get("/api/download/status")
async def download_status():
    return download_manager.get_stats()

@app.post("/api/download/cancel")
async def cancel_download():
    download_manager.cancel()
    return {"status": "cancelling"}

@app.post("/api/download/zip")
async def download_as_zip(req: DownloadRequest):
    """Download selected images as a ZIP archive for browser download."""
    if not req.posts:
        raise HTTPException(status_code=400, detail="Нет выбранных изображений")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            for post in req.posts:
                url = post.get("file_url") or post.get("sample_url") or post.get("preview_url")
                if not url or not url.startswith("http"):
                    continue
                
                filename = download_manager.format_filename(post, req.naming_pattern)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "Referer": get_referer_for_url(url),
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                }
                
                for attempt in range(2):
                    try:
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                if len(data) > 500:
                                    zip_file.writestr(filename, data)
                                    break
                    except Exception:
                        pass

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=images_collection.zip"}
    )

@app.get("/api/proxy-image")
async def proxy_image(url: str):
    """Image proxy to bypass CORS and anti-hotlinking."""
    if not url:
        raise HTTPException(status_code=400, detail="Missing url")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": get_referer_for_url(url),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "image/jpeg")
                    data = await resp.read()
                    return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})
    except Exception:
        pass
    
    # Return 1x1 transparent PNG if image is dead/offline (NEVER generate fake drawing)
    transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=transparent_png, media_type="image/png", status_code=200)

@app.get("/api/settings")
async def get_settings_endpoint():
    return load_settings()

@app.post("/api/settings")
async def update_settings_endpoint(settings: Dict[str, Any]):
    saved = save_settings(settings)
    return {"success": saved, "settings": load_settings()}

# Serve static files for web UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_server:app", host="0.0.0.0", port=8000, reload=True)
