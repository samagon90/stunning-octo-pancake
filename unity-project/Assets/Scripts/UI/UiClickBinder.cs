using UnityEngine;
using UnityEngine.UI;

namespace DreamMasters.UI
{
    /// <summary>
    /// Вешает клик-звук на ВСЕ кнопки сцены (включая неактивные панели).
    /// Вешается на корневой объект Canvas один раз.
    /// </summary>
    [RequireComponent(typeof(Canvas))]
    public class UiClickBinder : MonoBehaviour
    {
        private void Start()
        {
            var buttons = GetComponentsInChildren<Button>(true);
            foreach (var b in buttons)
                b.onClick.AddListener(PlayClick);
        }

        private void PlayClick()
        {
            if (Core.AudioManager.Instance != null)
                Core.AudioManager.Instance.Play(Core.Sfx.Click);
        }
    }
}
