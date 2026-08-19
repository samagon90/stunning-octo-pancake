import json
from pathlib import Path
from typing import Dict, Any

SETTINGS_FILE = Path.home() / ".nsfw_image_searcher_config.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "download_dir": str(Path.home() / "Downloads" / "NSFW_Images"),
    "default_source": "adult_meta",
    "default_rating": "all",
    "naming_pattern": "{source}_{id}_{tags}",
    "create_subfolders": True,
    "skip_existing": True,
    "save_metadata": True,
    "threads": 4,
    "limit": 40,
    "theme": "dark"
}

def load_settings() -> Dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = dict(DEFAULT_SETTINGS)
                res.update(data)
                return res
        except Exception:
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)

def save_settings(settings: Dict[str, Any]) -> bool:
    try:
        current = load_settings()
        current.update(settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
