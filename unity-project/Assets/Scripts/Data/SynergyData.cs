using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>Вид бонуса синергии.</summary>
    public enum SynergyBonusType
    {
        AttackPercent = 0,   // + % атаки
        DefensePercent = 1,  // + % защиты
        HpPercent = 2,       // + % здоровья
        CritChance = 3       // + шанс крита (0..1)
    }

    /// <summary>
    /// Парная синергия героев (канон: Чейни+Эш = +20% атаки в одном отряде).
    /// Assets → Create → Dream Masters → Synergy.
    /// </summary>
    [CreateAssetMenu(fileName = "NewSynergy", menuName = "Dream Masters/Synergy")]
    public class SynergyData : ScriptableObject
    {
        [Header("Пара героев")]
        public HeroData heroA;
        public HeroData heroB;

        [Header("Бонус обоим, пока в одном отряде")]
        public SynergyBonusType bonusType = SynergyBonusType.AttackPercent;
        [Range(0f, 1f)] public float value = 0.20f;

        public string Describe()
        {
            string stat = bonusType switch
            {
                SynergyBonusType.AttackPercent => "атаки",
                SynergyBonusType.DefensePercent => "защиты",
                SynergyBonusType.HpPercent => "здоровья",
                _ => "шанса крита"
            };
            return $"{heroA?.heroName} + {heroB?.heroName}: +{value * 100f:0}% {stat}";
        }
    }
}
