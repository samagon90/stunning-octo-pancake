using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using DreamMasters.Progress;

namespace DreamMasters.Services
{
    /// <summary>Результат обращения к серверу (версия протокола — для совместимости клиентов).</summary>
    public class ApiResponse<T>
    {
        public bool Ok;
        public string Error;
        public T Data;
        public int protocolVersion = 1;
    }

    /// <summary>Итог боя, отправляемый на сервер для валидации наград.</summary>
    [Serializable]
    public class BattleResultDto
    {
        public string levelId;
        public bool victory;
        public int secondsElapsed;
        public List<string> teamHeroIds;
        public long damageDealt;
        public int protocolVersion = 1;
    }

    /// <summary>Противник арены (мок-структура, сервер пришлёт такие же).</summary>
    [Serializable]
    public class ArenaOpponentDto
    {
        public string displayName;
        public int rating;
        public List<string> teamHeroIds;
    }

    /// <summary>
    /// Сетевой слой за интерфейсом: сейчас работает локальная заглушка,
    /// позже подключается Firebase/свой бэкенд БЕЗ правок геймплея.
    /// Правило: клиент отправляет намерения, сервер возвращает результат (античит, GDD §10).
    /// </summary>
    public interface INetworkService
    {
        bool IsOnline { get; }
        Task<ApiResponse<bool>> SyncProfile(PlayerProfile profile);
        Task<ApiResponse<Dictionary<CurrencyType, long>>> SubmitBattleResult(BattleResultDto result);
        Task<ApiResponse<List<ArenaOpponentDto>>> FetchArenaOpponents(int playerRating);
        event Action<bool> ConnectionChanged; // реконнект-логика: UI слушает и показывает статус
    }
}
