using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using DreamMasters.Core;
using DreamMasters.Services;

namespace DreamMasters.UI
{
    /// <summary>
    /// Чат (канон: «живое общение в чате»). Сейчас — локальный мир-эфир,
    /// после деплоя сервера — общий чат всех игроков (RestChatProvider).
    /// </summary>
    public class ChatUI : MonoBehaviour
    {
        [SerializeField] private Button backButton;
        [SerializeField] private MainMenuUI menuUi;
        [SerializeField] private Text logLabel;
        [SerializeField] private InputField inputField;
        [SerializeField] private Button sendButton;
        [SerializeField] private float refreshSeconds = 20f;

        private ChatService _chat;

        private void Start()
        {
            var gm = GameManager.Instance;
            if (gm != null)
            {
                _chat = gm.Chat;
                _chat.Updated += Redraw;
            }
            if (backButton != null) backButton.onClick.AddListener(() => { if (menuUi != null) menuUi.ShowMenu(); });
            if (sendButton != null) sendButton.onClick.AddListener(Send);
            Redraw();
            if (isActiveAndEnabled) StartCoroutine(RefreshLoop());
        }

        private void OnDestroy()
        {
            if (_chat != null) _chat.Updated -= Redraw;
        }

        private void Send()
        {
            if (_chat == null || inputField == null) return;
            var gm = GameManager.Instance;
            _chat.Send(gm != null ? gm.Profile.displayName : "Мастер", inputField.text);
            inputField.text = "";
            inputField.ActivateInputField();
        }

        private IEnumerator RefreshLoop()
        {
            var wait = new WaitForSeconds(refreshSeconds);
            while (true)
            {
                _chat?.RefreshAsync();
                yield return wait;
            }
        }

        private void Redraw()
        {
            if (_chat == null || logLabel == null) return;
            var sb = new System.Text.StringBuilder();
            for (int i = _chat.History.Count - 1; i >= 0 && sb.Length < 3000; i--)
                sb.AppendLine(_chat.History[i].ToString());
            logLabel.text = sb.ToString();
        }
    }
}
