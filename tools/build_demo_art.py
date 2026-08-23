#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка арта для веб-демо: заливка-хромакей от краёв (не трогает внутренности
персонажа), обрезка, даунскейл, фон в JPEG, всё в base64 → prototype/index.html.
Запуск: python3 tools/build_demo_art.py"""
import base64, io, json, os, re, sys
from collections import deque

try:
    from PIL import Image
except ImportError:
    sys.exit("Нужен Pillow: pip install --break-system-packages pillow")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "prototype", "art", "raw")
PROC = os.path.join(ROOT, "prototype", "art", "proc")
HTML = os.path.join(ROOT, "prototype", "index.html")

SPRITES = {
    "hero_frank": 360, "hero_ash": 360, "hero_aimer": 360, "hero_cheney": 360,
    "hero_frank_walk2": 360, "hero_frank_atk": 360, "hero_frank_cast": 360,
    "hero_ash_walk2": 360, "hero_ash_atk": 360, "hero_ash_cast": 360,
    "hero_aimer_walk2": 360, "hero_aimer_atk": 360, "hero_aimer_cast": 360,
    "hero_cheney_walk2": 360, "hero_cheney_atk": 360, "hero_cheney_cast": 360,
    "boss_darklord_atk": 520, "boss_darklord_cast": 520,
    "mob_dreamling_atk": 270, "mob_sylph_atk": 270, "mob_kelpie_atk": 280, "mob_golem_atk": 300,
    "mob_dreamling": 270, "mob_sylph": 270, "mob_kelpie": 280, "mob_golem": 300,
    "boss_darklord": 520,
    # параллакс-слои мира
    "mid": 540,   # layer_mid.png — парящие острова
    "front": 460, # layer_front.png — платформа
}

def chroma_key(im):
    """Заливка от краёв: строго удаляем магенту, мягко — только кромку (3px)."""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    rm = bytearray(w * h)

    def strict(r, g, b):
        return r > 150 and b > 120 and g < 100 and (r + b - 2 * g) > 110

    def soft(r, g, b):
        return r > 120 and b > 100 and g < 90 and (r + b - 2 * g) > 70

    q = deque()
    def push(x, y, depth):
        i = y * w + x
        if rm[i]:
            return
        r, g, b, a = px[x, y]
        if strict(r, g, b) or (depth <= 3 and soft(r, g, b)):
            rm[i] = 1
            q.append((x, y, depth))

    for x in range(w):
        push(x, 0, 0)
        push(x, h - 1, 0)
    for y in range(h):
        push(0, y, 0)
        push(w - 1, y, 0)

    while q:
        x, y, depth = q.popleft()
        nd = depth + 1
        if x > 0: push(x - 1, y, nd)
        if x < w - 1: push(x + 1, y, nd)
        if y > 0: push(x, y - 1, nd)
        if y < h - 1: push(x, y + 1, nd)

    removed = 0
    for i in range(w * h):
        if rm[i]:
            x, y = i % w, i // w
            px[x, y] = (0, 0, 0, 0)
            removed += 1
    return im, removed / (w * h)

def opaque_share(im):
    a = im.getchannel("A")
    hist = a.histogram()
    opaque = sum(hist[128:])  # заметно непрозрачные
    return opaque / (im.size[0] * im.size[1])

def trim(im, pad=8):
    bbox = im.getbbox()
    if bbox:
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(im.size[0], bbox[2] + pad), min(im.size[1], bbox[3] + pad))
        im = im.crop(bbox)
    return im

os.makedirs(PROC, exist_ok=True)
out = {}
for name, target_h in SPRITES.items():
    path = os.path.join(RAW, ("layer_" + name if name in ("mid", "front") else name) + ".png")
    if not os.path.exists(path):
        print("НЕТ ФАЙЛА:", path)
        continue
    im = Image.open(path)
    im, removed_share = chroma_key(im)
    im = trim(im)
    scale = target_h / im.size[1]
    im = im.resize((max(1, round(im.size[0] * scale)), target_h), Image.LANCZOS)
    share = opaque_share(im)
    im.save(os.path.join(PROC, name + ".png"))  # превью для просмотра
    buf = io.BytesIO()
    try:  # палитровое сжатие: для мультяшного арта почти без потерь, минус 60% веса
        im = im.quantize(colors=192, method=Image.FASTOCTREE)
    except Exception:
        pass
    im.save(buf, "PNG", optimize=True)
    out[name] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    flag = "ок" if (0.10 <= share <= 0.92 or name in ("mid","front")) else ("ПРОВЕРИТЬ: почти всё вырезано?" if share < 0.10 else "много фона осталось?")
    print(f"{name}: {im.size[0]}x{im.size[1]}, вырезано фона {removed_share:.0%}, "
          f"персонаж занимает {share:.0%} кропа ({flag}), {len(out[name])//1024} КБ")

bg_path = os.path.join(RAW, "layer_sky.jpg")
if os.path.exists(bg_path):
    bg = Image.open(bg_path).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    buf = io.BytesIO()
    bg.save(buf, "JPEG", quality=80, optimize=True)
    out["sky"] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    print("sky:", len(out["sky"]) // 1024, "КБ")

print("Итого b64:", sum(len(v) for v in out.values()) // 1024, "КБ")

html = open(HTML, encoding="utf-8").read()
new_line = "const ART_B64 = " + json.dumps(out) + "; //__ART__"
if "const ART_B64 = {}; //__ART__" in html:
    html = html.replace("const ART_B64 = {}; //__ART__", new_line, 1)
else:
    html = re.sub(r"const ART_B64 = \{.*?\}; //__ART__", new_line, html, count=1, flags=re.S)
open(HTML, "w", encoding="utf-8").write(html)
print("index.html:", os.path.getsize(HTML) // 1024, "КБ")
