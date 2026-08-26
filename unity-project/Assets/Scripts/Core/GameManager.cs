using UnityEngine;
using DreamMasters.Progress;
using DreamMasters.Services;

namespace DreamMasters.Core
{
    /// <summary>
    /// Точка входа приложения. Живёт в сцене Boot, DontDestroyOnLoad.
    /// Держит ссылки на сервисы, обрабатывает жизненный цикл Android-приложения:
    /// пауза при потере фокуса и автосохранение — игрок не теряет прогресс
    /// из-за звонка или сворачивания (урок оригинальной игры).
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [SerializeField] private GameConfig config;

        public GameConfig Config => config;
        public PlayerProfile Profile { get; private set; }

        public ISaveService Save { get; private set; }
        public INetworkService Network { get; private set; }
        public IAdService Ads { get; private set; }
        public CurrencyService Currencies { get; private set; }
        public HeroCollectionService Heroes { get; private set; }
        public InventoryService Inventory { get; private set; }
        public Progress.ArenaService Arena { get; private set; }
        public Services.ChatService Chat { get; private set; }

        /// <summary>Профиль изменили (настройки и т.п.) — сервисы обновляются.</summary>
        public event System.Action ProfileChanged;
        public void NotifyProfileChanged() => ProfileChanged?.Invoke();

        private bool _paused;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Application.targetFrameRate = config != null ? config.targetFrameRate : 60;

            // Сервисы за интерфейсами: бэкенд подключается заполнением apiBaseUrl
            // в GameConfig — без единой правки геймплея (см. GDD §9–10 и docs/FIREBASE-SETUP.md).
            string apiUrl = config != null ? config.apiBaseUrl : "";
            bool online = !string.IsNullOrEmpty(apiUrl);
            Save = online
                ? new HybridSaveService(config)
                : new LocalSaveService(config);
            Network = online
                ? new RestNetworkService(apiUrl)
                : new LocalNetworkStub();
            Ads = new NullAdService();

            Profile = Save.Load() ?? PlayerProfile.CreateNew();

            Currencies = new CurrencyService(Profile);
            Heroes = new HeroCollectionService(Profile);
            Inventory = new InventoryService(Profile);
            Arena = new Progress.ArenaService(Profile, Currencies);
            Chat = new Services.ChatService(
                online ? new Services.RestChatProvider(apiUrl) : new Services.LocalChatProvider());
            Currencies.RegenerateEnergy(Profile);
        }

        private void Start()
        {
            // Первый вход: выдаём стартового героя и открываем первый «сон».
            if (!Profile.tutorialFinished && !config.skipTutorial)
                Heroes.GrantStarterHeroes();
            Save.Save(Profile);
        }

        /// <summary>Пауза боя и сохранение при сворачивании/потере фокуса — обязательное правило Android.</summary>
        private void OnApplicationPause(bool pauseStatus)
        {
            if (pauseStatus == _paused) return;
            _paused = pauseStatus;
            if (_paused) Save?.Save(Profile);
            Battle.BattleManager.OnApplicationPaused(_paused);
            if (AudioManager.Instance != null) AudioManager.Instance.SetSuspended(_paused);
        }

        private void OnApplicationQuit() => Save?.Save(Profile);

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        [ContextMenu("Сбросить прогресс (дебаг)")]
        private void DebugResetProfile()
        {
            Save.Delete();
            Profile = PlayerProfile.CreateNew();
            UnityEngine.Debug.Log("[GameManager] Профиль сброшен.");
        }
    }
}
