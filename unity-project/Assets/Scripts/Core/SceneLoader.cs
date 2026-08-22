using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DreamMasters.Core
{
    /// <summary>
    /// Асинхронная загрузка сцен с прогрессом. Он-лайн RPG = тяжёлые сцены,
    /// игрок всегда должен видеть прогресс, а не чёрный экран.
    /// </summary>
    public static class SceneLoader
    {
        public static bool IsLoading { get; private set; }

        /// <summary>onProgress 0..1. loadingScreenPrefab — опционально, экран с полосой прогресса.</summary>
        public static void Load(string sceneName, System.Action<float> onProgress = null, System.Action onDone = null)
        {
            if (IsLoading) return;
            var runner = new GameObject("~SceneLoader").AddComponent<SceneLoaderRunner>();
            runner.StartCoroutine(runner.LoadRoutine(sceneName, onProgress, onDone));
        }

        private sealed class SceneLoaderRunner : MonoBehaviour
        {
            public IEnumerator LoadRoutine(string sceneName, System.Action<float> onProgress, System.Action onDone)
            {
                IsLoading = true;
                AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
                op.allowSceneActivation = false;
                while (op.progress < 0.9f)
                {
                    onProgress?.Invoke(op.progress / 0.9f);
                    yield return null;
                }
                onProgress?.Invoke(1f);
                op.allowSceneActivation = true;
                while (!op.isDone) yield return null;
                IsLoading = false;
                onDone?.Invoke();
                Destroy(gameObject);
            }
        }
    }
}
