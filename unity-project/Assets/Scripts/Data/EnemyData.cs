using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>
    /// Враг/босс. Для среза — общий формат: моб и босс отличаются флагом isBoss.
    /// Assets → Create → Dream Masters → Enemy.
    /// </summary>
    [CreateAssetMenu(fileName = "NewEnemy", menuName = "Dream Masters/Enemy")]
    public class EnemyData : ScriptableObject
    {
        [Header("Идентификация")]
        public string enemyId;
        public string displayName;
        public Element element = Element.Fire;
        public bool isBoss;

        [Header("Характеристики")]
        public HeroStatsBlock stats = new HeroStatsBlock();
        [Range(0, 5)] public int abilitiesUnlocked = 0; // сколько умений использует ИИ

        [Header("Награда за убийство")]
        public int goldReward = 50;
        public int shardReward = 0;   // осколки героя
        public int runeReward = 0;    // руны ранга

        public GameObject viewPrefab; // 3D-модель (прототип: капсула/куб)
    }
}
