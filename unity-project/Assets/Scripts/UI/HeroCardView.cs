using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Карточка героя в коллекции: портрет, имя, стихия (цвет), уровень, звёзды, ранг.
    /// Канон: карта героя = сама суть игры (ККИ-часть).
    /// </summary>
    public class HeroCardView : MonoBehaviour
    {
        [SerializeField] private Image icon;
        [SerializeField] private UnityEngine.UI.Text nameLabel;   // Text — без зависимостей
        [SerializeField] private UnityEngine.UI.Text levelLabel;
        [SerializeField] private UnityEngine.UI.Text starsLabel;
        [SerializeField] private Image elementBadge;
        [SerializeField] private Button selectButton;

        private HeroInstance _instance;
        private HeroData _data;

        public event System.Action<HeroInstance> Selected;

        private static readonly Color[] ElementColors =
        {
            new Color(0.93f, 0.32f, 0.20f), // Огонь
            new Color(0.55f, 0.78f, 0.95f), // Воздух
            new Color(0.55f, 0.72f, 0.35f), // Земля
            new Color(0.30f, 0.55f, 0.95f)  // Вода
        };

        private void Awake()
        {
            if (selectButton != null) selectButton.onClick.AddListener(() => Selected?.Invoke(_instance));
        }

        public void Bind(HeroInstance instance, HeroData data)
        {
            _instance = instance;
            _data = data;
            if (data == null || instance == null) return;

            if (nameLabel != null) nameLabel.text = data.heroName;
            if (levelLabel != null) levelLabel.text = "Ур. " + instance.level;
            if (starsLabel != null)
            {
                var sb = new System.Text.StringBuilder();
                for (int i = 0; i < instance.stars; i++) sb.Append("★");
                starsLabel.text = sb.ToString();
            }
            if (elementBadge != null) elementBadge.color = ElementColors[(int)data.element];
            if (icon != null && data.portrait != null) icon.sprite = data.portrait;
        }

        public HeroInstance Instance => _instance;
        public HeroData Data => _data;
    }
}
