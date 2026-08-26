using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Коллекция героев (ККИ-сердце игры): сетка карточек, тап — карточка детали
    /// с прокачкой. Показывает и «невыпавших» героев каталога (силуэты) — коллекционная цель.
    /// </summary>
    public class CollectionUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Transform grid;
        [SerializeField] private HeroCardView cardPrefab;
        [SerializeField] private HeroDetailUI detailPanel;

        private readonly List<HeroCardView> _spawned = new List<HeroCardView>();

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() =>
            {
                if (detailPanel != null) detailPanel.gameObject.SetActive(false);
                if (menuUi != null) menuUi.ShowMenu();
            });
            if (detailPanel != null) detailPanel.gameObject.SetActive(false);
        }

        private void OnEnable() => Rebuild();

        public void Rebuild()
        {
            var gm = GameManager.Instance;
            var found = Resources.LoadAll<HeroCatalog>("DreamMasters");
            if (gm == null || found.Length == 0) return;
            var catalog = found[0];

            Clear();

            foreach (var heroData in catalog.heroes)
            {
                var instance = gm.Profile.FindHero(heroData.heroId);
                var card = cardPrefab != null ? Instantiate(cardPrefab, grid) : CreateFallbackCard();
                card.Bind(instance, heroData);
                card.Selected += OnCardSelected;
                _spawned.Add(card);
            }
        }

        private void OnCardSelected(HeroInstance instance)
        {
            if (detailPanel == null) return;
            detailPanel.Open(instance);
            detailPanel.gameObject.SetActive(true);
        }

        private void Clear()
        {
            for (int i = 0; i < _spawned.Count; i++)
            {
                _spawned[i].Selected -= OnCardSelected;
                Destroy(_spawned[i].gameObject);
            }
            _spawned.Clear();
        }

        private HeroCardView CreateFallbackCard()
        {
            var go = new GameObject("HeroCard", typeof(RectTransform), typeof(Image), typeof(LayoutElement));
            go.transform.SetParent(grid, false);
            ((RectTransform)go.transform).sizeDelta = new Vector2(240, 320);
            go.AddComponent<HeroCardView>();
            var textGo = new GameObject("Name", typeof(RectTransform), typeof(Text));
            textGo.transform.SetParent(go.transform, false);
            var txt = textGo.GetComponent<Text>();
            txt.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            txt.fontSize = 26;
            txt.color = Color.black;
            txt.alignment = TextAnchor.MiddleCenter;
            ((RectTransform)textGo.transform).anchorMin = Vector2.zero;
            ((RectTransform)textGo.transform).anchorMax = Vector2.one;
            return go.GetComponent<HeroCardView>();
        }
    }
}
