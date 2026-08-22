using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Главный экран-хаб: панели Меню / Кампания / Коллекция / Отряд / Призыв / Магазин.
    /// Одна сцена «Home» — проще навигация и меньше загрузок на мобильных.
    /// Слот главной нативной рекламы размечен (AdSlot.MainMenu) — по плану подключается после релиза.
    /// </summary>
    public class MainMenuUI : MonoBehaviour
    {
        [Header("Панели (все в одном Canvas)")]
        [SerializeField] private GameObject menuPanel;
        [SerializeField] private GameObject campaignPanel;
        [SerializeField] private GameObject collectionPanel;
        [SerializeField] private GameObject teamPanel;
        [SerializeField] private GameObject summonPanel;
        [SerializeField] private GameObject shopPanel;
        [SerializeField] private GameObject arenaPanel;
        [SerializeField] private GameObject chatPanel;
        [SerializeField] private GameObject settingsPanel;
        [SerializeField] private GameObject loadingOverlay;

        [Header("Кнопки меню")]
        [SerializeField] private Button campaignButton;
        [SerializeField] private Button collectionButton;
        [SerializeField] private Button teamButton;
        [SerializeField] private Button summonButton;
        [SerializeField] private Button shopButton;
        [SerializeField] private Button arenaButton;
        [SerializeField] private Button chatButton;
        [SerializeField] private Button settingsButton;
        [SerializeField] private Button quitButton;

        [Header("Прочее")]
        [SerializeField] private UnityEngine.UI.Text welcomeLabel;
        [SerializeField] private GameObject adSlotPlaceholder; // будущее место нативной рекламы

        private void Start()
        {
            if (campaignButton != null) campaignButton.onClick.AddListener(() => Show(campaignPanel));
            if (collectionButton != null) collectionButton.onClick.AddListener(() => Show(collectionPanel));
            if (teamButton != null) teamButton.onClick.AddListener(() => Show(teamPanel));
            if (summonButton != null) summonButton.onClick.AddListener(() => Show(summonPanel));
            if (shopButton != null) shopButton.onClick.AddListener(() => Show(shopPanel));
            if (arenaButton != null) arenaButton.onClick.AddListener(() => Show(arenaPanel));
            if (chatButton != null) chatButton.onClick.AddListener(() => Show(chatPanel));
            if (quitButton != null) quitButton.onClick.AddListener(Quit);

            if (welcomeLabel != null && GameManager.Instance != null)
                welcomeLabel.text = $"Пробуждайся, Мастер {GameManager.Instance.Profile.displayName}!";
            if (adSlotPlaceholder != null) adSlotPlaceholder.SetActive(false); // SDK рекламы ещё нет (план GDD §9)

            Show(menuPanel);
        }

        public void Show(GameObject panel)
        {
            menuPanel?.SetActive(false);
            campaignPanel?.SetActive(false);
            collectionPanel?.SetActive(false);
            teamPanel?.SetActive(false);
            summonPanel?.SetActive(false);
            shopPanel?.SetActive(false);
            arenaPanel?.SetActive(false);
            chatPanel?.SetActive(false);
            settingsPanel?.SetActive(false);
            panel?.SetActive(true);
        }

        public void ShowMenu() => Show(menuPanel);

        public void SetLoadingVisible(bool visible)
        {
            if (loadingOverlay != null) loadingOverlay.SetActive(visible);
        }

        private void Quit()
        {
            if (GameManager.Instance != null) GameManager.Instance.Save.Save(GameManager.Instance.Profile);
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
