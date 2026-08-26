using System;
using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Data;
using DreamMasters.Services;

namespace DreamMasters.Progress
{
    /// <summary>Результат авто-боя Арены.</summary>
    public class ArenaAutoResult
    {
        public bool Victory;
        public int RatingDelta;
        public long Gold;
        public long Shards;
        public string Description;
    }

    /// <summary>
    /// Арена и Колизей (канон):
    /// — Арена: автобои, рейтинг за победу, зал славы;
    /// — Колизей: ручные бои против команд других игроков, максимум 3 поражения в день,
    ///   награды за пороги побед. Расчёт рейтинга — на сервере (клиент отправляет результат).
    /// </summary>
    public class ArenaService
    {
        private readonly PlayerProfile _profile;
        private readonly CurrencyService _currencies;

        public const int MaxDailyLosses = 3;
        public const int StartRating = 1000;

        public int Rating => _profile.arenaRating;
        public int ColosseumLossesToday { get { _profile.RollColosseumDay(); return _profile.colosseumLossesToday; } }
        public int ColosseumWinsToday { get { _profile.RollColosseumDay(); return _profile.colosseumWinsToday; } }
        public bool ColosseumAvailable => ColosseumLossesToday < MaxDailyLosses;

        public event Action Changed;

        public ArenaService(PlayerProfile profile, CurrencyService currencies)
        {
            _profile = profile;
            _currencies = currencies;
            if (_profile.arenaRating <= 0) _profile.arenaRating = StartRating;
        }

        /// <summary>Колизей: ручной бой завершён — рейтинг и награды (сервер в проде решает так же).</summary>
        public int RecordColosseum(bool victory)
        {
            _profile.RollColosseumDay();
            int delta;
            if (victory)
            {
                _profile.colosseumWinsToday++;
                delta = +20;
                _currencies.Grant(CurrencyType.Gold, 150, "colosseum_win");
                _currencies.Grant(CurrencyType.Shard, 10, "colosseum_win");
            }
            else
            {
                _profile.colosseumLossesToday++;
                delta = -10;
                _currencies.Grant(CurrencyType.Gold, 40, "colosseum_loss");
            }
            ApplyDelta(delta);
            return delta;
        }

        /// <summary>Арена: автобой. Мощь отряда vs мощь противника (псевдо-серверный расчёт).</summary>
        public ArenaAutoResult SimulateAutoFight(ArenaOpponentDto opponent, HeroCatalog catalog, HeroCollectionService heroes)
        {
            float myPower = ComputeTeamPower(_profile, catalog, heroes);

            // Мощь из рейтинга: rating 1000 ≈ 3000 условной мощи.
            float theirRatingPower = 3f * opponent.rating;
            float winChance = myPower / (myPower + theirRatingPower + 1f);
            bool victory = Random.value < winChance;

            int delta = victory ? +15 : -8;
            var result = new ArenaAutoResult
            {
                Victory = victory,
                RatingDelta = delta,
                Gold = victory ? 200 : 50,
                Shards = victory ? 12 : 3,
                Description = victory
                    ? $"Отряд разнес команду {opponent.displayName}! Рейтинг +{delta}."
                    : $"{opponent.displayName} оказался сильнее. Рейтинг {delta}."
            };
            _currencies.Grant(CurrencyType.Gold, result.Gold, "arena");
            _currencies.Grant(CurrencyType.Shard, result.Shards, "arena");
            ApplyDelta(delta);
            return result;
        }

        private void ApplyDelta(int delta)
        {
            _profile.arenaRating = Math.Max(0, _profile.arenaRating + delta);
            if (_profile.arenaRating > _profile.bestArenaRating)
                _profile.bestArenaRating = _profile.arenaRating;
            Changed?.Invoke();
        }

        /// <summary>Сила команды: статы × стихийное покрытие (канон: все 4 стихии = преимущество).</summary>
        public static float ComputeTeamPower(PlayerProfile profile, HeroCatalog catalog, HeroCollectionService heroes)
        {
            float power = 0f;
            var elements = new HashSet<int>();
            foreach (var id in profile.teamHeroIds)
            {
                var data = catalog.GetHero(id);
                var inst = profile.FindHero(id);
                if (data == null || inst == null) continue;
                var stats = inst.ComputeStats(data);
                power += stats.attack * 8f + stats.maxHp * 0.4f + stats.defense * 5f;
                elements.Add((int)data.element);
            }
            if (elements.Count >= 4) power *= 1.15f; // канон: бонус за все стихии
            return power;
        }
    }
}
