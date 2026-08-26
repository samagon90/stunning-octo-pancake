using System.Collections;
using UnityEngine;
using DreamMasters.Core;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Всплывающие цифры урона/лечения (TextMesh, пул через PoolManager).
    /// «...вы только и успеваете следить за вылетающими циферками урона» — обзор оригинала.
    /// </summary>
    public class FloatingDamageText : MonoBehaviour
    {
        [SerializeField] private float lifetime = 0.9f;
        [SerializeField] private float riseSpeed = 1.8f;

        private TextMesh _text;
        private Coroutine _routine;

        private void Awake() => _text = GetComponent<TextMesh>();

        public static void Spawn(GameObject prefab, Vector3 position, string text, Color color)
        {
            if (prefab == null || PoolManager.Instance == null) return;
            var instance = PoolManager.Instance.Get(prefab, position, Quaternion.identity).GetComponent<FloatingDamageText>();
            instance.Play(text, color);
        }

        private void Play(string text, Color color)
        {
            if (_text == null) _text = GetComponent<TextMesh>() ?? gameObject.AddComponent<TextMesh>();
            _text.text = text;
            _text.color = color;
            _text.fontSize = 48;
            _text.characterSize = 0.12f;
            _text.anchor = TextAnchor.MiddleCenter;

            if (_routine != null) StopCoroutine(_routine);
            _routine = StartCoroutine(RiseAndFade());
        }

        private IEnumerator RiseAndFade()
        {
            float t = 0f;
            Color c = _text.color;
            Vector3 start = transform.position;
            Vector3 target = start + Vector3.up * riseSpeed;
            while (t < lifetime)
            {
                t += Time.deltaTime;
                float k = t / lifetime;
                transform.position = Vector3.Lerp(start, target, k);
                c.a = 1f - k;
                _text.color = c;
                yield return null;
            }
            PoolManager.Instance.Release(gameObject);
        }
    }
}
