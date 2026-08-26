#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор контента Dream Masters Revival v2.
9 миров × 15 уровней, 14 героев (56 умений), 27 врагов, 11 синергий, миры, каталог, конфиг.
Детерминированные GUID → ассеты корректно ссылаются на скрипты и друг на друга."""
import hashlib, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "unity-project", "Assets")
SCRIPTS = os.path.join(ROOT, "Scripts")
CONTENT = os.path.join(ROOT, "Resources", "DreamMasters")

def guid_for(path_relative):
    return hashlib.md5(("DreamMasters/" + path_relative).encode("utf-8")).hexdigest()

def esc(s):
    out = []
    for ch in s:
        if ord(ch) > 127: out.append("\\u%04X" % ord(ch))
        elif ch == '"': out.append('\\"')
        else: out.append(ch)
    return '"' + "".join(out) + '"'

def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

SCRIPT_META = "fileFormatVersion: 2\nguid: {guid}\nMonoImporter:\n  externalObjects: {{}}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {{instanceID: 0}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
ASSET_META = "fileFormatVersion: 2\nguid: {guid}\nNativeFormatImporter:\n  externalObjects: {{}}\n  mainObjectFileID: 11400000\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
FOLDER_META = "fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"

script_guids = {}
for base, _, files in os.walk(SCRIPTS):
    for fn in files:
        if fn.endswith(".cs"):
            full = os.path.join(base, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            g = guid_for(rel)
            script_guids[fn[:-3]] = g
            write_file(full + ".meta", SCRIPT_META.format(guid=g))
for base, dirs, _ in os.walk(SCRIPTS):
    for d in dirs:
        full = os.path.join(base, d)
        rel = os.path.relpath(full, ROOT).replace("\\", "/")
        if not os.path.exists(os.path.join(full, ".meta")):
            write_file(os.path.join(full, ".meta"), FOLDER_META.format(guid=guid_for(rel)))

def asset_yaml(class_name, name, fields):
    return "\n".join([
        "%YAML 1.1", "%TAG !u! tag:unity3d.com,2011:",
        "--- !u!114 &11400000", "MonoBehaviour:",
        "  m_ObjectHideFlags: 0", "  m_CorrespondingSourceObject: {fileID: 0}",
        "  m_PrefabInstance: {fileID: 0}", "  m_PrefabAsset: {fileID: 0}",
        "  m_GameObject: {fileID: 0}", "  m_Enabled: 1", "  m_EditorHideFlags: 0",
        "  m_Script: {fileID: 11500000, guid: %s, type: 3}" % script_guids[class_name],
        "  m_Name: " + name, "  m_EditorClassIdentifier: ",
    ] + ["  " + l for l in fields]) + "\n"

asset_guids = {}
def save_asset(cls, file_name, name, fields):
    rel = "Resources/DreamMasters/%s.asset" % file_name
    g = guid_for(rel)
    asset_guids[file_name] = g
    path = os.path.join(CONTENT, file_name + ".asset")
    write_file(path, asset_yaml(cls, name, fields))
    write_file(path + ".meta", ASSET_META.format(guid=g))

def ref(file_name):
    return "{fileID: 11400000, guid: %s, type: 3}" % asset_guids[file_name]

# ================= УМЕНИЯ (56) =================
A = []  # (id, имя, описание, тип, к-т, кд, дальность, радиус, саппорт, баф)
def ab(hero, en, ru, t, pc, cd, rng=6, rad=0, sup=0, buf=0, desc=""):
    A.append((f"{hero}_{en}", ru, desc or ru, t, pc, cd, rng, rad, sup, buf))

# Эш (огонь, средняя, боец)
ab("ash","fireball","Огненный шар",0,1.6,8,6); ab("ash","blaze","Вспышка пламени",1,1.3,12,6,3.5)
ab("ash","flame_line","Огненная струя",2,1.4,10,8,2.5); ab("ash","ultimate","Ярость Эша",0,3.0,20,7)
# Фрэнк (земля, ближняя, танк)
ab("frank","slam","Удар оземь",1,1.2,10,0,3.0); ab("frank","shield","Каменная кожа",4,0,15,0,0,0.15,6)
ab("frank","taunt_strike","Провокация",0,1.8,8,2); ab("frank","quake","Землетрясение",1,2.0,18,0,4.5)
# Аймер (вода, дальняя, поддержка)
ab("aimer","heal","Слёзы исцеления",3,0,8,0,0,1.5); ab("aimer","purify","Очищение",3,0,12,0,0,2.0)
ab("aimer","bless","Благословение",4,0,15,0,0,0.20,6); ab("aimer","drown","Водяной хлыст",0,1.6,10,7)
# Чейни (вода, дальняя, боец)
ab("cheney","wave","Волна Чейни",0,1.5,8,7); ab("cheney","splash","Брызги сямисена",1,1.3,12,7,3.5)
ab("cheney","tide","Прилив",2,1.4,10,9,3); ab("cheney","tempest","Шторм",1,2.6,20,8,5)
# Аид (воздух, средняя, боец)
ab("hades","spear","Копьё ветра",0,1.7,8,6); ab("hades","gust","Порыв",1,1.2,12,6,4)
ab("hades","storm","Буря",2,1.5,10,9,3); ab("hades","reap","Жатва Аида",0,3.2,22,7)
# Жанна (огонь, средняя, универсал)
ab("jeanne","strike","Удар знамени",0,1.5,8,6); ab("jeanne","banner","Знамя Жанны",4,0,15,0,0,0.20,6)
ab("jeanne","flare","Всполох",1,1.4,12,6,3.5); ab("jeanne","verdict","Приговор",1,2.4,20,8,5)
# Зевс (воздух, средняя, боец)
ab("zeus","bolt","Молния",0,1.8,8,7); ab("zeus","thunder","Гром",1,1.5,12,7,4)
ab("zeus","storm_front","Грозовой фронт",2,1.6,11,9,3); ab("zeus","wrath","Гнев Олимпа",1,3.4,24,9,5.5)
# Трипитака (земля, средняя, танк)
ab("tripitaka","staff","Удар посохом",0,1.5,8,2); ab("tripitaka","sutra","Чтение сутры",4,0,16,0,0,0.25,8)
ab("tripitaka","palm","Ладонь Будды",1,1.3,10,0,3.5); ab("tripitaka","lotus","Лотос защиты",4,0,20,0,0,0.35,10)
# Нюйва (земля, дальняя, поддержка)
ab("nuwa","mend","Ладонь созидания",3,0,8,0,0,1.6); ab("nuwa","stone_skin","Каменный покров",4,0,14,0,0,0.20,7)
ab("nuwa","shards","Осколки неба",1,1.4,12,8,3.5); ab("nuwa","rainbow","Радуга Нюйвы",3,0,18,0,0,2.4)
# Шаман (огонь, средняя, универсал)
ab("shaman","spark","Искра духов",0,1.5,8,6); ab("shaman","totem","Тотем огня",4,0,15,0,0,0.18,7)
ab("shaman","ash_cloud","Пепельное облако",1,1.4,12,7,4); ab("shaman","spirit_fire","Огонь духов",1,2.8,22,8,5)
# Лян (воздух, дальняя, боец)
ab("liang","fan","Взмах веера",0,1.6,8,7); ab("liang","gale","Порыв стратагем",2,1.5,10,9,3)
ab("liang","feint","Ложный манёвр",0,1.9,9,7); ab("liang","stratagem","Стратегия Ляна",1,3.0,22,9,5)
# Юнь (вода, ближняя, танк)
ab("yun","fist","Кулак волны",0,1.6,8,2); ab("yun","shell","Панцирь глубин",4,0,15,0,0,0.22,7)
ab("yun","whirl","Водоворот",1,1.4,11,0,3.5); ab("yun","tsunami","Цунами",1,2.7,20,8,5)
# Электра (воздух, дальняя, боец)
ab("electra","arc","Дуга",0,1.7,8,7); ab("electra","static","Статический разряд",1,1.35,12,7,3.5)
ab("electra","network","Сеть зарядов",2,1.5,10,9,3); ab("electra","overload","Перегрузка",1,3.1,22,8,5)
# Тетра (вода, средняя, поддержка)
ab("tetra","drop","Капля",3,0,8,0,0,1.4); ab("tetra","mist","Дымка",4,0,14,0,0,0.18,6)
ab("tetra","geyser","Гейзер",1,1.45,12,7,3.5); ab("tetra","spring","Живой источник",3,0,18,0,0,2.6)

for aid, nm, desc, tt, pc, cd, rng, rad, sup, buf in A:
    save_asset("AbilityData", "ab_" + aid, nm, [
        "abilityId: " + esc(aid), "displayName: " + esc(nm), "description: " + esc(desc),
        "targetType: %d" % tt, "powerCoefficient: %g" % pc, "cooldownSeconds: %g" % cd,
        "castRange: %g" % rng, "effectRadius: %g" % rad, "supportValue: %g" % sup, "buffDuration: %g" % buf])

# ================= ГЕРОИ (14) =================
# (id, имя, кат, стихия(0F 1A 2E 3W), дальн, роль, (hp,atk,def,spd,move,crit), звёзды, [умения], лор)
HEROES = [
    ("ash","Эш",4,0,1,1,(900,150,50,1.1,3.8,0.15),5,["ash_fireball","ash_blaze","ash_flame_line","ash_ultimate"],"Весёлый повелитель пламени из мира чужих легенд. Первый, кто откликнулся на зов Мастера."),
    ("frank","Фрэнк",3,2,0,0,(1600,90,110,0.8,3.2,0.05),5,["frank_slam","frank_shield","frank_taunt_strike","frank_quake"],"Порождение забытой лаборатории: сдержан, надёжен, держит строй как скала."),
    ("aimer","Аймер",2,3,2,2,(800,100,40,0.9,3.4,0.05),5,["aimer_heal","aimer_purify","aimer_bless","aimer_drown"],"Хранительница слёз Мира Снов. Ни один герой не падёт, пока она рядом."),
    ("cheney","Чейни",1,3,2,1,(950,135,45,1.0,3.6,0.12),6,["cheney_wave","cheney_splash","cheney_tide","cheney_tempest"],"Музыка её сямисена звучит как прилив — красиво и смертоносно."),
    ("hades","Аид",0,1,1,1,(1000,140,60,1.0,3.6,0.10),6,["hades_spear","hades_gust","hades_storm","hades_reap"],"Владыка ветров подземного царства. Спасает тех, кто не боится темноты."),
    ("jeanne","Жанна",0,0,1,3,(1100,120,70,1.0,3.5,0.08),7,["jeanne_strike","jeanne_banner","jeanne_flare","jeanne_verdict"],"Знамя, которое ведёт за собой даже потерявшихся во сне."),
    ("zeus","Зевс",0,1,1,1,(1050,155,65,1.0,3.5,0.12),7,["zeus_bolt","zeus_thunder","zeus_storm_front","zeus_wrath"],"Громовержец, чей сон тысячу лет охраняли орлы. Проснулся — и взялся за молнии."),
    ("tripitaka","Трипитака",2,2,1,0,(1750,95,125,0.85,3.3,0.05),6,["tripitaka_staff","tripitaka_sutra","tripitaka_palm","tripitaka_lotus"],"Паломник, идущий через сны так же спокойно, как через пустыни."),
    ("nuwa","Нюйва",1,2,2,2,(880,105,50,0.9,3.4,0.06),6,["nuwa_mend","nuwa_stone_skin","nuwa_shards","nuwa_rainbow"],"Полузмея-полубогиня, чинящая небо и судьбы отрядов."),
    ("shaman","Шаман",3,0,1,3,(1150,125,70,1.0,3.5,0.08),6,["shaman_spark","shaman_totem","shaman_ash_cloud","shaman_spirit_fire"],"Говорит с духами огня. Духи отвечают."),
    ("liang","Лян",1,1,2,1,(980,145,55,1.05,3.6,0.12),7,["liang_fan","liang_gale","liang_feint","liang_stratagem"],"Стратег, просчитывающий сны на три хода вперёд."),
    ("yun","Юнь",0,3,0,0,(1700,100,120,0.85,3.3,0.06),7,["yun_fist","yun_shell","yun_whirl","yun_tsunami"],"Спящий дракон западных морей. В воде и во сне — непобедим."),
    ("electra","Электра",0,1,2,1,(920,150,48,1.1,3.7,0.14),6,["electra_arc","electra_static","electra_network","electra_overload"],"Живая молния. Говорит быстро, бьёт быстрее."),
    ("tetra","Тетра",1,3,1,2,(900,110,55,0.95,3.5,0.06),5,["tetra_drop","tetra_mist","tetra_geyser","tetra_spring"],"Хранительница четырёх источников. Каждому нальёт по потребе."),
]
for hid, nm, cat, el, rng, role, st, stars, abilities, lore in HEROES:
    hp, atk, dfn, spd, move, crit = st
    fields = ["heroId: " + esc(hid), "heroName: " + esc(nm), "category: %d" % cat,
              "element: %d" % el, "attackRange: %d" % rng, "role: %d" % role,
              "baseStats:", "  maxHp: %g" % hp, "  attack: %g" % atk, "  defense: %g" % dfn,
              "  attackSpeed: %g" % spd, "  moveSpeed: %g" % move, "  critChance: %g" % crit,
              "  critDamage: 1.5", "  hpRegen: 0", "abilities:"]
    for a in abilities:
        fields.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids["ab_" + a])
    fields += ["maxStars: %d" % stars, "portrait: {fileID: 0}", "lore: " + esc(lore)]
    save_asset("HeroData", "hero_" + hid, nm, fields)

# ================= ВРАГИ =================
def mob_fields(eid, nm, el, boss, hp, atk, dfn, gold, shards, runes):
    return ["enemyId: " + esc(eid), "displayName: " + esc(nm), "element: %d" % el, "isBoss: %d" % (1 if boss else 0),
            "stats:", "  maxHp: %g" % round(hp), "  attack: %g" % round(atk), "  defense: %g" % round(dfn),
            "  attackSpeed: 0.9", "  moveSpeed: 3", "  critChance: 0.05", "  critDamage: 1.5", "  hpRegen: 0",
            "abilitiesUnlocked: %d" % (2 if boss else 0), "goldReward: %d" % gold, "shardReward: %d" % shards,
            "runeReward: %d" % runes, "viewPrefab: {fileID: 0}"]

FAMILIES = [("dreamling", "Сновидец", 0), ("sylph", "Сильфида", 1), ("golem", "Каменный страж", 2), ("kelpie", "Келпи", 3)]
TIERS = {"dreamling": 5, "sylph": 3, "golem": 3, "kelpie": 3}
BASE = {"dreamling": (380, 55, 20), "sylph": (340, 62, 15), "golem": (600, 48, 35), "kelpie": (420, 58, 18)}
for fam, nm, el in FAMILIES:
    for t in range(1, TIERS[fam] + 1):
        hp, atk, dfn = BASE[fam]
        save_asset("EnemyData", "en_mob_%s_%d" % (fam, t), "%s %s" % (nm, "I" * t), mob_fields(
            "mob_%s_%d" % (fam, t), nm, el, False,
            hp * 1.35 ** (t - 1), atk * 1.25 ** (t - 1), dfn + 6 * t, 16 * t, 1, 0))
save_asset("EnemyData", "en_midboss_nightmare_1", "Кошмар", mob_fields("midboss_nightmare_1", "Кошмар", 0, True, 2600, 110, 60, 150, 10, 2))
save_asset("EnemyData", "en_midboss_nightmare_2", "Древний Кошмар", mob_fields("midboss_nightmare_2", "Древний Кошмар", 1, True, 5200, 170, 90, 260, 14, 3))
save_asset("EnemyData", "en_boss_darklord_intro", "Повелитель Мрака", mob_fields("boss_darklord_intro", "Повелитель Мрака", 0, True, 4200, 95, 80, 120, 12, 3))
save_asset("EnemyData", "en_boss_darklord", "Повелитель Мрака Истинный", mob_fields("boss_darklord", "Повелитель Мрака Истинный", 0, True, 9800, 240, 130, 500, 30, 6))

# Боссы-Мастера миров (побеждённый Мастер присоединяется — канон)
# Баланс: масштаб 1.45^(w-2) с потолком ×12 (подобрано симулятором tools/balance_sim.py)
MASTERS = [("yun", 2), ("nuwa", 3), ("zeus", 4), ("shaman", 5), ("tripitaka", 6), ("electra", 7), ("tetra", 8), ("liang", 9)]
for hero_id, w in MASTERS:
    scale = min(1.45 ** (w - 2), 12.0)
    save_asset("EnemyData", "en_boss_master_" + hero_id, "Сон Мастера", mob_fields(
        "boss_master_" + hero_id, "Сон Мастера", 0, True, 3200 * scale, 130 * scale, 80 * scale,
        200 + 60 * w, 12 + w, 3))

# ================= МИРЫ И УРОВНИ =================
W1_NAMES = ["Первый вдох сна","Тропа сновидцев","Шёпот в тумане","Каменный сад","Врата Кошмара",
            "Логово сильфид","Речные голоса","Обманчивый берег","Гроза над сном","Сердце Кошмара",
            "Пепельная дорога","Залы забытья","Тёмный прилив","Преддверие трона","Трон Повелителя Мрака"]
W1_INTROS = ["Пробуждайся, Мастер. Первый сон всегда проигрывают — таков закон.",
             "Сновидцы тянутся к свету твоего сознания. Отбейся.","Воздух звенит: сильфиды уже рядом.",
             "Камни здесь помнят боль. Много боли.","Кошмар сторожит врата. Все стихии пригодятся.",
             "Пение сильфид усыпляет. Не слушай.","Келпи зовут в глубину. Не отвечай.","Кажется, берег близко. Кажется.",
             "Гроза — это просто чей-то очень плохой сон.","Сердце Кошмара бьётся. Останови его.",
             "Пепел — всё, что осталось от прежних Мастеров.","Здесь забыли даже собственные имена.",
             "Прилив темнеет. Пора.","За этой дверью — трон.","Он ждал тебя тысячи лет. Пора вернуть долг."]
WORLDS = [
    ("w1","Первый сон",0,"Сон, в котором всё началось и где закончится.", None, W1_NAMES, W1_INTROS),
    ("w2","Сон Глубин",3,"Первый заточённый Мастер спит на дне. Вода помнит его имя.", "yun", None, None),
    ("w3","Каменный сон",2,"Сон, обратившийся в камень. Нюйва чинит его изнутри.", "nuwa", None, None),
    ("w4","Ветряной сон",1,"Бесконечное небо, по которому гремит сон Зевса.", "zeus", None, None),
    ("w5","Сон Кошмаров",0,"Здесь Мрак впервые проник в чужие сны. Пахнет пеплом.", "shaman", None, None),
    ("w6","Сон Преданий",2,"Сказки и предания сплелись в каменные залы.", "tripitaka", None, None),
    ("w7","Грозовой сон",1,"Между молниями живёт Электра. Не моргай.", "electra", None, None),
    ("w8","Туманный сон",3,"Туман пьёт имена. Тетра раздаёт их обратно.", "tetra", None, None),
    ("w9","Вечный сон",0,"Последний сон. Здесь Мрак запер Ляна — и себя.", "liang", None, None),
]
PLACES = ["Тропа","Сад","Мост","Врата","Логово","Залы","Берег","Ущелье","Дорога","Преддверие","Трон","Сердце","Река","Башня","Предел"]
THEME_WORDS = {0:["пепла","искры","жара","пламени","углей"],1:["ветра","грозы","свиста","бури","эха"],
               2:["камня","корней","песка","руды","скал"],3:["прилива","тумана","глубин","слёз","шторма"]}
FAM_OF_ELEMENT = {0:"dreamling",1:"sylph",2:"golem",3:"kelpie"}

level_files_by_world = {}
for w_idx, (wid, wname, wel, wdesc, master, w_names, w_intros) in enumerate(WORLDS, start=1):
    files = []
    for i in range(15):
        lvl_idx = i + 1
        tier = min(1 + (w_idx - 1) // 2 + (1 if i >= 8 else 0), TIERS[FAM_OF_ELEMENT[wel]])
        fam = FAM_OF_ELEMENT[wel]
        is_final = lvl_idx == 15
        is_mid = lvl_idx in (5, 10)
        waves = []
        if w_names is not None:
            names, intros = w_names, w_intros
        else:
            names = ["%s %s" % (p, THEME_WORDS[wel][(i + w_idx) % 5]) for p in PLACES]
            intros = ["Мир %d: %s. %s" % (w_idx, wname, wdesc)] * 15

        if w_idx == 1 and lvl_idx == 1:
            waves = [("en_mob_dreamling_1", 2, 0.8), ("en_boss_darklord_intro", 1, 0.5)]
        elif is_final:
            if master is not None:
                waves = [("en_mob_%s_%d" % (fam, tier), 4, 0.6), ("en_boss_master_" + master, 1, 0.6)]
                if w_idx == 9:
                    waves.append(("en_boss_darklord", 1, 0.5))
            else:
                waves = [("en_mob_%s_%d" % (fam, tier), 4, 0.6), ("en_boss_darklord", 1, 0.5)]
        elif is_mid:
            waves = [("en_mob_%s_%d" % (fam, tier), 3, 0.7),
                     ("en_mob_%s_%d" % (fam, max(1, tier - 1)), 3, 0.7),
                     ("en_midboss_nightmare_%d" % (1 if lvl_idx == 5 else 2), 1, 0.5)]
        else:
            waves = [("en_mob_%s_%d" % (fam, tier), 3 + lvl_idx // 5, 0.7),
                     ("en_mob_%s_%d" % (fam, max(1, tier - 1)), 2 + lvl_idx // 6, 0.7)]
            if lvl_idx % 3 == 0:
                waves.append(("en_mob_golem_%d" % min(1 + w_idx // 3, 3), 1 + lvl_idx // 8, 0.8))

        scripted = 1 if (w_idx == 1 and lvl_idx == 1) else 0
        fields = ["levelId: " + esc("%s_l%02d" % (wid, lvl_idx)),
                  "displayName: " + esc(names[i]), "introText: " + esc(intros[i]), "waves:"]
        for enemy, count, interval in waves:
            fields += ["  - enemy: {fileID: 11400000, guid: %s, type: 3}" % asset_guids[enemy],
                       "    count: %d" % count, "    spawnInterval: %g" % interval]
        fields += ["goldReward: %d" % (150 + 40 * i + 130 * (w_idx - 1)),
                   "crystalReward: %d" % (15 + 3 * i + 10 * (w_idx - 1)),
                   "shardReward: %d" % (8 + 2 * i + 6 * (w_idx - 1)),
                   "runeReward: 6", "scriptedPlayerLoss: %d" % scripted]
        fname = "lvl_%s_%02d" % (wid, lvl_idx)
        save_asset("LevelData", fname, "%d-%d %s" % (w_idx, lvl_idx, names[i]), fields)
        files.append(fname)
    level_files_by_world[wid] = files

for w_idx, (wid, wname, wel, wdesc, master, _unused1, _unused2) in enumerate(WORLDS, start=1):
    fields = ["worldId: " + esc(wid), "worldName: " + esc(wname), "themeElement: %d" % wel,
              "description: " + esc(wdesc), "levels:"]
    for f in level_files_by_world[wid]:
        fields.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids[f])
    fields.append("bossHero: " + (ref("hero_" + master) if master else "{fileID: 0}"))
    save_asset("WorldData", "world_" + wid, wname, fields)

# ================= СИНЕРГИИ =================
SYN = [("syn_ash_cheney","ash","cheney",0,0.20),("syn_frank_aimer","frank","aimer",2,0.20),
       ("syn_hades_jeanne","hades","jeanne",1,0.20),("syn_ash_jeanne","ash","jeanne",0,0.15),
       ("syn_frank_hades","frank","hades",3,0.05),("syn_zeus_electra","zeus","electra",0,0.20),
       ("syn_yun_frank","yun","frank",2,0.20),("syn_nuwa_aimer","nuwa","aimer",1,0.25),
       ("syn_liang_hades","liang","hades",0,0.20),("syn_tripitaka_shaman","tripitaka","shaman",2,0.15),
       ("syn_tetra_cheney","tetra","cheney",1,0.20)]
for sid, a, b, bt, val in SYN:
    save_asset("SynergyData", sid, sid, [
        "heroA: " + ref("hero_" + a), "heroB: " + ref("hero_" + b),
        "bonusType: %d" % bt, "value: %g" % val])

# ================= КОНФИГ =================
save_asset("GameConfig", "GameConfig", "GameConfig", [
    "targetFrameRate: 60", "elementAdvantageMultiplier: 1.25", "elementDisadvantageMultiplier: 0.8",
    "reviveInvulnerabilitySeconds: 1.5", "allowSpeedX2: 1", "profileFileName: " + esc("profile.json"),
    "profileVersion: 1", "apiBaseUrl: " + esc(""), "skipTutorial: 0", "debugGodMode: 0"])

# ================= КАТАЛОГ =================
cat = ["heroes:"]
for h in HEROES:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids["hero_" + h[0]])
cat.append("synergies:")
for sid, _, _, _, _ in SYN:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids[sid])
cat.append("starterHeroes:")
for h in ["ash", "frank", "aimer", "cheney"]:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids["hero_" + h])
cat.append("enemies:")
enemies = []
for fam, nm, el in FAMILIES:
    for t in range(1, TIERS[fam] + 1):
        enemies.append("en_mob_%s_%d" % (fam, t))
enemies += ["en_midboss_nightmare_1", "en_midboss_nightmare_2", "en_boss_darklord_intro", "en_boss_darklord"]
enemies += ["en_boss_master_" + m for m, _ in MASTERS]
for e in enemies:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids[e])
cat.append("worlds:")
for w in WORLDS:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids["world_" + w[0]])
cat.append("world1Levels:")
for f in level_files_by_world["w1"]:
    cat.append("  - {fileID: 11400000, guid: %s, type: 3}" % asset_guids[f])
save_asset("HeroCatalog", "HeroCatalog", "HeroCatalog", cat)

for folder, rel in [(ROOT, "Assets"), (os.path.join(ROOT, "Scripts"), "Assets/Scripts"),
                    (os.path.join(ROOT, "Resources"), "Assets/Resources"), (CONTENT, "Assets/Resources/DreamMasters")]:
    if not os.path.exists(os.path.join(folder, ".meta")):
        write_file(os.path.join(folder, ".meta"), FOLDER_META.format(guid=guid_for(rel)))

print("Скриптов с .meta:", len(script_guids))
print("Героев: %d, умений: %d, врагов: %d, уровней: %d, миров: %d, синергий: %d" %
      (len(HEROES), len(A), len(enemies), 15 * len(WORLDS), len(WORLDS), len(SYN)))
