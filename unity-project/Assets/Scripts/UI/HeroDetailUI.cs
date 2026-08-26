using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Карточка героя: статы и все канонные способы прокачки —
    /// уровень (пыль), звёзды (осколки+камень), ранг (6 рун+камень), пробуждение,
    /// апгрейд умений (золото+очко навыка). Все кнопки сами проверяют валюты.
    /// </summary>
    public class HeroDetailUI : MonoBehaviour
    {
        [SerializeField] private Text titleLabel;
        [SerializeField] private Text statsLabel;
        [SerializeField] private Text statusLabel;
        [SerializeField] private Button levelUpButton;
        [SerializeField] private Button starUpButton;
        [SerializeField] private Button rankUpButton;
        [SerializeField] private Button awakenButton;
        [SerializeField] private Button[] abilityButtons = new Button[4];
        [SerializeField] private Button closeButton;

        private HeroInstance _instance;
        private HeroData _data;
        private HeroCollectionService _heroes;
        private CurrencyService _currencies;
        private bool _bound;

        public void Open(HeroInstance instance)
        {
            var gm = GameManager.Instance;
            if (gm == null || instance == null) return;
            _instance = instance;
            _heroes = gm.Heroes;
            _currencies = gm.Currencies;
            _data = _heroes.GetData(instance);
            if (!_bound)
            {
                BindButtons();
                _bound = true;
            }
            Refresh();
        }

        private void BindButtons()
        {
            if (levelUpButton != null) levelUpButton.onClick.AddListener(OnLevelUp);
            if (starUpButton != null) starUpButton.onClick.AddListener(OnStarUp);
            if (rankUpButton != null) rankUpButton.onClick.AddListener(OnRankUp);
            if (awakenButton != null) awakenButton.onClick.AddListener(OnAwaken);
            for (int i = 0; i < abilityButtons.Length; i++)
            {
                if (abilityButtons[i] == null) continue;
                int idx = i;
                abilityButtons[i].onClick.AddListener(() => OnUpgradeAbility(idx));
            }
            if (closeButton != null) closeButton.onClick.AddListener(() => gameObject.SetActive(false));
        }

        private void Refresh()
        {
            if (_instance == null || _data == null) return;
            var stats = _instance.ComputeStats(_data);

            if (titleLabel != null)
                titleLabel.text = $"{_data.heroName} — {_data.element.RuName()}, ур.{_instance.level}, " +
                                  $"{new string('★', _instance.stars)} ({_instance.stars}/{_data.maxStars}), ранг {_instance.rank}";

            if (statsLabel != null)
                statsLabel.text =
                    $"ХП: {stats.maxHp:0}\nАТК: {stats.attack:0}\nЗАЩ: {stats.defense:0}\n" +
                    $"Скор.атаки: {stats.attackSpeed:0.0}\nКрит: {stats.critChance * 100f:0}% (×{stats.critDamage:0.0})\n" +
                    $"Роль: {HeroEnumNames.Roles[(int)_data.role]}, {HeroEnumNames.Ranges[(int)_data.attackRange]}\n" +
                    $"Категория: {HeroEnumNames.Categories[(int)_data.category]}" +
                    (_instance.awakened ? "\n<ПРОБУЖДЁН>" : "");

            if (statusLabel != null) statusLabel.text = "";

            if (levelUpButton != null)
            {
                long cost = HeroCollectionService.DustCostForLevel(_instance.level + 1);
                bool maxed = _instance.level >= HeroCollectionService.MaxLevel;
                levelUpButton.interactable = !maxed && _currencies.CanAfford(CurrencyType.Dust, cost);
                var l = levelUpButton.GetComponentInChildren<Text>();
                if (l != null) l.text = maxed ? "Макс. уровень" : $"Уровень ↑ ({cost} пыли)";
            }
            if (starUpButton != null)
            {
                bool can = _instance.stars < _data.maxStars &&
                           _currencies.CanAfford(CurrencyType.Shard, CurrencyService.ShardsPerHero) &&
                           _currencies.CanAfford(CurrencyType.EvolutionStone, 1);
                starUpButton.interactable = can;
                var l = starUpButton.GetComponentInChildren<Text>();
                if (l != null) l.text = _instance.stars >= _data.maxStars ? "Макс. звёзды" : $"Звезда ↑ (80 осколков + камень)";
            }
            if (rankUpButton != null)
            {
                bool can = _instance.rank < HeroRank.Purple &&
                           _currencies.CanAfford(CurrencyType.Rune, HeroCollectionService.RunesPerRank) &&
                           _currencies.CanAfford(CurrencyType.EvolutionStone, 1);
                rankUpButton.interactable = can;
                var l = rankUpButton.GetComponentInChildren<Text>();
                if (l != null) l.text = _instance.rank >= HeroRank.Purple ? "Макс. ранг" : $"Ранг ↑ (6 рун + камень)";
            }
            if (awakenButton != null)
            {
                awakenButton.interactable = _instance.CanAwaken(_data) && _currencies.CanAfford(CurrencyType.EvolutionStone, 10);
                var l = awakenButton.GetComponentInChildren<Text>();
                if (l != null) l.text = _instance.awakened ? "Пробуждён" : "Пробуждение (10 камней)";
            }
            for (int i = 0; i < abilityButtons.Length; i++)
            {
                if (abilityButtons[i] == null) continue;
                var l = abilityButtons[i].GetComponentInChildren<Text>();
                int lvl = i < _instance.abilityLevels.Length ? _instance.abilityLevels[i] : 0;
                var ability = _data.abilities.Count > i ? _data.abilities[i] : null;
                if (l != null)
                    l.text = ability == null ? "-" :
                        (lvl == 0 ? $"{ability.displayName} [ранг]" : $"{ability.displayName} ур.{lvl} ↑");
                bool can = lvl > 0 && lvl < _instance.level &&
                           _currencies.CanAfford(CurrencyType.Gold, 100L * lvl) &&
                           _currencies.CanAfford(CurrencyType.SkillPoint, 1);
                abilityButtons[i].interactable = can;
            }
        }

        private void OnLevelUp()
        {
            if (_heroes.TryLevelUp(_instance, _currencies)) Refresh();
            else if (statusLabel != null) statusLabel.text = "Не хватает волшебной пыли.";
        }

        private void OnStarUp()
        {
            if (_heroes.TryStarUp(_instance, _currencies)) Refresh();
            else if (statusLabel != null) statusLabel.text = "Нужно 80 осколков и камень эволюции.";
        }

        private void OnRankUp()
        {
            if (_heroes.TryRankUp(_instance, _currencies)) Refresh();
            else if (statusLabel != null) statusLabel.text = "Нужно 6 рун и камень эволюции.";
        }

        private void OnAwaken()
        {
            if (_heroes.TryAwaken(_instance, _currencies)) Refresh();
            else if (statusLabel != null) statusLabel.text = "Пробуждение: макс. звёзды + фиолетовый ранг + 10 камней.";
        }

        private void OnUpgradeAbility(int index)
        {
            if (_heroes.TryUpgradeAbility(_instance, index, _currencies)) Refresh();
            else if (statusLabel != null) statusLabel.text = "Умение ≤ уровня героя; нужно золото и очко навыка.";
        }
    }
}
