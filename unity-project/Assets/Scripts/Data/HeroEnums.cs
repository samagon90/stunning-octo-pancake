namespace DreamMasters.Data
{
    /// <summary>Пять направлений-категорий героев оригинала. Влияет на синергии.</summary>
    public enum HeroCategory
    {
        Legend = 0,   // Легенды
        Myth = 1,     // Мифы
        Tale = 2,     // Сказки
        Saga = 3,     // Предания
        Other = 4     // Другие
    }

    /// <summary>Дальнобойность героя. Ближняя — танки, средняя — дамагеры, дальняя — саппорты.</summary>
    public enum AttackRange
    {
        Melee = 0,   // ближняя
        Mid = 1,     // средняя
        Ranged = 2   // дальняя
    }

    /// <summary>Боевая роль.</summary>
    public enum HeroRole
    {
        Tank = 0,      // сдерживает врага
        Damage = 1,    // основной урон
        Support = 2,   // лечение и усиление
        Universal = 3  // универсал
    }

    public static class HeroEnumNames
    {
        public static readonly string[] Categories = { "Легенды", "Мифы", "Сказки", "Предания", "Другие" };
        public static readonly string[] Ranges = { "Ближний", "Средний", "Дальний" };
        public static readonly string[] Roles = { "Танк", "Боец", "Поддержка", "Универсал" };
    }
}
