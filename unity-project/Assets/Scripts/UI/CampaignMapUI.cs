using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Карта кампании: полоса миров снов (9 штук) + уровни выбранного мира.
    /// Мир открывается зачисткой предыдущего. Финальный уровень мира — Мастер сна,
    /// который после победы присоединяется (канон). Вход — 6 энергии.
    /// </summary>
    public class CampaignMapUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Text worldTitleLabel;
        [SerializeField] private Text worldDescLabel;
        [SerializeField] private Transform worldsStrip;     // LayoutGroup: кнопки миров
        [SerializeField] private Transform levelsContainer; // LayoutGroup: кнопки уровней
        [SerializeField] private Button worldButtonPrefab;
        [SerializeField] private Button levelButtonPrefab;
        [SerializeField] private string battleSceneName = "Battle";
        [SerializeField] private long energyCostPerLevel = 6;

        private HeroCatalog _catalog;
        private int _selectedWorld;
        private readonly System.Collections.Generic.List<GameObject> _spawned = new System.Collections.Generic.List<GameObject>();

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => { if (menuUi != null) menuUi.ShowMenu(); });
            var found = Resources.LoadAll<HeroCatalog>("DreamMasters");
            _catalog = found.Length > 0 ? found[0] : null;
            if (_catalog == null || _catalog.WorldCount == 0)
            {
                Debug.LogError("[CampaignMap] Каталог миров пуст.");
                return;
            }
            var gm = GameManager.Instance;
            if (gm != null)
            {
                gm.Currencies.RegenerateEnergy(gm.Profile);
                // Открываем последний доступный мир (или текущий прогресс)
                _selectedWorld = Mathf.Clamp(gm.Profile.campaignWorld - 1, 0, _catalog.WorldCount - 1);
                for (int w = _catalog.WorldCount - 1; w >= 0; w--)
                    if (gm.Profile.IsWorldUnlocked(w)) { _selectedWorld = w; break; }
            }
            Rebuild();
        }

        private void Rebuild()
        {
            Clear();
            var gm = GameManager.Instance;
            if (gm == null) return;

            // Полоса миров
            for (int w = 0; w < _catalog.WorldCount; w++)
            {
                int idx = w;
                var world = _catalog.worlds.Count > w ? _catalog.worlds[w] : null;
                var btn = MakeButton(worldsStrip, worldButtonPrefab, world != null ? world.worldName : "Мир " + (w + 1));
                btn.interactable = gm.Profile.IsWorldUnlocked(w);
                btn.onClick.AddListener(() => { _selectedWorld = idx; Rebuild(); });
                _spawned.Add(btn.gameObject);
            }

            // Уровни выбранного мира
            var levels = GetLevels(_selectedWorld);
            var worldData = _catalog.GetWorld(_selectedWorld);
            if (worldTitleLabel != null)
                worldTitleLabel.text = worldData != null
                    ? $"Мир {_selectedWorld + 1}: {worldData.worldName} ({worldData.themeElement.RuName()})"
                    : $"Мир {_selectedWorld + 1}";
            if (worldDescLabel != null && worldData != null)
                worldDescLabel.text = worldData.description + (worldData.bossHero != null
                    ? $"\nМастер сна: {worldData.bossHero.heroName} — победи, и он присоединится!" : "");

            for (int i = 0; i < levels.Count; i++)
            {
                int index = i;
                var level = levels[i];
                bool unlocked = gm.Profile.IsLevelUnlocked(_selectedWorld, index);
                bool final = worldData != null && worldData.bossHero != null && index == levels.Count - 1;

                var btn = MakeButton(levelsContainer, levelButtonPrefab,
                    $"{index + 1}. {level.displayName}{(final ? " ★" : "")}{(unlocked ? "" : " [закрыт]")}");
                btn.interactable = unlocked;
                btn.onClick.AddListener(() => Launch(index));
                _spawned.Add(btn.gameObject);
            }
        }

        private System.Collections.Generic.List<LevelData> GetLevels(int worldIndex)
        {
            var world = _catalog.GetWorld(worldIndex);
            if (world != null) return world.levels;
            return _catalog.world1Levels;
        }

        private void Launch(int levelIndex)
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            if (!gm.Currencies.TrySpend(CurrencyType.Energy, energyCostPerLevel))
            {
                Debug.Log("[CampaignMap] Недостаточно энергии.");
                return;
            }
            BattleLaunch.ClearLevel();
            BattleLaunch.PendingWorld = _selectedWorld;
            BattleLaunch.PendingLevelIndex = levelIndex;
            BattleLaunch.IsRetry = false;
            if (menuUi != null) menuUi.SetLoadingVisible(true);
            SceneLoader.Load(battleSceneName);
        }

        private Button MakeButton(Transform parent, Button prefab, string label)
        {
            Button btn;
            if (prefab != null) btn = Instantiate(prefab, parent);
            else
            {
                var go = new GameObject("Btn", typeof(RectTransform), typeof(Image), typeof(Button));
                go.transform.SetParent(parent, false);
                var textGo = new GameObject("Label", typeof(RectTransform), typeof(Text));
                textGo.transform.SetParent(go.transform, false);
                var txt = textGo.GetComponent<Text>();
                txt.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                txt.fontSize = 26;
                txt.color = Color.black;
                txt.alignment = TextAnchor.MiddleCenter;
                var rt = (RectTransform)textGo.transform;
                rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
                btn = go.GetComponent<Button>();
            }
            var t = btn.GetComponentInChildren<Text>();
            if (t != null) t.text = label;
            return btn;
        }

        private void Clear()
        {
            foreach (var go in _spawned) Destroy(go);
            _spawned.Clear();
        }
    }
}
