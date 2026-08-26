using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Battle;
using DreamMasters.Core;

namespace DreamMasters.UI
{
    /// <summary>
    /// Боевой HUD: 4 портрета героев, 4 кнопки умений выбранного героя (заливка кулдауна),
    /// автобой, ускорение ×2. Итог боя показывает BattleResultUI (отдельная панель).
    /// </summary>
    public class BattleHUD : MonoBehaviour
    {
        [Header("Ссылки (назначить в Инспекторе)")]
        [SerializeField] private Button[] heroButtons = new Button[4];
        [SerializeField] private Image[] heroButtonIcons = new Image[4];
        [SerializeField] private Button[] abilityButtons = new Button[4];
        [SerializeField] private Image[] abilityCooldownFills = new Image[4];
        [SerializeField] private Button autoButton;
        [SerializeField] private Button speedButton;
        [SerializeField] private Text waveLabel;

        private int _selectedHero;
        private readonly BattleUnit[] _units = new BattleUnit[4];
        private BattleUnit Selected => _selectedHero < _units.Length ? _units[_selectedHero] : null;

        private void Start()
        {
            var bm = BattleManager.Instance;
            if (bm == null) return;

            for (int i = 0; i < bm.Heroes.Count && i < _units.Length; i++) _units[i] = bm.Heroes[i];
            for (int i = 0; i < heroButtons.Length; i++)
            {
                int idx = i;
                if (heroButtons[i] != null) heroButtons[i].onClick.AddListener(() => SelectHero(idx));
            }
            for (int i = 0; i < abilityButtons.Length; i++)
            {
                int idx = i;
                if (abilityButtons[i] != null) abilityButtons[i].onClick.AddListener(() => CastAbility(idx));
            }
            if (autoButton != null) autoButton.onClick.AddListener(BattleManager.ToggleAuto);
            if (speedButton != null) speedButton.onClick.AddListener(BattleManager.ToggleSpeed);

            bm.HeroesChanged += OnHeroesChanged;
            SelectHero(0);
        }

        private void OnDestroy()
        {
            var bm = BattleManager.Instance;
            if (bm != null) bm.HeroesChanged -= OnHeroesChanged;
        }

        private void OnHeroesChanged(System.Collections.Generic.IReadOnlyList<BattleUnit> units)
        {
            for (int i = 0; i < units.Count && i < _units.Length; i++) _units[i] = units[i];
        }

        private void SelectHero(int index)
        {
            if (index < 0 || index >= _units.Length || _units[index] == null) return;
            _selectedHero = index;
            for (int i = 0; i < heroButtonIcons.Length; i++)
                if (heroButtonIcons[i] != null)
                    heroButtonIcons[i].transform.localScale = i == index ? Vector3.one * 1.15f : Vector3.one;
        }

        private void CastAbility(int abilityIndex)
        {
            var unit = Selected;
            if (unit != null) unit.TryCastManually(abilityIndex);
        }

        private void Update()
        {
            // Ручное управление выбранным героем джойстиком (остальные — ИИ).
            var unit = Selected;
            if (unit != null && unit.IsAlive && VirtualJoystick.Instance != null &&
                VirtualJoystick.Instance.IsActive && !BattleManager.AutoMode)
                unit.transform.position += new Vector3(
                    VirtualJoystick.Instance.Direction.x, 0f,
                    VirtualJoystick.Instance.Direction.y) * (unit.Stats.moveSpeed * Time.deltaTime);

            RefreshCooldowns();
            RefreshWaveLabel();
        }

        private void RefreshCooldowns()
        {
            var unit = Selected;
            if (unit == null) return;
            for (int i = 0; i < abilityCooldownFills.Length; i++)
            {
                if (abilityCooldownFills[i] == null) continue;
                float readiness = unit.GetAbilityReadiness(i);
                abilityCooldownFills[i].fillAmount = readiness;
                if (abilityButtons[i] != null) abilityButtons[i].interactable = readiness >= 1f;
            }
        }

        private void RefreshWaveLabel()
        {
            if (waveLabel == null) return;
            var wc = WaveController.Active;
            if (wc != null && wc.TotalWaves > 0)
                waveLabel.text = $"Волна {Mathf.Min(wc.CurrentWave + 1, wc.TotalWaves)} / {wc.TotalWaves}";
        }
    }
}
