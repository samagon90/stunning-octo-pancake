using System;

namespace DreamMasters.Progress
{
    /// <summary>
    /// Движок валют. Все изменения проходят через него — позже серверные транзакции
    /// встанут сюда без изменения геймплея (GDD §9: монетизация добавляется после релиза).
    /// </summary>
    public class CurrencyService
    {
        private readonly PlayerProfile _profile;

        public event Action<CurrencyType, long> CurrencyChanged; // тип, новый баланс

        public CurrencyService(PlayerProfile profile) => _profile = profile;

        public long Get(CurrencyType type) => _profile.GetCurrency(type);

        public bool CanAfford(CurrencyType type, long amount) => Get(type) >= amount;

        public bool TrySpend(CurrencyType type, long amount, string reason = null)
        {
            if (amount < 0) throw new ArgumentOutOfRangeException(nameof(amount), "Сумма должна быть ≥ 0.");
            if (!CanAfford(type, amount)) return false;
            _profile.SetCurrency(type, Get(type) - amount);
            CurrencyChanged?.Invoke(type, Get(type));
            return true;
        }

        public void Grant(CurrencyType type, long amount, string reason = null)
        {
            if (amount < 0) throw new ArgumentOutOfRangeException(nameof(amount), "Сумма должна быть ≥ 0.");
            _profile.SetCurrency(type, Get(type) + amount);
            CurrencyChanged?.Invoke(type, Get(type));
        }

        /// <summary>Осколки: канон — 80 осколков = гарантированный герой.</summary>
        public const int ShardsPerHero = 80;

        // ---------- Реген энергии (канон: энергия восстанавливается со временем) ----------
        public const int MaxEnergy = 60;
        private static readonly System.TimeSpan EnergyTick = System.TimeSpan.FromMinutes(6); // +1 за 6 минут

        /// <summary>Догоняет накопленную энергию по времени, прошедшему с прошлого тика.</summary>
        public void RegenerateEnergy(PlayerProfile profile)
        {
            System.DateTime last = ParseOrNow(profile.energyRegenUtc);
            System.DateTime now = System.DateTime.UtcNow;
            if (now <= last) return;
            long ticks = (long)(now - last).Ticks / EnergyTick.Ticks;
            if (ticks <= 0) return;
            long current = profile.GetCurrency(CurrencyType.Energy);
            long gained = System.Math.Min(ticks, System.Math.Max(0, MaxEnergy - current));
            if (gained > 0) Grant(CurrencyType.Energy, gained, "regen");
            profile.energyRegenUtc = now.ToString("o");
        }

        private static System.DateTime ParseOrNow(string iso)
        {
            if (System.DateTime.TryParse(iso, null, System.Globalization.DateTimeStyles.RoundtripKind, out var dt))
                return dt.ToUniversalTime();
            return System.DateTime.UtcNow;
        }
    }
}
