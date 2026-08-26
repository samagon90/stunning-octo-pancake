using DreamMasters.Data;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Рантайм-состояние умения в бою: кулдаун и уровень (уровень ≤ уровня героя — канон).
    /// </summary>
    public class AbilityRuntime
    {
        public readonly AbilityData Data;
        public int Level;              // 0 = слот ещё не открыт (зависит от ранга героя)
        public float CooldownRemaining { get; private set; }

        public bool IsReady => Level > 0 && CooldownRemaining <= 0f;

        public AbilityRuntime(AbilityData data, int level)
        {
            Data = data;
            Level = level;
        }

        public void Tick()
        {
            if (CooldownRemaining > 0f) CooldownRemaining -= UnityEngine.Time.deltaTime;
        }

        public void Cast() => CooldownRemaining = Data.cooldownSeconds;

        /// <summary>0..1 — доля готовности для UI-кнопки (заливка кулдауна).</summary>
        public float Readiness01 => Data.cooldownSeconds <= 0f ? 1f : 1f - (CooldownRemaining / Data.cooldownSeconds);
    }
}
