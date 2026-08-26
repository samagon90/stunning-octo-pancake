using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Progress;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Арена (авто) и Колизей (ручной бой в сцене Battle, максимум 3 поражения в день — канон).
    /// Противники — из INetworkService (заглушка сейчас, сервер после деплоя).
    /// </summary>
    public class ArenaUI : MonoBehaviour
    {
        [Header("Общее")]
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Text ratingLabel;
        [SerializeField] private Text resultLabel;

        [Header("Арена (авто)")]
        [SerializeField] private GameObject arenaTab;
        [SerializeField] private Button[] arenaFightButtons = new Button[3]; // по одному на противника
        [SerializeField] private Text[] opponentLabels = new Text[3];

        [Header("Колизей (ручной)")]
        [SerializeField] private GameObject colosseumTab;
        [SerializeField] private Button tabArenaButton;
        [SerializeField] private Button tabColosseumButton;
        [SerializeField] private Button[] colosseumFightButtons = new Button[3];
        [SerializeField] private Text colosseumStatusLabel;
        [SerializeField] private string battleScene = "Battle";

        private List<ArenaOpponentDto> _opponents = new List<ArenaOpponentDto>();

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => { if (menuUi != null) menuUi.ShowMenu(); });
            if (tabArenaButton != null) tabArenaButton.onClick.AddListener(() => SwitchTab(true));
            if (tabColosseumButton != null) tabColosseumButton.onClick.AddListener(() => SwitchTab(false));

            for (int i = 0; i < arenaFightButtons.Length; i++)
            {
                if (arenaFightButtons[i] == null) continue;
                int idx = i;
                arenaFightButtons[i].onClick.AddListener(() => AutoFight(idx));
            }
            for (int i = 0; i < colosseumFightButtons.Length; i++)
            {
                if (colosseumFightButtons[i] == null) continue;
                int idx = i;
                colosseumFightButtons[i].onClick.AddListener(() => StartColosseum(idx));
            }

            var gm = GameManager.Instance;
            if (gm != null && gm.Arena != null) gm.Arena.Changed += Refresh;
            Refresh();
            LoadOpponents();
        }

        private void OnDestroy()
        {
            var gm = GameManager.Instance;
            if (gm != null && gm.Arena != null) gm.Arena.Changed -= Refresh;
        }

        private async void LoadOpponents()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            var resp = await gm.Network.FetchArenaOpponents(gm.Profile.arenaRating);
            if (resp.Ok && resp.Data != null) _opponents = resp.Data;
            Refresh();
        }

        private void SwitchTab(bool arena)
        {
            if (arenaTab != null) arenaTab.SetActive(arena);
            if (colosseumTab != null) colosseumTab.SetActive(!arena);
        }

        private void Refresh()
        {
            var gm = GameManager.Instance;
            if (gm == null || gm.Arena == null) return;

            if (ratingLabel != null)
                ratingLabel.text = $"Рейтинг: {gm.Arena.Rating}  •  Рекорд: {gm.Profile.bestArenaRating}";

            for (int i = 0; i < opponentLabels.Length; i++)
            {
                if (opponentLabels[i] == null) continue;
                opponentLabels[i].text = i < _opponents.Count
                    ? $"{_opponents[i].displayName}\nРейтинг {_opponents[i].rating}"
                    : "…";
            }

            if (colosseumStatusLabel != null)
                colosseumStatusLabel.text = $"Поражений сегодня: {gm.Arena.ColosseumLossesToday}/{ArenaService.MaxDailyLosses}\n" +
                                            $"Побед сегодня: {gm.Arena.ColosseumWinsToday}  •  Награда: 150 золота и 10 осколков за победу";

            bool canFight = gm.Arena.ColosseumAvailable;
            for (int i = 0; i < colosseumFightButtons.Length; i++)
                if (colosseumFightButtons[i] != null) colosseumFightButtons[i].interactable = canFight && i < _opponents.Count;
        }

        private void AutoFight(int opponentIndex)
        {
            var gm = GameManager.Instance;
            if (gm == null || opponentIndex >= _opponents.Count) return;
            var catalog = ResourcesHelper.Catalog();
            var result = gm.Arena.SimulateAutoFight(_opponents[opponentIndex], catalog, gm.Heroes);
            if (resultLabel != null) resultLabel.text = result.Description + $"\n+{result.Gold} золота, +{result.Shards} осколков";
            gm.Save.Save(gm.Profile);
            Refresh();
        }

        private void StartColosseum(int opponentIndex)
        {
            var gm = GameManager.Instance;
            if (gm == null || opponentIndex >= _opponents.Count || !gm.Arena.ColosseumAvailable) return;

            BattleLaunch.Pvp = new BattleLaunch.PvpContext
            {
                OpponentName = _opponents[opponentIndex].displayName,
                OpponentRating = _opponents[opponentIndex].rating,
                TeamHeroIds = new List<string>(_opponents[opponentIndex].teamHeroIds)
            };
            if (menuUi != null) menuUi.SetLoadingVisible(true);
            SceneLoader.Load(battleScene);
        }
    }
}
