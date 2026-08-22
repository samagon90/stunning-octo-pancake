using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Верхняя панель валют. Слушает CurrencyService — обновляется событием, а не каждый кадр.
    /// </summary>
    public class CurrenciesBarUI : MonoBehaviour
    {
        [SerializeField] private Text goldLabel;
        [SerializeField] private Text crystalLabel;
        [SerializeField] private Text shardLabel;
        [SerializeField] private Text runeLabel;
        [SerializeField] private Text energyLabel;

        private CurrencyService _currencies;

        private void Start()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            _currencies = gm.Currencies;
            _currencies.CurrencyChanged += OnCurrencyChanged;
            RefreshAll();
        }

        private void OnDestroy()
        {
            if (_currencies != null) _currencies.CurrencyChanged -= OnCurrencyChanged;
        }

        private void OnCurrencyChanged(CurrencyType type, long newAmount)
        {
            switch (type)
            {
                case CurrencyType.Gold: if (goldLabel != null) goldLabel.text = Short(newAmount); break;
                case CurrencyType.Crystal: if (crystalLabel != null) crystalLabel.text = Short(newAmount); break;
                case CurrencyType.Shard: if (shardLabel != null) shardLabel.text = Short(newAmount); break;
                case CurrencyType.Rune: if (runeLabel != null) runeLabel.text = Short(newAmount); break;
                case CurrencyType.Energy: if (energyLabel != null) energyLabel.text = Short(newAmount); break;
            }
        }

        private void RefreshAll()
        {
            OnCurrencyChanged(CurrencyType.Gold, _currencies.Get(CurrencyType.Gold));
            OnCurrencyChanged(CurrencyType.Crystal, _currencies.Get(CurrencyType.Crystal));
            OnCurrencyChanged(CurrencyType.Shard, _currencies.Get(CurrencyType.Shard));
            OnCurrencyChanged(CurrencyType.Rune, _currencies.Get(CurrencyType.Rune));
            OnCurrencyChanged(CurrencyType.Energy, _currencies.Get(CurrencyType.Energy));
        }

        private static string Short(long n)
        {
            if (n >= 1_000_000) return (n / 1_000_000) + "M";
            if (n >= 1_000) return (n / 1_000) + "K";
            return n.ToString();
        }
    }
}
