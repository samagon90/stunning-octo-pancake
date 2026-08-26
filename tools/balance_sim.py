#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Симулятор баланса Dream Masters Revival.
Воспроизводит формулы урона/статов из C# (HeroInstance.ComputeStats + DamageCalculator)
и простую модель боя (DPS-гонка с учётом стихий), чтобы проверить кривую сложности
135 уровней и подобрать нужный уровень героев. Запуск: python3 tools/balance_sim.py"""
import math

# ---------- Формулы из кода (держать в синхроне!) ----------
ELEMENT_ADV, ELEMENT_DIS = 1.25, 0.80
DOMINATES = lambda e: (e + 1) % 4  # Fire>Air>Earth>Water>Fire

def element_mult(a, d):
    if DOMINATES(a) == d: return ELEMENT_ADV
    if DOMINATES(d) == a: return ELEMENT_DIS
    return 1.0

def hero_stats(base, level, stars=1, rank=0, awakened=False):
    mult = (1 + (level - 1) * 0.10) * (1 + (stars - 1) * 0.15) * (1 + rank * 0.12) * (2.0 if awakened else 1.0)
    return {"hp": base["hp"] * mult, "atk": base["atk"] * mult, "def": base["def"] * mult,
            "spd": base["spd"], "crit": base["crit"]}

def damage(atk, dfn, coeff, ea, ed, crit):
    raw = atk * coeff * element_mult(ea, ed)
    mit = raw * (100 / (100 + max(0, dfn)))
    return max(1.0, mit * (1.5 if crit else 1.0))

# ---------- Контент (копия generate_content.py) ----------
HEROES = {
    "ash":     {"hp": 900,  "atk": 150, "def": 50,  "spd": 1.10, "crit": 0.15, "el": 0},
    "frank":   {"hp": 1600, "atk": 90,  "def": 110, "spd": 0.80, "crit": 0.05, "el": 2},
    "aimer":   {"hp": 800,  "atk": 100, "def": 40,  "spd": 0.90, "crit": 0.05, "el": 3},
    "cheney":  {"hp": 950,  "atk": 135, "def": 45,  "spd": 1.00, "crit": 0.12, "el": 3},
}
SYNERGY_ATK = 0.20  # Эш+Чейни

MOB_BASE = {"dreamling": (380, 55, 20), "sylph": (340, 62, 15), "golem": (600, 48, 35), "kelpie": (420, 58, 18)}
TIERS = {"dreamling": 5, "sylph": 3, "golem": 3, "kelpie": 3}
FAM_OF_ELEMENT = {0: "dreamling", 1: "sylph", 2: "golem", 3: "kelpie"}
MASTERS = {2: "yun", 3: "nuwa", 4: "zeus", 5: "shaman", 6: "tripitaka", 7: "electra", 8: "tetra", 9: "liang"}
WORLD_ELEMENT = {1: 0, 2: 3, 3: 2, 4: 1, 5: 0, 6: 2, 7: 1, 8: 3, 9: 0}

def mob_stats(fam, t):
    hp, atk, dfn = MOB_BASE[fam]
    return {"hp": hp * 1.35 ** (t - 1), "atk": atk * 1.25 ** (t - 1), "def": dfn + 6 * t, "spd": 0.9, "crit": 0.05}

def level_composition(w, i):
    """Возвращает список (stats, element, is_boss) врагов уровня w(1..9), i(1..15)."""
    el = WORLD_ELEMENT[w]
    fam = FAM_OF_ELEMENT[el]
    tier = min(1 + (w - 1) // 2 + (1 if i >= 8 else 0), TIERS[fam])

    def mob(s): return (s, el, False)
    def boss(s, boss_el=None): return (s, el if boss_el is None else boss_el, True)

    if w == 1 and i == 1:
        return ([mob(mob_stats("dreamling", 1))] * 2
                + [boss({"hp": 4200, "atk": 95, "def": 80, "spd": 0.9, "crit": 0.05}, 0)])

    if i == 15:
        darklord = {"hp": 9800, "atk": 240, "def": 130, "spd": 0.9, "crit": 0.05}
        if w in MASTERS:
            scale = min(1.45 ** (w - 2), 12.0)
            out = [mob(mob_stats(fam, tier))] * 4
            out.append(boss({"hp": 3200 * scale, "atk": 130 * scale, "def": 80 * scale, "spd": 0.9, "crit": 0.05}, 0))
            if w == 9:
                out.append(boss(darklord, 0))
            return out
        return [mob(mob_stats(fam, tier))] * 4 + [boss(darklord, 0)]

    if i in (5, 10):
        mb = {"hp": 2600 if i == 5 else 5200, "atk": 110 if i == 5 else 170,
              "def": 60 if i == 5 else 90, "spd": 0.9, "crit": 0.05}
        return ([mob(mob_stats(fam, tier))] * 3
                + [mob(mob_stats(fam, max(1, tier - 1)))] * 3
                + [boss(mb, 0)])

    out = [mob(mob_stats(fam, tier))] * (3 + i // 5)
    out += [mob(mob_stats(fam, max(1, tier - 1)))] * (2 + i // 6)
    if i % 3 == 0:
        out += [(mob_stats("golem", min(1 + w // 3, 3)), 2, False)] * (1 + i // 8)
    return out

def simulate(team_levels, w, i, runs=200, seed=7):
    """Доля побед команды 4 героев данного уровня (кит растёт с уровнем, как у живого игрока)."""
    rnd = Randomish(seed)
    stars = min(1 + team_levels // 14, 5)
    rank = min(team_levels // 14, 5)
    wins = 0
    for _ in range(runs):
        heroes = []
        for hid, base in HEROES.items():
            s = hero_stats(base, team_levels, stars=stars, rank=rank)
            heroes.append({**s, "el": base["el"]})
        heroes[0]["atk"] *= 1 + SYNERGY_ATK; heroes[3]["atk"] *= 1 + SYNERGY_ATK  # Эш+Чейни
        hps = [h["hp"] for h in heroes]
        enemies = [{**e[0], "el": e[1]} for e in level_composition(w, i)]
        ehp = [e["hp"] for e in enemies]

        # DPS-гонка с таргетингом: герои бьют самого слабого живого, враги — первого живого
        t = 0.0
        while t < 180:
            for k, h in enumerate(heroes):
                if hps[k] <= 0: continue
                for j, e in enumerate(enemies):
                    if ehp[j] > 0:
                        ehp[j] -= damage(h["atk"], e["def"], 1.4, h["el"], e["el"], rnd.crit(h["crit"]))
                        break
            for j, e in enumerate(enemies):
                if ehp[j] <= 0: continue
                for k, h in enumerate(heroes):
                    if hps[k] > 0:
                        hps[k] -= damage(e["atk"], h["def"], 1.0, e["el"], h["el"], e["crit"])
                        break
            if all(x <= 0 for x in ehp): wins += 1; break
            if all(x <= 0 for x in hps): break
            t += 1.0  # условный тик (дальше масштаб не важен — сравнение симметричное)
    return wins / runs

class Randomish:
    def __init__(self, seed): self.s = seed
    def crit(self, chance):
        self.s = (self.s * 1103515245 + 12345) % (2 ** 31)
        return ((self.s >> 16) % 1000) / 1000 < chance

# ---------- Отчёт ----------
print("Кривая сложности: уровень героев для 50% побед (кит растёт вместе с уровнем)")
print(f"{'Мир':>4} {'лвл5':>6} {'лвл10':>6} {'лвл15':>6}  (герои 1..60; звезды=1+lvl/14, ранг=lvl/14)")
for w in range(1, 10):
    need = []
    for i in (5, 10, 15):
        lvl = 1
        for candidate in range(1, 61):
            if simulate(candidate, w, i, runs=60) >= 0.5: lvl = candidate; break
        else:
            lvl = -1  # недостижимо на 60
        need.append(lvl)
    print(f"{w:>4} {need[0]:>6} {need[1]:>6} {need[2]:>6}")

print()
print("Контроль: свежая команда (ур.1, 1★, белый) на мире 1:")
print("  уровень 2:", f"{simulate(1, 1, 2, runs=100):.0%} побед")
print("Контроль: топ-команда (ур.60, 5★, Purple) на мире 9, финал:")
print("  уровень 15:", f"{simulate(60, 9, 15, runs=100):.0%} побед")
