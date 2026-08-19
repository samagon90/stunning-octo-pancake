from typing import List, Dict

POPULAR_TAGS = [
    # General / Composition
    "solo", "1girl", "2girls", "3girls", "female", "highres", "absurdres", "masterpiece",
    "looking_at_viewer", "smile", "blush", "open_mouth", "closed_eyes",
    "long_hair", "short_hair", "twintails", "ponytail", "blonde_hair", "black_hair", 
    "blue_hair", "silver_hair", "white_hair", "pink_hair", "red_hair", "brown_hair",
    "blue_eyes", "red_eyes", "green_eyes", "purple_eyes", "yellow_eyes",
    
    # Clothing / Outfit
    "bikini", "swimsuit", "micro_bikini", "lingerie", "underwear", "panties", "bra",
    "stockings", "thighhighs", "pantyhose", "garter_straps", "cleavage",
    "maid", "school_uniform", "bunny_suit", "bunny_ears", "dress", "skirt",
    "collar", "choker", "leotard", "bodysuit", "latex", "kimono", "yukata",
    
    # Anatomy / Pose
    "breasts", "large_breasts", "medium_breasts", "huge_breasts", "cleavage", "nipples",
    "ass", "butt", "thighs", "wide_hips", "navel", "bare_shoulders",
    "nude", "completely_nude", "topless", "bottomless", "side_view", "back_view",
    "from_behind", "lying", "on_back", "on_stomach", "sitting", "kneeling", "standing",
    "all_fours", "bent_over", "spread_legs", "spread_pussy", "cameltoe",
    
    # Styles & Themes
    "wallpaper", "digital_art", "4k", "photorealistic", "anime", "cg", "fantasy",
    "cyberpunk", "aesthetic", "neon", "gothic", "sensual", "dark_skin", "tan",
    
    # Filter / Search modifiers
    "rating:explicit", "rating:questionable", "rating:safe", "rating:sensitive",
    "score:>100", "score:>500", "score:>1000", "width:>1920", "height:>1080",
    "order:score", "order:rank", "order:favcount",
    "-male", "-furry", "-3d", "-yaoi", "-guro"
]

def suggest_tags(query: str, limit: int = 10) -> List[str]:
    """Suggest matching tags for query."""
    if not query:
        return POPULAR_TAGS[:limit]
    
    # Get last word typed
    tokens = query.strip().split()
    current_token = tokens[-1].lower() if tokens else ""
    
    if not current_token:
        return POPULAR_TAGS[:limit]

    matches = [t for t in POPULAR_TAGS if current_token in t.lower()]
    # Sort matches: exact start first
    matches.sort(key=lambda x: (not x.lower().startswith(current_token), len(x)))
    return matches[:limit]
