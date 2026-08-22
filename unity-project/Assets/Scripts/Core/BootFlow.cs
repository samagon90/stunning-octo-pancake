using UnityEngine;
using DreamMasters.Core;

namespace DreamMasters.Core
{
    /// <summary>
    /// Вешается на пустой объект сцены Boot. Инициализирует GameManager
    /// и уходит на главный экран с загрузочным прогрессом.
    /// </summary>
    public class BootFlow : MonoBehaviour
    {
        [SerializeField] private string homeSceneName = "Home";

        private void Start()
        {
            // GameManager создаётся компонентом на этом же объекте (см. README-SETUP).
            if (GameManager.Instance == null)
            {
                Debug.LogError("[BootFlow] GameManager не найден в сцене Boot.");
                return;
            }
            SceneLoader.Load(homeSceneName);
        }
    }
}
