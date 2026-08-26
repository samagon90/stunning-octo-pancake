using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// «Предсказание судьбы» — гача оригинала. Тяга за 80 осколков или за кристаллы.
    /// Дубликаты конвертируются в осколки и камень эволюции (мягкая экономика).
    /// </summary>
    public class SummonUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Button summonShardsButton;
        [SerializeField] private Button summonCrystalsButton;
        [SerializeField] private Text resultLabel;

        private const long CrystalCost = 288;

        private void Start()
        {
            if (backButton != null)
                backButton.onClick.AddListener(() => { if (menuUi != null) menuUi.ShowMenu(); });
            if (summonShardsButton != null) summonShardsButton.onClick.AddListener(() => Summon(useShards: true));
            if (summonCrystalsButton != null) summonCrystalsButton.onClick.AddListener(() => Summon(useShards: false));
        }

        private void OnEnable() => RefreshCosts();

        private void RefreshCosts()
        {
            var gm = GameManager.Instance;
            if (summonShardsButton != null)
            {
                var l = summonShardsButton.GetComponentInChildren<Text>();
                if (l != null) l.text = $"Предсказание судьбы\n({CurrencyService.ShardsPerHero} осколков)";
                summonShardsButton.interactable = gm != null &&
                    gm.Currencies.CanAfford(CurrencyType.Shard, CurrencyService.ShardsPerHero);
            }
            if (summonCrystalsButton != null)
            {
                var l = summonCrystalsButton.GetComponentInChildren<Text>();
                if (l != null) l.text = $"Предсказание судьбы\n({CrystalCost} кристаллов)";
                summonCrystalsButton.interactable = gm != null &&
                    gm.Currencies.CanAfford(CurrencyType.Crystal, CrystalCost);
            }
        }

        private void Summon(bool useShards)
        {
            var gm = GameManager.Instance;
            var found = Resources.LoadAll<HeroCatalog>("DreamMasters");
            if (gm == null || found.Length == 0) return;
            var catalog = found[0];

            bool paid = useShards
                ? gm.Currencies.TrySpend(CurrencyType.Shard, CurrencyService.ShardsPerHero, "summon")
                : gm.Currencies.TrySpend(CurrencyType.Crystal, CrystalCost, "summon");
            if (!paid) return;

            var candidates = new List<HeroData>();
            foreach (var h in catalog.heroes)
                if (h != null) candidates.Add(h);
            if (candidates.Count == 0) return;

            var pick = candidates[Random.Range(0, candidates.Count)];
            bool duplicate = gm.Profile.FindHero(pick.heroId) != null;
            gm.Heroes.Obtain(pick.heroId);

            string text;
            if (duplicate)
            {
                // Дубликат: часть ресурсов возвращается
                gm.Currencies.Grant(CurrencyType.Shard, CurrencyService.ShardsPerHero / 2, "dupe");
                gm.Currencies.Grant(CurrencyType.EvolutionStone, 1, "dupe");
                text = $"{pick.heroName} уже служит тебе!\nВозвращено 40 осколков и камень эволюции.";
            }
            else
            {
                text = $"Судьба привела: {pick.heroName}!\n{pick.element.RuName()}, {HeroEnumNames.Roles[(int)pick.role]} — герой присоединился к коллекции!";
            }

            if (resultLabel != null) resultLabel.text = text;
            Debug.Log("[Summon] " + text);
            gm.Save.Save(gm.Profile);
            RefreshCosts();
        }
    }
}
