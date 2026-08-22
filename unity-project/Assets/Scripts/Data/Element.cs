using UnityEngine;

namespace DreamMasters.Data
{
    /// <summary>Стихии героев. Цикл превосходства оригинала: Огонь > Воздух > Земля > Вода > Огонь.</summary>
    public enum Element
    {
        Fire = 0,  // Огонь
        Air = 1,   // Воздух
        Earth = 2, // Земля
        Water = 3  // Вода
    }

    /// <summary>Правила взаимодействия стихий — единственный источник истины для боя и арены.</summary>
    public static class ElementRules
    {
        /// <summary>Какая стихия доминирует над данной (кто бьёт её сильнее).</summary>
        public static Element Dominates(this Element e) => (Element)(((int)e + 1) % 4);
        // Fire -> Air (огонь силён против воздуха), Air -> Earth, Earth -> Water, Water -> Fire.

        /// <summary>Множитель урона атакующего по защитнику с учётом стихий.</summary>
        public static float GetDamageMultiplier(Element attacker, Element defender, float advantage = 1.25f, float disadvantage = 0.80f)
        {
            if (attacker.Dominates() == defender) return advantage;
            if (defender.Dominates() == attacker) return disadvantage;
            return 1f;
        }

        public static readonly string[] RuNames = { "Огонь", "Воздух", "Земля", "Вода" };
        public static string RuName(this Element e) => RuNames[(int)e];
    }
}
