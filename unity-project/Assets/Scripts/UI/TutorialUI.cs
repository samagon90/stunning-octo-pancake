using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Progress;

namespace DreamMasters.UI
{
    /// <summary>
    /// Обучение-оверлей: история пробуждения (канон сюжета) страницами.
    /// Скип — зажать экран на 5 секунд (пасхалка оригинала: там так пропускали
    /// непроходимое обучение). Завершение ставит tutorialFinished.
    /// </summary>
    public class TutorialUI : MonoBehaviour
    {
        [SerializeField] private GameObject panel;
        [SerializeField] private Text pageLabel;
        [SerializeField] private Text pageCounterLabel;
        [SerializeField] private Button nextButton;
        [SerializeField] private Image holdProgress; // заливка удержания (0..1)
        [SerializeField] private float holdToSkipSeconds = 5f;

        private static readonly string[] Pages =
        {
            "Несколько тысяч лет назад Повелитель Мрака вторгся в Мир. Великие Мастера ценой нечеловеческих жертв заточили его в Вечном Сне...",
            "Тысячи лет спустя Повелитель пробудился — и применил к Мастерам их же оружие: заключил каждого в его собственный сон.",
            "Разделённые и одинокие, Мастера не смогли разрушить проклятие. Легионы разрушения вновь заполонили Мир.",
            "Ты — последний Мастер, оставшийся в здравом уме. Собери отряд героев, пройди сны Мастеров и освободи Королевство!",
            "Сначала — Первый сон. И да: первый бой проигрывают ВСЕГДА. Так задумано.\n\n(Зажми экран на 5 секунд, если хочешь пропустить обучение — как в легендах)"
        };

        private int _page;
        private bool _finished;
        private float _holdT;

        private void Start()
        {
            if (nextButton != null) nextButton.onClick.AddListener(NextPage);
            var gm = GameManager.Instance;
            bool needTutorial = gm != null && !gm.Profile.tutorialFinished;
            if (panel != null) panel.SetActive(needTutorial);
            if (needTutorial) ShowPage(0);
        }

        private void ShowPage(int index)
        {
            _page = Mathf.Clamp(index, 0, Pages.Length - 1);
            if (pageLabel != null) pageLabel.text = Pages[_page];
            if (pageCounterLabel != null) pageCounterLabel.text = $"{_page + 1} / {Pages.Length}";
            if (nextButton != null)
            {
                var txt = nextButton.GetComponentInChildren<Text>();
                if (txt != null) txt.text = _page == Pages.Length - 1 ? "Пробудиться!" : "Далее";
            }
        }

        private void NextPage()
        {
            if (_page < Pages.Length - 1) { ShowPage(_page + 1); return; }
            Finish();
        }

        private void Update()
        {
            if (panel == null || !panel.activeSelf || _finished) return;

            // Канонный скип: зажать любую точку экрана 5 секунд.
            bool holding = Input.touchCount > 0 || Input.GetMouseButton(0);
            if (holding)
            {
                _holdT += Time.deltaTime;
                if (holdProgress != null)
                {
                    holdProgress.fillAmount = Mathf.Clamp01(_holdT / holdToSkipSeconds);
                    holdProgress.gameObject.SetActive(true);
                }
                if (_holdT >= holdToSkipSeconds) Finish();
            }
            else
            {
                _holdT = 0f;
                if (holdProgress != null) holdProgress.gameObject.SetActive(false);
            }
        }

        private void Finish()
        {
            if (_finished) return;
            _finished = true;
            var gm = GameManager.Instance;
            if (gm != null)
            {
                gm.Profile.tutorialFinished = true;
                gm.Save.Save(gm.Profile);
            }
            if (panel != null) panel.SetActive(false);
        }
    }
}
