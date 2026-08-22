using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>Базовый блок характеристик (в оригинале 12 статов; здесь ядро из 8, расширяется без ломки формулы).</summary>
    [System.Serializable]
    public class HeroStatsBlock
    {
        public float maxHp = 1000f;
        public float attack = 120f;
        public float defense = 60f;       // снижает урон
        public float attackSpeed = 1.0f;  // атаки в секунду
        public float moveSpeed = 3.5f;    // юнитов в секунду
        public float critChance = 0.10f;  // 0..1
        public float critDamage = 1.5f;   // мнитель при крите
        public float hpRegen = 0f;        // ХП в секунду
    }

    /// <summary>
    /// Герой-карта. ScriptableObject — контент (100+ героев) добавляется без кода.
    /// Assets → Create → Dream Masters → Hero.
    /// </summary>
    [CreateAssetMenu(fileName = "NewHero", menuName = "Dream Masters/Hero")]
    public class HeroData : ScriptableObject
    {
        [Header("Идентификация")]
        public string heroId;
        public string heroName;
        public HeroCategory category = HeroCategory.Other;
        public Element element = Element.Fire;
        public AttackRange attackRange = AttackRange.Mid;
        public HeroRole role = HeroRole.Damage;

        [Header("База (1 уровень, 1 звезда, белый ранг)")]
        public HeroStatsBlock baseStats = new HeroStatsBlock();

        [Header("Умения (ровно 4, открываются по рангу)")]
        public List<AbilityData> abilities = new List<AbilityData>();

        [Header("Развитие")]
        [Range(5, 7)] public int maxStars = 5; // 5..7 по редкости (канон)
        public Sprite portrait;

        [TextArea(3, 6)]
        public string lore;

        public const int RankSlotsPerAbility = 1; // слот умения i открывается на ранге i
    }
}
