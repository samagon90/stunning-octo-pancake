using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>Одна волна врагов в уровне.</summary>
    [System.Serializable]
    public class WaveData
    {
        public EnemyData enemy;
        [Min(1)] public int count = 3;
        [Min(0f)] public float spawnInterval = 0.8f;
    }

    /// <summary>
    /// Уровень кампании: комнаты-волны + босс. Уровень живёт в мире («сне»).
    /// Assets → Create → Dream Masters → Level.
    /// </summary>
    [CreateAssetMenu(fileName = "NewLevel", menuName = "Dream Masters/Level")]
    public class LevelData : ScriptableObject
    {
        [Header("Идентификация")]
        public string levelId;
        public string displayName;
        [TextArea(2, 4)] public string introText;

        [Header("Волны (последняя обычно босс)")]
        public List<WaveData> waves = new List<WaveData>();

        [Header("Награды за прохождение (первый раз)")]
        public int goldReward = 200;
        public int crystalReward = 20;
        public int shardReward = 10;
        public int runeReward = 6; // канон: 6 рун на ранг

        [Header("Спецправила")]
        [Tooltip("Канон: самый первый бой — гарантированный проигрыш первому боссу.")]
        public bool scriptedPlayerLoss = false;
    }
}
