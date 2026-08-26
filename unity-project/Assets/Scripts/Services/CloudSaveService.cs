using System.Collections.Generic;
using System.Threading.Tasks;
using DreamMasters.Core;
using DreamMasters.Progress;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// Облачные сохранения поверх REST (Cloud Functions: /profile GET/PUT).
    /// Активируется заполнением apiBaseUrl в GameConfig — код менять не нужно.
    /// Ошибка сети НЕ ломает игру: локальный профиль остаётся истиной (урок оригинала).
    /// </summary>
    public class CloudSaveService
    {
        private readonly RestApiClient _api;

        public CloudSaveService(GameConfig config)
        {
            _api = new RestApiClient(config != null ? config.apiBaseUrl : "");
        }

        public async Task<bool> PushAsync(PlayerProfile profile)
        {
            if (profile == null || _api == null) return false;
            string json = JsonUtility.ToJson(profile);
            var resp = await _api.PostAsync($"/profile?accountId={profile.anonymousId}", json);
            if (!resp.Ok) Debug.LogWarning("[CloudSave] Push не удался: " + resp.Error);
            return resp.Ok;
        }

        public async Task<PlayerProfile> PullAsync(string accountId)
        {
            var resp = await _api.GetAsync("/profile?accountId=" + accountId);
            if (!resp.Ok || string.IsNullOrEmpty(resp.Data)) return null;
            try { return JsonUtility.FromJson<PlayerProfile>(resp.Data); }
            catch { return null; }
        }
    }
}
