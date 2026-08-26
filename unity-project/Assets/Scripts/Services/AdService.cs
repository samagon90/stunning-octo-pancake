using System;

namespace DreamMasters.Services
{
    /// <summary>
    /// Слоты нативной рекламы — зафиксированы заранее (GDD §9), чтобы UI не пришлось
    /// перекраивать при подключении SDK ПОСЛЕ стабилизации приложения.
    /// </summary>
    public enum AdSlot
    {
        MainMenu = 0,      // главный экран
        BattleResult = 1,  // экран результатов боя
        Shop = 2,          // магазин
        HeroFeed = 3       // лента героев
    }

    /// <summary>
    /// Монетизация (отложенная). Сейчас в игре только этот интерфейс и заглушка.
    /// Реальный SDK (AdMob Native Ads / медиация) подключается в итерации 6.
    /// </summary>
    public interface IAdService
    {
        bool IsAvailable(AdSlot slot);
        void ShowNative(AdSlot slot, Action onShown);
        void NotifyAppResumed(); // для Consent Manager/GDPR при возврате в игру
    }

    /// <summary>Заглушка: ничего не показывает, логирует вызовы. Больше ничего в срезе нет.</summary>
    public sealed class NullAdService : IAdService
    {
        public bool IsAvailable(AdSlot slot) => false;

        public void ShowNative(AdSlot slot, Action onShown)
        {
            UnityEngine.Debug.Log($"[Ads] Показ слота {slot} запрошен, но SDK рекламы ещё не подключён (по плану).");
            onShown?.Invoke();
        }

        public void NotifyAppResumed() { }
    }
}
