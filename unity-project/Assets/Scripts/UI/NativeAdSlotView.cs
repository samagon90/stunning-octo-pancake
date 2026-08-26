using UnityEngine;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Слот нативной рекламы: панель-контейнер, которая включается ТОЛЬКО когда
    /// рекламный SDK доступен (после релиза, по плану GDD §9). До этого — выключена,
    /// место в вёрстке зарезервировано и не перекраивается.
    /// </summary>
    public class NativeAdSlotView : MonoBehaviour
    {
        [SerializeField] private AdSlot slot = AdSlot.MainMenu;
        [SerializeField] private GameObject container; // сам блок рекламы
        [SerializeField] private float refreshSeconds = 60f;

        private float _timer;

        private void OnEnable() => Refresh();

        private void Update()
        {
            _timer -= Time.unscaledDeltaTime;
            if (_timer > 0f) return;
            _timer = refreshSeconds;
            Refresh();
        }

        private void Refresh()
        {
            var ads = Core.GameManager.Instance != null ? Core.GameManager.Instance.Ads : null;
            bool available = ads != null && ads.IsAvailable(slot);
            if (container != null) container.SetActive(available);
            if (available) ads.ShowNative(slot, null);
        }
    }
}
