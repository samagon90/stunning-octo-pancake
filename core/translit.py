import re

RU_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def transliterate(text: str) -> str:
    """Transliterate Russian text to Latin (e.g. милена лисицына -> milena lisitsyna)."""
    res = []
    for ch in text.lower():
        if ch in RU_TO_LAT:
            res.append(RU_TO_LAT[ch])
        else:
            res.append(ch)
    return "".join(res)

def is_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters."""
    return bool(re.search(r'[а-яА-ЯёЁ]', text))

def expand_query_for_booru(query: str) -> str:
    """Format query for Booru engines (underscore-joined tags and latin conversion)."""
    if not query:
        return ""
    
    clean = query.strip()
    if is_cyrillic(clean):
        latin = transliterate(clean)
        # Convert spaces to underscores for names
        words = latin.split()
        if len(words) >= 2:
            return f"{'_'.join(words)} {' '.join(words)}"
        return latin
    return clean
