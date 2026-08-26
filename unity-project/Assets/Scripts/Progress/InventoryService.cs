using System;
using System.Collections.Generic;

namespace DreamMasters.Progress
{
    /// <summary>
    /// Инвентарь: экипировка героев. В срезе — каркас: предметы, надевание на героев,
    /// «родной» сет героя (канон: сет даёт бонус всему отряду). Без заточки — она в итерации 2.
    /// </summary>
    public class InventoryService
    {
        private readonly PlayerProfile _profile;

        public InventoryService(PlayerProfile profile) => _profile = profile;

        public event Action<ItemInstance> ItemAdded;
        public event Action<ItemInstance> ItemEquipped;
    }

    /// <summary>Предмет экипировки (карккас для среза).</summary>
    [Serializable]
    public class ItemInstance
    {
        public string itemId;
        public string name;
        public int attackBonus;
        public int defenseBonus;
        public int hpBonus;
        public string boundHeroId = ""; // «родной» предмет конкретного героя
    }
}
