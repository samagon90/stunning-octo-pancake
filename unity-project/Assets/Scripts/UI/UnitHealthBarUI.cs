using UnityEngine;
using DreamMasters.Battle;

namespace DreamMasters.UI
{
    /// <summary>
    /// HP-бар над юнитом: два спрайта (фон/заливка), billboard к камере.
    /// Создаётся из кода — префаб не нужен. Цвет заливки — стихия юнита.
    /// </summary>
    public class UnitHealthBarUI : MonoBehaviour
    {
        private static Texture2D _whiteTexture;
        private static Sprite _whiteSprite;

        private Transform _fill;
        private BattleUnit _unit;
        private Camera _cam;
        private Vector3 _fillScale;

        private static readonly Color[] ElementColors =
        {
            new Color(0.93f, 0.32f, 0.20f), // Огонь
            new Color(0.70f, 0.85f, 0.98f), // Воздух
            new Color(0.55f, 0.72f, 0.35f), // Земля
            new Color(0.30f, 0.55f, 0.95f)  // Вода
        };

        public static UnitHealthBarUI Attach(BattleUnit unit, Camera cam)
        {
            if (unit == null) return null;

            if (_whiteSprite == null)
            {
                _whiteTexture = new Texture2D(4, 4);
                var pixels = new Color[16];
                for (int i = 0; i < 16; i++) pixels[i] = Color.white;
                _whiteTexture.SetPixels(pixels);
                _whiteTexture.Apply();
                _whiteSprite = Sprite.Create(_whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4f);
            }

            var root = new GameObject("HP_" + unit.name);
            root.transform.SetParent(unit.transform, false);
            root.transform.localPosition = Vector3.up * 2.6f;

            var bg = root.AddComponent<SpriteRenderer>();
            bg.sprite = _whiteSprite;
            bg.color = new Color(0f, 0f, 0f, 0.6f);
            bg.transform.localScale = new Vector3(1.2f, 0.14f, 1f);
            bg.sortingOrder = 50;

            var fillGo = new GameObject("Fill");
            fillGo.transform.SetParent(root.transform, false);
            var fill = fillGo.AddComponent<SpriteRenderer>();
            fill.sprite = _whiteSprite;
            fill.color = ElementColors[(int)unit.Element];
            fill.sortingOrder = 51;
            fillGo.transform.localScale = new Vector3(1.16f, 0.10f, 1f);
            fillGo.transform.localPosition = new Vector3(0f, 0f, -0.01f);

            var bar = root.AddComponent<UnitHealthBarUI>();
            bar._unit = unit;
            bar._fill = fillGo.transform;
            bar._fillScale = fillGo.transform.localScale;
            bar._cam = cam != null ? cam : Camera.main;
            return bar;
        }

        private void LateUpdate()
        {
            if (_unit == null)
            {
                Destroy(gameObject);
                return;
            }
            if (!_unit.IsAlive) { gameObject.SetActive(false); return; }

            float ratio = _unit.MaxHp > 0f ? _unit.CurrentHp / _unit.MaxHp : 0f;
            _fillScale.x = 1.16f * Mathf.Clamp01(ratio);
            _fill.localScale = _fillScale;
            _fill.localPosition = new Vector3(-(1.16f - _fillScale.x) * 0.5f, 0f, -0.01f);

            if (_cam != null)
            {
                Vector3 dir = transform.position - _cam.transform.position;
                transform.rotation = Quaternion.LookRotation(dir);
            }
        }
    }
}
