using UnityEngine;
using UnityEngine.EventSystems;

namespace DreamMasters.UI
{
    /// <summary>
    /// Виртуальный джойстик под большой палец (левая половина экрана, портрет).
    /// Только тач: реализует интерфейсы EventSystem — работает и в редакторе мышью.
    /// </summary>
    public class VirtualJoystick : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        public static VirtualJoystick Instance { get; private set; }

        [SerializeField] private RectTransform background;   // база джойстика
        [SerializeField] private RectTransform knob;         // ручка
        [SerializeField] private float radius = 90f;         // радиус хода ручки
        [SerializeField] private float deadZone = 0.12f;

        /// <summary>Направление −1..1 (x, z-плоскость боя). Ноль — палец отпущен.</summary>
        public Vector2 Direction { get; private set; }
        public bool IsActive { get; private set; }

        private Vector2 _center;

        private void Awake() => Instance = this;

        public void OnPointerDown(PointerEventData e)
        {
            IsActive = true;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                background.parent as RectTransform, e.position, e.pressEventCamera, out _center);
            background.anchoredPosition = _center;
            background.gameObject.SetActive(true);
            UpdateKnob(e.position, e.pressEventCamera);
        }

        public void OnDrag(PointerEventData e) => UpdateKnob(e.position, e.pressEventCamera);

        public void OnPointerUp(PointerEventData e)
        {
            IsActive = false;
            Direction = Vector2.zero;
            knob.anchoredPosition = Vector2.zero;
            background.gameObject.SetActive(false);
        }

        private void UpdateKnob(Vector2 screenPos, Camera cam)
        {
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                background, screenPos, cam, out Vector2 local);
            Vector2 clamped = Vector2.ClampMagnitude(local, radius);
            knob.anchoredPosition = clamped;
            Vector2 dir = clamped / radius;
            Direction = dir.magnitude < deadZone ? Vector2.zero : dir.normalized * ((dir.magnitude - deadZone) / (1f - deadZone));
        }
    }
}
