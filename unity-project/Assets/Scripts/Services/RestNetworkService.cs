using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using DreamMasters.Progress;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// Сетевой сервис поверх REST (Cloud Functions: /battleResult, /arenaOpponents).
    /// Включается apiBaseUrl в GameConfig. Сервер — авторитет по наградам и рейтингу
    /// (античит: клиент присылает результат, сервер решает сколько дать).
    /// </summary>
    public class RestNetworkService : INetworkService
    {
        private readonly RestApiClient _api;

        public bool IsOnline => Application.internetReachability != NetworkReachability.NotReachable;
        public event Action<bool> ConnectionChanged;

        public RestNetworkService(string baseUrl)
        {
            _api = new RestApiClient(baseUrl);
        }

        public async Task<ApiResponse<bool>> SyncProfile(PlayerProfile profile)
        {
            if (!IsOnline) return new ApiResponse<bool> { Ok = false, Error = "offline" };
            string json = JsonUtility.ToJson(profile);
            var resp = await _api.PostAsync("/profile?accountId=" + profile.anonymousId, json);
            return new ApiResponse<bool> { Ok = resp.Ok, Error = resp.Error, Data = resp.Ok };
        }

        public async Task<ApiResponse<Dictionary<CurrencyType, long>>> SubmitBattleResult(BattleResultDto result)
        {
            if (!IsOnline) return Offline<Dictionary<CurrencyType, long>>("offline");
            string json = JsonUtility.ToJson(result);
            var resp = await _api.PostAsync("/battleResult", json);
            if (!resp.Ok) return Offline<Dictionary<CurrencyType, long>>(resp.Error);
            return new ApiResponse<Dictionary<CurrencyType, long>>
            {
                Ok = true,
                Data = ParseRewards(resp.Data) // {"gold":200,"shard":10,"rune":6}
            };
        }

        public async Task<ApiResponse<List<ArenaOpponentDto>>> FetchArenaOpponents(int playerRating)
        {
            if (!IsOnline) return Offline<List<ArenaOpponentDto>>("offline");
            var resp = await _api.GetAsync("/arenaOpponents?rating=" + playerRating);
            if (!resp.Ok) return Offline<List<ArenaOpponentDto>>(resp.Error);
            // Сервер вернёт JSON — полный парсер добавит типы DTO; заготовка под итерацию 4.
            return new ApiResponse<List<ArenaOpponentDto>> { Ok = true, Data = new List<ArenaOpponentDto>() };
        }

        private static ApiResponse<T> Offline<T>(string error) => new ApiResponse<T> { Ok = false, Error = error };

        private static Dictionary<CurrencyType, long> ParseRewards(string json)
        {
            var dict = new Dictionary<CurrencyType, long>();
            if (string.IsNullOrEmpty(json)) return dict;
            // Минимальный парсер {"gold":N,"shard":N,"rune":N}
            foreach (var pair in json.Trim('{', '}').Split(','))
            {
                var kv = pair.Split(':');
                if (kv.Length != 2) continue;
                string key = kv[0].Trim().Trim('"');
                if (!long.TryParse(kv[1].Trim('"'), out long value)) continue;
                switch (key)
                {
                    case "gold": dict[CurrencyType.Gold] = value; break;
                    case "crystal": dict[CurrencyType.Crystal] = value; break;
                    case "shard": dict[CurrencyType.Shard] = value; break;
                    case "rune": dict[CurrencyType.Rune] = value; break;
                }
            }
            return dict;
        }
    }
}
