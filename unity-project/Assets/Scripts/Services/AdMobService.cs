using System;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// AdMob-реализация IAdService (НАТИВНАЯ РЕКЛАМА — подключается ПОСЛЕ релиза, GDD §9).
    ///
    /// КАК ВКЛЮЧИТЬ (когда придёт время — см. docs/ADS-SETUP.md):
    /// 1. Импортировать Google Mobile Ads Unity Plugin (Package Manager → по URL с GitHub releases).
    /// 2. Player Settings → Scripting Define Symbols → добавить DMR_ADMOB.
    /// 3. Заполнить AppId / NativeAdUnitId (тестовые ID из документации Google).
    /// 4. В GameManager заменить new NullAdService() на new AdMobService().
    /// 5. Consent: перед загрузкой рекламы вызвать ConsentInformation.Update (GDPR),
    ///    персонализация берётся из Profile.adsPersonalized (тумблер в настройках).
    ///
    /// Сейчас файл НЕ компилируется в билд (guard DMR_ADMOB) — проект живёт без SDK.
    /// </summary>
    public sealed class AdMobService : IAdService
    {
#if DMR_ADMOB
        // TODO после импорта плагина:
        // private NativeAd _nativeAd;
        // public AdMobService(string nativeAdUnitId) { MobileAds.Initialize(_ => LoadNative(nativeAdUnitId)); }
        // private void LoadNative(string id) { NativeAd.LoadNativeAd(new AdRequest.Builder().Build(), id, ...); }
        // IsAvailable: _nativeAd != null && _nativeAd.IsLoaded();
        // ShowNative: регистрировать GameObject-контейнеры (NativeAd.RegisterNativeAdSceneObject...)
#endif

        private const string TestNativeUnitId = "ca-app-pub-3940256099942544/2247696110"; // тестовый ID Google

        public bool IsAvailable(AdSlot slot)
        {
#if DMR_ADMOB
            return false; // TODO: return _nativeAd != null && _nativeAd.IsLoaded();
#else
            return false;
#endif
        }

        public void ShowNative(AdSlot slot, Action onShown)
        {
#if DMR_ADMOB
            Debug.Log($"[AdMob] Показ нативной рекламы в слоте {slot} (unit {TestNativeUnitId}).");
            onShown?.Invoke();
#else
            Debug.LogWarning("[AdMob] SDK не подключён (символ DMR_ADMOB не задан). По плану реклама включается после релиза.");
            onShown?.Invoke();
#endif
        }

        public void NotifyAppResumed()
        {
            // TODO: Consent Information / GDPR refresh при возврате в приложение.
        }
    }
}
