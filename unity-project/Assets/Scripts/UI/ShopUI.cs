using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Progress;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Магазин (каркас). Обмены за игровую валюту работают уже сейчас.
    /// Панели с пометкой «Реклама» — заготовленные слоты нативной рекламы:
    /// SDK НЕ подключаем до стабилизации (GDD §9), места уже размечены.
    /// </summary>
    public class ShopUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Button buyDustForGold;
        [SerializeField] private Button buySkillPointsForCrystals;
        [SerializeField] private GameObject nativeAdPlaceholder; // слот AdSlot.Shop
        [SerializeField] private Text statusLabel;

        private const long DustPackPrice = 5000;     // золота
        private const long DustPackAmount = 2500;    // пыли
        private const long SkillPointPrice = 50;     // кристаллов
        private const long SkillPointAmount = 5;

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() =>
            {
                if (menuUi != null) menuUi.ShowMenu();
            });
            if (buyDustForGold != null) buyDustForGold.onClick.AddListener(BuyDust);
            if (buySkillPointsForCrystals != null) buySkillPointsForCrystals.onClick.AddListener(BuySkillPoints);
            if (nativeAdPlaceholder != null) nativeAdPlaceholder.SetActive(false); // реклама появится после релиза
        }

        private void BuyDust()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            if (gm.Currencies.TrySpend(CurrencyType.Gold, DustPackPrice, "shop_dust"))
            {
                gm.Currencies.Grant(CurrencyType.Dust, DustPackAmount, "shop_dust");
                Say($"Куплено {DustPackAmount} волшебной пыли.");
            }
            else Say("Не хватает золота — сражайся!");
        }

        private void BuySkillPoints()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            if (gm.Currencies.TrySpend(CurrencyType.Crystal, SkillPointPrice, "shop_sp"))
            {
                gm.Currencies.Grant(CurrencyType.SkillPoint, SkillPointAmount, "shop_sp");
                Say($"Куплено {SkillPointAmount} очков навыков.");
            }
            else Say("Не хватает кристаллов.");
        }

        private void Say(string s) { if (statusLabel != null) statusLabel.text = s; }
    }
}
