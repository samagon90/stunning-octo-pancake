using System;
using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Progress
{
    /// <summary>Все валюты и ресурсы игры (канон оригинала).</summary>
    [Serializable]
    public enum CurrencyType
    {
        Gold = 0,           // золото — прокачка умений, апгрейды
        Crystal = 1,        // кристаллы — премиум (осколки, очки навыков)
        Shard = 2,          // осколки героя: 80 = гарантированный герой
        Rune = 3,           // руны ранга (6 на ранг)
        EvolutionStone = 4, // камни эволюции (звёзды/ранги/пробуждение)
        Dust = 5,           // волшебная пыль — прокачка уровня
        SkillPoint = 6,     // очки навыков (регенерируются со временем)
        Energy = 7,         // энергия входа в уровни
        SoulStone = 8       // камни души (будущие механики)
    }

    /// <summary>Ранг героя по цветам — канон: белый → зелёный → зелёный+1 → синий → синий+1 → фиолетовый.</summary>
    public enum HeroRank
    {
        White = 0,
        Green = 1,
        GreenPlus = 2,
        Blue = 3,
        BluePlus = 4,
        Purple = 5
    }

    /// <summary>Экземпляр героя у игрока (сериализуется в JSON). Данные — в HeroData.</summary>
    [Serializable]
    public class HeroInstance
    {
        public string heroId;
        public int level = 1;
        [Range(1, 7)] public int stars = 1;
        public HeroRank rank = HeroRank.White;
        public int[] abilityLevels = { 1, 0, 0, 0 }; // уровень каждого из 4 умений (0 = ещё не открыт)
        public bool awakened;
        public int expIntoLevel;

        public HeroInstance(string id) { heroId = id; }

        /// <summary>Число открытых умений по рангу (слот i открывается на ранге i).</summary>
        public int UnlockedAbilitySlots => awakened ? 4 : System.Math.Min((int)rank + 1, 4);

        /// <summary>Расчёт финальных статов: база × уровень × звёзды × ранг × пробуждение.</summary>
        public Data.HeroStatsBlock ComputeStats(Data.HeroData data)
        {
            var s = new Data.HeroStatsBlock();
            float lvl = 1f + (level - 1) * 0.10f;          // +10% за уровень
            float star = 1f + (stars - 1) * 0.15f;         // +15% за звезду
            float rankM = 1f + (int)rank * 0.12f;          // +12% за ранг
            float awake = awakened ? 2.0f : 1.0f;          // канон: пробуждение ≈ ×2
            float mult = lvl * star * rankM * awake;

            s.maxHp = data.baseStats.maxHp * mult;
            s.attack = data.baseStats.attack * mult;
            s.defense = data.baseStats.defense * mult;
            s.attackSpeed = data.baseStats.attackSpeed;
            s.moveSpeed = data.baseStats.moveSpeed;
            s.critChance = data.baseStats.critChance;
            s.critDamage = data.baseStats.critDamage;
            s.hpRegen = data.baseStats.hpRegen * mult;
            return s;
        }

        /// <summary>Слитие одинаковых карт: звезда вверх (требуются камни эволюции — проверяет сервис).</summary>
        public bool TryAddStar(Data.HeroData data, out string error)
        {
            if (stars >= data.maxStars && !awakened)
            {
                // Полные звёзды — путь к пробуждению лежит через максимальный ранг (см. HeroCollectionService).
                error = "Достигнут максимум звёзд этого героя.";
                return false;
            }
            if (stars < data.maxStars) { stars++; error = null; return true; }
            error = "Нельзя добавить звезду."; return false;
        }

        public bool CanAwaken(Data.HeroData data)
        {
            return !awakened && stars >= data.maxStars && rank == HeroRank.Purple;
        }
    }

    /// <summary>
    /// Профиль игрока. Хранится и локально (кеш), и в облаке (после подключения бэкенда).
    /// Все поля сериализуемы через JsonUtility.
    /// </summary>
    [Serializable]
    public class PlayerProfile
    {
        public int profileVersion = 1;             // версия протокола данных
        public string anonymousId;                 // генерируется при первом входе
        public string boundAccountId = "";         // Google Play Games / сервер — позже
        public string displayName = "Мастер";
        public long createdUtcTicks;

        // Валюты — пары (тип, количество), JsonUtility не умеет словари.
        public List<int> currencyKeys = new List<int>();
        public List<long> currencyValues = new List<long>();

        // Коллекция и команда
        public List<HeroInstance> heroes = new List<HeroInstance>();
        public List<string> teamHeroIds = new List<string>(); // ровно 4 слота

        // Прогресс кампании
        public int campaignWorld = 1;
        public int campaignLevel = 1;
        public int arenaRating = 1000;
        public int bestArenaRating;

        /// <summary>Сколько уровней зачищено в каждом мире (индекс = мир).</summary>
        public List<int> worldProgress = new List<int>();

        // Арена «Колизей»: канон — до 3 поражений в день
        public string colosseumDay = "";
        public int colosseumLossesToday;
        public int colosseumWinsToday;

        public bool tutorialFinished;
        public string lastSaveUtc;
        public string energyRegenUtc; // когда тикал реген энергии (ISO) — переживает рестарты

        // ---------- Настройки ----------
        [Range(0f, 1f)] public float musicVolume = 0.8f;
        [Range(0f, 1f)] public float sfxVolume = 1.0f;
        public bool adsPersonalized = true; // для Consent Manager при подключении рекламы

        // ---------- Прогресс миров (канон: 9 миров по 15 уровней) ----------
        public const int LevelsPerWorld = 15;

        public int GetWorldProgress(int worldIndex)
        {
            return worldIndex >= 0 && worldIndex < worldProgress.Count ? worldProgress[worldIndex] : 0;
        }

        public void RecordLevelCleared(int worldIndex, int levelIndex)
        {
            if (worldIndex < 0 || levelIndex < 0) return;
            while (worldProgress.Count <= worldIndex) worldProgress.Add(0);
            if (levelIndex + 1 > worldProgress[worldIndex]) worldProgress[worldIndex] = levelIndex + 1;
            campaignWorld = worldIndex + 1;
            campaignLevel = Mathf.Clamp(worldProgress[worldIndex] + 1, 1, LevelsPerWorld);
        }

        public bool IsWorldUnlocked(int worldIndex)
        {
            if (worldIndex <= 0) return true;
            return GetWorldProgress(worldIndex - 1) >= LevelsPerWorld;
        }

        public bool IsLevelUnlocked(int worldIndex, int levelIndex)
        {
            return IsWorldUnlocked(worldIndex) && levelIndex < GetWorldProgress(worldIndex) + 1;
        }

        // ---------- Колизей: канон — до 3 поражений в день ----------
        public void RollColosseumDay()
        {
            string today = DateTime.UtcNow.ToString("yyyyMMdd");
            if (!string.Equals(colosseumDay, today))
            {
                colosseumDay = today;
                colosseumLossesToday = 0;
                colosseumWinsToday = 0;
            }
        }

        public long GetCurrency(CurrencyType t)
        {
            int key = (int)t;
            for (int i = 0; i < currencyKeys.Count; i++)
                if (currencyKeys[i] == key) return currencyValues[i];
            return 0;
        }

        public void SetCurrency(CurrencyType t, long amount)
        {
            int key = (int)t;
            for (int i = 0; i < currencyKeys.Count; i++)
                if (currencyKeys[i] == key) { currencyValues[i] = amount; return; }
            currencyKeys.Add(key);
            currencyValues.Add(amount);
        }

        public HeroInstance FindHero(string heroId)
        {
            for (int i = 0; i < heroes.Count; i++)
                if (heroes[i].heroId == heroId) return heroes[i];
            return null;
        }

        public static PlayerProfile CreateNew()
        {
            var p = new PlayerProfile
            {
                anonymousId = System.Guid.NewGuid().ToString("N"),
                createdUtcTicks = System.DateTime.UtcNow.Ticks,
                lastSaveUtc = System.DateTime.UtcNow.ToString("o")
            };
            p.SetCurrency(CurrencyType.Gold, 1000);
            p.SetCurrency(CurrencyType.Crystal, 100);
            p.SetCurrency(CurrencyType.Energy, 60);
            p.SetCurrency(CurrencyType.SkillPoint, 10);
            return p;
        }
    }
}
