using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using DreamMasters.Progress;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// Локальная заглушка сети: имитирует задержку и ответы сервера.
    /// 1) позволяет играть офлайн (бои считаются на клиенте — сервер лишь валидирует);
    /// 2) точка подмены на реальный API (Firebase Functions / свой бэкенд) в итерации 3.
    /// </summary>
    public class LocalNetworkStub : INetworkService
    {
        private const int SimulatedLatencyMs = 120;
        private static readonly Task Completed = Task.CompletedTask;

        public bool IsOnline => Application.internetReachability != NetworkReachability.NotReachable;
        public event Action<bool> ConnectionChanged;

        public LocalNetworkStub()
        {
            // Мобильный интернет рвётся часто — следим и сообщаем UI (GDD §10, устойчивость).
            SimulatorTick();
        }

        private async void SimulatorTick()
        {
            bool wasOnline = IsOnline;
            while (true)
            {
                await Task.Delay(2000);
                bool now = IsOnline;
                if (now != wasOnline)
                {
                    wasOnline = now;
                    ConnectionChanged?.Invoke(now);
                }
            }
        }

        public async Task<ApiResponse<bool>> SyncProfile(PlayerProfile profile)
        {
            await Task.Delay(SimulatedLatencyMs);
            return new ApiResponse<bool> { Ok = true, Data = true };
        }

        public async Task<ApiResponse<Dictionary<CurrencyType, long>>> SubmitBattleResult(BattleResultDto result)
        {
            await Task.Delay(SimulatedLatencyMs);
            // Валидация наград будет на сервере (античит). Пока — зеркалим ожидаемую награду.
            var rewards = new Dictionary<CurrencyType, long>
            {
                [CurrencyType.Gold] = result.victory ? 200 : 50,
                [CurrencyType.Shard] = result.victory ? 10 : 2,
                [CurrencyType.Rune] = result.victory ? 6 : 1
            };
            return new ApiResponse<Dictionary<CurrencyType, long>> { Ok = true, Data = rewards };
        }

        public async Task<ApiResponse<List<ArenaOpponentDto>>> FetchArenaOpponents(int playerRating)
        {
            await Task.Delay(SimulatedLatencyMs);
            var list = new List<ArenaOpponentDto>
            {
                new ArenaOpponentDto { displayName = "МастерОгня", rating = playerRating + 25 },
                new ArenaOpponentDto { displayName = "СнежнаяДева", rating = playerRating - 10 },
                new ArenaOpponentDto { displayName = "ДревоЖизни", rating = playerRating + 5 }
            };
            return new ApiResponse<List<ArenaOpponentDto>> { Ok = true, Data = list };
        }
    }
}
