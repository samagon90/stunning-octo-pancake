using UnityEngine;

namespace DreamMasters.UI
{
    /// <summary>
    /// Safe Area для вырезов и чёлок (Canvas/RectTransform). Вешается на корневую
    /// панель каждого экрана — обязательное правило Android (GDD §10).
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class SafeAreaFitter : MonoBehaviour
    {
        private Rect _appliedSafeArea = Rect.zero;
        private RectTransform _rt;
        private Vector2Int _lastScreen;

        private void Awake()
        {
            _rt = (RectTransform)transform;
            Apply();
        }

        private void Update()
        {
            if (Screen.safeArea != _appliedSafeArea || Screen.width != _lastScreen.x || Screen.height != _lastScreen.y)
                Apply();
        }

        private void Apply()
        {
            Rect sa = Screen.safeArea;
            _appliedSafeArea = sa;
            _lastScreen = new Vector2Int(Screen.width, Screen.height);

            Vector2 min = sa.position;
            Vector2 max = sa.position + sa.size;
            min.x /= _lastScreen.x; min.y /= _lastScreen.y;
            max.x /= _lastScreen.x; max.y /= _lastScreen.y;

            _rt.anchorMin = min;
            _rt.anchorMax = max;
            _rt.offsetMin = Vector2.zero;
            _rt.offsetMax = Vector2.zero;
        }
    }
}
