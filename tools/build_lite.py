#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Лайт-сборка: index.html БЕЗ встроенного арта (векторный режим).
Итог: ~100 КБ вместо 10 МБ — для слабых устройств и старых браузеров."""
import io, re, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = io.open(os.path.join(ROOT, "prototype", "index.html"), encoding="utf-8").read()

# 1) убрать весь арт (одна огромная строка)
src = re.sub(r"const ART_B64 = \{.*?\}; //__ART__", "const ART_B64 = {}; //__ART__ (лайт: без арта)", src, count=1, flags=re.S)
assert "__ART__ (лайт" in src

# 2) версия + мгновенный векторный режим
src = re.sub(r"const GAME_VERSION = 'v\\d+[^']*';", "const GAME_VERSION = 'v14-LITE';", src, count=1)
src = src.replace("let VEC = false;", "let VEC = true; // лайт: всегда вектор")

# 3) подвал меню
src = src.replace("Полная версия — Unity: 9 миров, 14 героев, арена, гача, чат • веб-демо ",
                  "ЛАЙТ-СБОРКА (вектор) • полная со спрайтами — index.html • ")

out = os.path.join(ROOT, "prototype", "index-lite.html")
io.open(out, "w", encoding="utf-8").write(src)
print("index-lite.html:", os.path.getsize(out) // 1024, "КБ")
