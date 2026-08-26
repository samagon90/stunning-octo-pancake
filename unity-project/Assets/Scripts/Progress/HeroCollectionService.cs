using System;
using System.Collections.Generic;
using DreamMasters.Core;
using DreamMasters.Data;
using UnityEngine;

namespace DreamMasters.Progress
{
    /// <summary>
    /// Коллекция героев: получение, прокачка, звёзды, ранги, пробуждение.
    /// Правила канона оригинала (см. GDD §3).
    /// </summary>
    public class HeroCollectionService
    {
        private readonly PlayerProfile _profile;

        public event Action<HeroInstance> HeroAdded;
        public event Action<HeroInstance> HeroChanged;

        public HeroCollectionService(PlayerProfile profile) => _profile = profile;

        public IReadOnlyList<HeroInstance> AllHeroes => _profile.heroes;
        public IReadOnlyList<string> TeamIds => _profile.teamHeroIds;
        public const int TeamSize = 4; // канон: отряд из 4 героев
        public const int RunesPerRank = 6; // канон: 6 рун на ранг

        public HeroInstance Obtain(string heroId)
        {
            var existing = _profile.FindHero(heroId);
            if (existing != null) return existing;
            var inst = new HeroInstance(heroId);
            _profile.heroes.Add(inst);
            HeroAdded?.Invoke(inst);
            return inst;
        }

        /// <summary>Стартовые герои оригинала: Эш (ДД, огонь), Фрэнк (танк), Аймер (лекарь), Чейни (вода).</summary>
        public void GrantStarterHeroes()
        {
            var catalog = LoadCatalog();
            if (catalog != null && catalog.starterHeroes.Count > 0)
            {
                foreach (var hero in catalog.starterHeroes)
                {
                    var inst = Obtain(hero.heroId);
                    if (_profile.teamHeroIds.Count < TeamSize && !_profile.teamHeroIds.Contains(hero.heroId))
                        _profile.teamHeroIds.Add(hero.heroId);
                    HeroChanged?.Invoke(inst);
                }
            }
            _profile.tutorialFinished = false; // обучение = первый скриптованный бой
        }

        public bool SetTeam(List<string> heroIds)
        {
            if (heroIds == null || heroIds.Count > TeamSize) return false;
            for (int i = 0; i < heroIds.Count; i++)
                if (_profile.FindHero(heroIds[i]) == null) return false;
            _profile.teamHeroIds = new List<string>(heroIds);
            return true;
        }

        /// <summary>Уровень вверх за «корм»: пыль или другие карты (упрощение среза: пыль и золото).</summary>
        public bool TryLevelUp(HeroInstance hero, CurrencyService currencies)
        {
            var data = GetData(hero);
            if (data == null || hero.level >= MaxLevel) return false;
            long dustCost = DustCostForLevel(hero.level + 1);
            if (!currencies.TrySpend(CurrencyType.Dust, dustCost)) return false;
            hero.level++;
            HeroChanged?.Invoke(hero);
            return true;
        }

        public const int MaxLevel = 60;
        public static long DustCostForLevel(int targetLevel) => 10L * targetLevel * targetLevel;

        /// <summary>Ранг вверх: 6 рун + камни эволюции. Открывает слот умения (канон).</summary>
        public bool TryRankUp(HeroInstance hero, CurrencyService currencies)
        {
            var data = GetData(hero);
            if (data == null) return false;
            if (hero.rank >= HeroRank.Purple) return false;
            if (!currencies.TrySpend(CurrencyType.Rune, RunesPerRank)) return false;
            if (!currencies.TrySpend(CurrencyType.EvolutionStone, 1)) return false;

            hero.rank = (HeroRank)((int)hero.rank + 1);
            for (int i = 0; i < hero.abilityLevels.Length; i++)
                if (hero.abilityLevels[i] == 0 && i < hero.UnlockedAbilitySlots)
                    hero.abilityLevels[i] = 1; // новый слот открыт — умение 1 уровня
            HeroChanged?.Invoke(hero);
            return true;
        }

        /// <summary>Звезда вверх: дубль карты (осколки) + камни эволюции (канон).</summary>
        public bool TryStarUp(HeroInstance hero, CurrencyService currencies)
        {
            var data = GetData(hero);
            if (data == null) return false;
            if (hero.stars >= data.maxStars) return false;
            if (!currencies.TrySpend(CurrencyType.Shard, CurrencyService.ShardsPerHero)) return false;
            if (!currencies.TrySpend(CurrencyType.EvolutionStone, 1)) return false;
            hero.stars++;
            HeroChanged?.Invoke(hero);
            return true;
        }

        /// <summary>Пробуждение: макс. звёзды + фиолетовый ранг → облик новый, статы ×2 (канон).</summary>
        public bool TryAwaken(HeroInstance hero, CurrencyService currencies)
        {
            var data = GetData(hero);
            if (data == null || !hero.CanAwaken(data)) return false;
            if (!currencies.TrySpend(CurrencyType.EvolutionStone, 10)) return false;
            hero.awakened = true;
            HeroChanged?.Invoke(hero);
            return true;
        }

        /// <summary>Прокачка умения: золото + очко навыка; уровень умения ≤ уровня героя (канон).</summary>
        public bool TryUpgradeAbility(HeroInstance hero, int abilityIndex, CurrencyService currencies)
        {
            var data = GetData(hero);
            if (data == null || abilityIndex < 0 || abilityIndex >= hero.abilityLevels.Length) return false;
            int lvl = hero.abilityLevels[abilityIndex];
            if (lvl == 0 || lvl >= hero.level) return false; // канон: навык ≤ уровень героя
            long goldCost = 100L * lvl;
            if (!currencies.TrySpend(CurrencyType.Gold, goldCost)) return false;
            if (!currencies.TrySpend(CurrencyType.SkillPoint, 1)) return false;
            hero.abilityLevels[abilityIndex]++;
            HeroChanged?.Invoke(hero);
            return true;
        }

        public HeroData GetData(HeroInstance hero) => LoadCatalog()?.GetHero(hero.heroId);

        private static HeroCatalog _catalogCache;
        private static HeroCatalog LoadCatalog()
        {
            if (_catalogCache != null) return _catalogCache;
            var found = Resources.LoadAll<HeroCatalog>("DreamMasters");
            if (found.Length > 0) _catalogCache = found[0];
            else UnityEngine.Debug.LogWarning("[HeroCollection] HeroCatalog не найден в Resources/DreamMasters.");
            return _catalogCache;
        }
    }
}
