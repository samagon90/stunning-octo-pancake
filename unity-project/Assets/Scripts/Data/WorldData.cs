using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>
    /// Мир-«сон» кампании (канон: 9 миров). 15 уровней, тема-стихия и Мастер сна —
    /// финальный босс, который после победы ПРИСОЕДИНЯЕТСЯ к отряду игрока.
    /// Assets → Create → Dream Masters → World (но всё уже сгенерировано).
    /// </summary>
    [CreateAssetMenu(fileName = "NewWorld", menuName = "Dream Masters/World")]
    public class WorldData : ScriptableObject
    {
        public string worldId;
        public string worldName;
        public Element themeElement;
        [TextArea(2, 4)] public string description;
        public List<LevelData> levels = new List<LevelData>();

        [Header("Мастер этого сна: финальный босс 15-го уровня, присоединяется после победы")]
        public HeroData bossHero;
    }
}
