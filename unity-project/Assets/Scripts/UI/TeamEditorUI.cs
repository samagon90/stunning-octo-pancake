using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Редактор отряда из 4 героев (канон). Тап по слоту — следующий герой коллекции.
    /// Проверки стихий подсказывают составить отряд со всеми стихиями (урок арены).
    /// </summary>
    public class TeamEditorUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Button[] slotButtons = new Button[4];
        [SerializeField] private Text hintLabel;

        private readonly List<string> _owned = new List<string>();

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() =>
            {
                if (menuUi != null) menuUi.ShowMenu();
                Save();
            });
            for (int i = 0; i < slotButtons.Length; i++)
            {
                if (slotButtons[i] == null) continue;
                int idx = i;
                slotButtons[i].onClick.AddListener(() => CycleSlot(idx));
            }
        }

        private void OnEnable() => Refresh();

        private void Refresh()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;

            _owned.Clear();
            foreach (var hero in gm.Profile.heroes) _owned.Add(hero.heroId);
            if (_owned.Count == 0) return;

            // Добиваем команду до 4 слотов первыми героями
            var team = new List<string>(gm.Profile.teamHeroIds);
            while (team.Count < HeroCollectionService.TeamSize && team.Count < _owned.Count)
                for (int i = 0; i < _owned.Count && team.Count < HeroCollectionService.TeamSize; i++)
                    if (!team.Contains(_owned[i])) team.Add(_owned[i]);

            gm.Profile.teamHeroIds = team;

            var catalog = Resources.LoadAll<HeroCatalog>("DreamMasters");
            var cat = catalog.Length > 0 ? catalog[0] : null;

            for (int i = 0; i < slotButtons.Length && i < team.Count; i++)
            {
                var label = slotButtons[i].GetComponentInChildren<Text>();
                if (label == null) continue;
                var data = cat != null ? cat.GetHero(team[i]) : null;
                label.text = data != null
                    ? $"{data.heroName}\n{data.element.RuName()}"
                    : "Пусто";
            }

            if (hintLabel != null)
                hintLabel.text = "Тапни по слоту, чтобы сменить героя. Совет: держи в отряде все 4 стихии — как учили «Барьеры стихий».";
        }

        private void CycleSlot(int slotIndex)
        {
            var gm = GameManager.Instance;
            if (gm == null || slotIndex >= gm.Profile.teamHeroIds.Count) return;
            string current = gm.Profile.teamHeroIds[slotIndex];
            int pos = _owned.IndexOf(current);
            for (int step = 1; step <= _owned.Count; step++)
            {
                string candidate = _owned[(pos + step) % _owned.Count];
                if (candidate == current) break;
                bool taken = false;
                for (int s = 0; s < gm.Profile.teamHeroIds.Count; s++)
                    if (s != slotIndex && gm.Profile.teamHeroIds[s] == candidate) taken = true;
                if (taken) continue;
                gm.Profile.teamHeroIds[slotIndex] = candidate;
                Refresh();
                return;
            }
        }

        private void Save()
        {
            var gm = GameManager.Instance;
            if (gm != null) gm.Save.Save(gm.Profile);
        }
    }
}
