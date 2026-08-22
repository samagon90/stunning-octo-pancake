using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>
    /// База всего контента героев, синергий и врагов. Заполняется в Инспекторе,
    /// код обращается только сюда — контент не захардкожен.
    /// Assets → Create → Dream Masters → Hero Catalog.
    /// </summary>
    [CreateAssetMenu(fileName = "HeroCatalog", menuName = "Dream Masters/Hero Catalog")]
    public class HeroCatalog : ScriptableObject
    {
        [Header("Герои (цель ремейка — 100+, для среза — 4)")]
        public List<HeroData> heroes = new List<HeroData>();

        [Header("Синергии (пары героев)")]
        public List<SynergyData> synergies = new List<SynergyData>();

        [Header("Стартовые герои для выбора (канон: 4 варианта)")]
        public List<HeroData> starterHeroes = new List<HeroData>();

        [Header("Враги")]
        public List<EnemyData> enemies = new List<EnemyData>();

        [Header("Кампания: миры снов (9 миров по 15 уровней)")]
        public List<WorldData> worlds = new List<WorldData>();

        [Header("Легаси: мир 1 (используется, если миры не заполнены)")]
        public List<LevelData> world1Levels = new List<LevelData>();

        /// <summary>Мир по индексу (или null).</summary>
        public WorldData GetWorld(int index)
        {
            return index >= 0 && index < worlds.Count ? worlds[index] : null;
        }

        /// <summary>Сколько миров реально настроено.</summary>
        public int WorldCount => worlds.Count > 0 ? worlds.Count : (world1Levels.Count > 0 ? 1 : 0);

        private Dictionary<string, HeroData> _heroById;

        public HeroData GetHero(string heroId)
        {
            if (_heroById == null) Index();
            return _heroById != null && _heroById.TryGetValue(heroId, out var h) ? h : null;
        }

        public List<SynergyData> GetSynergiesFor(HeroData hero, IReadOnlyList<HeroData> team)
        {
            var result = new List<SynergyData>();
            foreach (var s in synergies)
            {
                if (s.heroA == null || s.heroB == null) continue;
                bool involves = s.heroA == hero || s.heroB == hero;
                if (!involves) continue;
                var other = s.heroA == hero ? s.heroB : s.heroA;
                for (int i = 0; i < team.Count; i++)
                    if (team[i] == other) { result.Add(s); break; }
            }
            return result;
        }

        private void Index()
        {
            _heroById = new Dictionary<string, HeroData>(heroes.Count);
            foreach (var h in heroes)
                if (h != null && !string.IsNullOrEmpty(h.heroId) && !_heroById.ContainsKey(h.heroId))
                    _heroById.Add(h.heroId, h);
        }
    }
}
