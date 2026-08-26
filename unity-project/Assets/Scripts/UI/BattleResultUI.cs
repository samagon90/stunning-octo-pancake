using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Battle;
using DreamMasters.Core;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Итоговый экран боя: награды, продолжение (в меню) и повтор.
    /// Здесь же размечен слот будущей нативной рекламы (AdSlot.BattleResult).
    /// </summary>
    public class BattleResultUI : MonoBehaviour
    {
        [SerializeField] private GameObject panel;
        [SerializeField] private Text titleLabel;
        [SerializeField] private Text rewardsLabel;
        [SerializeField] private Button continueButton;
        [SerializeField] private Button retryButton;
        [SerializeField] private GameObject adPlaceholder; // включится вместе с AdMob Native (после релиза)

        [Header("Сцены")]
        [SerializeField] private string homeScene = "Home";
        [SerializeField] private string battleScene = "Battle";

        private int _lastLevelIndex = -1;

        private void Start()
        {
            var bm = BattleManager.Instance;
            if (bm != null) bm.BattleEnded += OnBattleEnded;
            if (continueButton != null) continueButton.onClick.AddListener(Continue);
            if (retryButton != null) retryButton.onClick.AddListener(Retry);
            if (panel != null) panel.SetActive(false);
            if (adPlaceholder != null) adPlaceholder.SetActive(false);
            _lastLevelIndex = BattleLaunch.PendingLevelIndex;
        }

        private void OnDestroy()
        {
            var bm = BattleManager.Instance;
            if (bm != null) bm.BattleEnded -= OnBattleEnded;
        }

        private void OnBattleEnded(BattleOutcome outcome)
        {
            if (panel == null) return;
            panel.SetActive(true);
            if (Core.AudioManager.Instance != null)
                Core.AudioManager.Instance.Play(outcome.Victory ? Core.Sfx.Victory : Core.Sfx.Defeat);
            if (titleLabel != null)
                titleLabel.text = outcome.IsPvp
                    ? (outcome.Victory ? $"ПОБЕДА НА КОЛИЗЕЕ! (рейтинг {outcome.RatingDelta:+#;-#;0})" : "ПОРАЖЕНИЕ НА КОЛИЗЕЕ")
                    : outcome.Victory ? "ПОБЕДА!" :
                      (outcome.ScriptedLoss ? "Так задумано..." : "Поражение");
            if (rewardsLabel != null)
            {
                string text = outcome.Victory
                    ? $"+{outcome.Gold} золота\n+{outcome.Crystals} кристаллов\n+{outcome.Shards} осколков\n+{outcome.Runes} рун"
                    : "Повелитель Мрака лишь сильнее. Прокачай героев и вернись!";
                if (!string.IsNullOrEmpty(outcome.JoinedHeroName))
                    text += $"\n\n{outcome.JoinedHeroName} пробудился и присоединился к твоему отряду!";
                rewardsLabel.text = text;
            }
        }

        private void Continue()
        {
            BattleLaunch.PendingLevelIndex = -1;
            SceneLoader.Load(homeScene);
        }

        private void Retry()
        {
            BattleLaunch.PendingLevelIndex = _lastLevelIndex;
            BattleLaunch.IsRetry = true;
            SceneLoader.Load(battleScene);
        }
    }
}
