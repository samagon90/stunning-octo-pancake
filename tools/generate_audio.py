#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор звуков Dream Masters Revival: 8-bit-духовые SFX + эмбиент-луп.
Чистый Python (wave/math), без зависимостей. Выход: unity-project/Assets/Resources/Audio/*.wav"""
import math, os, struct, wave, random

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "unity-project", "Assets", "Resources", "Audio")
random.seed(20150815)  # дата русского релиза оригинала :)

def save(name, samples):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(s * 32767)))) for s in samples))
    print("OK", name, len(samples) / SR, "c")

def env(i, n, a=0.01, r=0.3):
    """ATK-REL огибающая."""
    t = i / n
    at = min(1.0, t / max(a, 1e-6))
    re = max(0.0, (1.0 - t) / max(r, 1e-6))
    return at * min(1.0, re)

def tone(freq, dur, vol=0.5, wave_fn=math.sin, vib=0.0):
    n = int(SR * dur); out = []
    for i in range(n):
        t = i / SR
        f = freq * (1 + vib * math.sin(2 * math.pi * 5 * t))
        out.append(vol * env(i, n) * wave_fn(2 * math.pi * f * t))
    return out

def noise(dur, vol=0.4, lp=0.3):
    n = int(SR * dur); out = []; prev = 0.0
    for i in range(n):
        prev = prev * lp + (1 - lp) * random.uniform(-1, 1)
        out.append(vol * env(i, n, a=0.005, r=0.5) * prev)
    return out

def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]

def seq(pauses, *parts):
    out = []
    for p in parts: out += p + [0.0] * pauses
    return out

saw = lambda x: 2 * ((x / (2 * math.pi)) % 1) - 1
square = lambda x: 1.0 if (x / (2 * math.pi)) % 1 < 0.5 else -1.0

# Клики UI
save("Click", tone(880, 0.07, 0.35, square))
# Попадание: шум + низкий удар
save("Hit", mix(noise(0.12, 0.45, lp=0.25), tone(120, 0.12, 0.5)))
# Крит: попадание + высокий звон
save("Crit", mix(noise(0.16, 0.4, lp=0.2), tone(120, 0.16, 0.5), tone(1320, 0.18, 0.25, vib=0.02)))
# Каст умения: восходящий свип
n = int(SR * 0.22); sweep = []
for i in range(n):
    f = 260 + 900 * (i / n) ** 1.6
    sweep.append(0.35 * env(i, n) * math.sin(2 * math.pi * f * (i / SR)))
save("Cast", sweep)
# Лечение: две ноты вверх
save("Heal", seq(60, tone(523, 0.12, 0.3), tone(784, 0.18, 0.3)))
# Победа: мажорная арпеджиата C-E-G-C
save("Victory", seq(90, *[tone(f, 0.16, 0.32, square) for f in (523, 659, 784, 1046)]))
# Поражение: минорный спуск
save("Defeat", seq(110, *[tone(f, 0.22, 0.3, saw) for f in (392, 330, 262)]))
# Рёв босса: низкий пила-свип вниз
n = int(SR * 0.5); roar = []
for i in range(n):
    f = 180 - 110 * (i / n)
    roar.append(0.45 * env(i, n, a=0.05, r=0.5) * saw(2 * math.pi * f * (i / SR)))
save("BossRoar", mix(roar, noise(0.5, 0.15, lp=0.1)))

# Музыка: эмбиент-луп «Сон» ~12 c — аккордовое дыхание (Am → F → C → G)
def pad(freqs, dur, vol=0.08):
    n = int(SR * dur); out = []
    for i in range(n):
        t = i / SR
        lfo = 0.6 + 0.4 * math.sin(2 * math.pi * 0.12 * t)
        out.append(vol * lfo * sum(math.sin(2 * math.pi * f * t + k) for k, f in enumerate(freqs)) / len(freqs))
    return out

chords = [
    (220.0, 261.63, 329.63),   # Am
    (174.61, 220.0, 261.63),   # F
    (196.0, 261.63, 329.63),   # C(низкий G)
    (196.0, 246.94, 293.66),   # G
]
music = []
fade = int(SR * 0.8)
for c in chords:
    block = pad(c, 3.0)
    for i in range(fade):  # кроссфейд между аккордами
        k = i / fade
        if i < len(block): block[i] *= k
        if len(music) - fade + i >= 0 and len(music) - fade + i < len(music) and i < len(block):
            music[len(music) - fade + i] += block[i] * (1 - k) * 0  # простое наложение
    music += block
# выравнивание громкости и мягкое начало/конец для бесшовного лупа
peak = max(abs(s) for s in music) or 1.0
music = [s / peak * 0.55 for s in music]
save("music_dream", music)

print("Готово:", sorted(os.listdir(OUT)))
