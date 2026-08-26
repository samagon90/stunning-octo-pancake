using System;
using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Data;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Формула урона. Единственная точка правды для PvP и PvE (чтобы арена считалась одинаково).
    /// Урон = АТК × к-т умения × стихия × крит − защита.
    /// </summary>
    public static class DamageCalculator
    {
        public static float Compute(
            float attack,
            float defense,
            float abilityCoefficient,
            Element attackerElement,
            Element defenderElement,
            float critChance,
            float critDamage,
            float elementAdvantage = 1.25f,
            float elementDisadvantage = 0.80f,
            float incomingMultiplier = 1f)
        {
            bool crit = Random.value < critChance;
            float elementMult = ElementRules.GetDamageMultiplier(attackerElement, defenderElement, elementAdvantage, elementDisadvantage);
            float raw = attack * abilityCoefficient * elementMult;
            float mitigated = raw * (100f / (100f + Mathf.Max(0f, defense)));
            if (crit) mitigated *= critDamage;
            mitigated *= incomingMultiplier;
            return Mathf.Max(1f, mitigated);
        }

        public static float SynergyMultiplier(SynergyBonusType type, List<SynergyData> synergies, float baseStat)
        {
            float bonus = 0f;
            for (int i = 0; i < synergies.Count; i++)
                if (synergies[i].bonusType == type) bonus += synergies[i].value;
            return baseStat * (1f + bonus);
        }

        public static float SynergyFlat(SynergyBonusType type, List<SynergyData> synergies)
        {
            float bonus = 0f;
            for (int i = 0; i < synergies.Count; i++)
                if (synergies[i].bonusType == type) bonus += synergies[i].value;
            return bonus;
        }
    }
}
