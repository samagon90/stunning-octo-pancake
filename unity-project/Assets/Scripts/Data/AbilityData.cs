using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>Тип цели умения — как в оригинале: одиночный, по площади, по прямой, лечение, баф.</summary>
    public enum AbilityTargetType
    {
        SingleTarget = 0,
        AoeRadius = 1,
        Line = 2,
        HealAlly = 3,
        BuffTeam = 4
    }

    /// <summary>
    /// Умение героя. ScriptableObject — контент добавляется без правки кода.
    /// Assets → Create → Dream Masters → Ability.
    /// </summary>
    [CreateAssetMenu(fileName = "NewAbility", menuName = "Dream Masters/Ability")]
    public class AbilityData : ScriptableObject
    {
        [Header("Идентификация")]
        public string abilityId;
        public string displayName;

        [TextArea(2, 4)]
        public string description;

        [Header("Параметры")]
        public AbilityTargetType targetType = AbilityTargetType.SingleTarget;
        [Tooltip("Множитель от атаки героя. 1.5 = 150% АТК.")]
        public float powerCoefficient = 1.5f;
        public float cooldownSeconds = 8f;
        public float castRange = 6f;
        [Tooltip("Радиус для AoeRadius / ширина для Line.")]
        public float effectRadius = 3f;

        [Header("Лечение/баф (для HealAlly, BuffTeam)")]
        [Tooltip("Для лечения: множитель от атаки. Для бафа: % усиления, напр. 0.2 = +20%.")]
        public float supportValue = 1.0f;
        public float buffDuration = 5f;

        public const int MaxAbilitiesPerHero = 4; // канон: ровно 4 активных навыка
    }
}
