using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Настройки: имя Мастера, громкость музыки/звуков, персонализация рекламы
    /// (заготовка под Consent Manager), ссылка на политику конфиденциальности.
    /// </summary>
    public class SettingsUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private InputField nameInput;
        [SerializeField] private Slider musicSlider;
        [SerializeField] private Slider sfxSlider;
        [SerializeField] private Toggle adsPersonalizedToggle;
        [SerializeField] private Button privacyButton;
        [SerializeField] private string privacyUrl = "https://example.com/privacy";
        [SerializeField] private Text versionLabel;

        private bool _binding;

        private void Start()
        {
            if (backButton != null) backButton.onClick.AddListener(() => { Save(); if (menuUi != null) menuUi.ShowMenu(); });
            if (musicSlider != null) musicSlider.onValueChanged.AddListener(_ => OnChanged());
            if (sfxSlider != null) sfxSlider.onValueChanged.AddListener(_ => OnChanged());
            if (nameInput != null) nameInput.onEndEdit.AddListener(_ => OnChanged());
            if (adsPersonalizedToggle != null) adsPersonalizedToggle.onValueChanged.AddListener(_ => OnChanged());
            if (privacyButton != null) privacyButton.onClick.AddListener(() => Application.OpenURL(privacyUrl));
            if (versionLabel != null)
                versionLabel.text = $"v{Application.version} • профиль: {(GameManager.Instance != null ? GameManager.Instance.Profile.profileVersion : 0)}";
        }

        private void OnEnable() => Bind();

        private void Bind()
        {
            var gm = GameManager.Instance;
            if (gm == null) return;
            _binding = true;
            if (nameInput != null) nameInput.text = gm.Profile.displayName;
            if (musicSlider != null) musicSlider.value = gm.Profile.musicVolume;
            if (sfxSlider != null) sfxSlider.value = gm.Profile.sfxVolume;
            if (adsPersonalizedToggle != null) adsPersonalizedToggle.isOn = gm.Profile.adsPersonalized;
            _binding = false;
        }

        private void OnChanged()
        {
            if (_binding) return;
            var gm = GameManager.Instance;
            if (gm == null) return;
            var p = gm.Profile;
            if (nameInput != null && !string.IsNullOrWhiteSpace(nameInput.text)) p.displayName = nameInput.text.Trim();
            if (musicSlider != null) p.musicVolume = musicSlider.value;
            if (sfxSlider != null) p.sfxVolume = sfxSlider.value;
            if (adsPersonalizedToggle != null) p.adsPersonalized = adsPersonalizedToggle.isOn;

            gm.NotifyProfileChanged(); // AudioManager применит громкости сразу
            gm.Save.Save(p);
        }

        private void Save()
        {
            var gm = GameManager.Instance;
            if (gm != null) gm.Save.Save(gm.Profile);
        }
    }
}
