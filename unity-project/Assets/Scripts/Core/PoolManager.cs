using System.Collections.Generic;
using UnityEngine;

namespace DreamMasters.Core
{
    /// <summary>
    /// Пул объектов: никакой Instantiate/Destroy в бою (пули, эффекты, враги,
    /// всплывающие цифры урона). Ключ — префаб.
    /// </summary>
    public class PoolManager : MonoBehaviour
    {
        public static PoolManager Instance { get; private set; }

        private readonly Dictionary<Object, Queue<Object>> _pools = new Dictionary<Object, Queue<Object>>();
        private readonly Dictionary<Object, Object> _originByClone = new Dictionary<Object, Object>();

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        public T Get<T>(T prefab, Vector3 position, Quaternion rotation) where T : Object
        {
            if (!_pools.TryGetValue(prefab, out var queue))
            {
                queue = new Queue<Object>();
                _pools[prefab] = queue;
            }

            Object obj = queue.Count > 0 ? queue.Dequeue() : Instantiate(prefab, position, rotation);
            _originByClone[obj] = prefab;

            if (obj is GameObject go)
            {
                go.transform.SetPositionAndRotation(position, rotation);
                go.SetActive(true);
            }
            else if (obj is Component comp)
            {
                comp.transform.SetPositionAndRotation(position, rotation);
                comp.gameObject.SetActive(true);
            }
            return (T)obj;
        }

        public void Release<T>(T clone) where T : Object
        {
            if (clone == null) return;
            if (!_originByClone.TryGetValue(clone, out var prefab)) { Destroy(clone); return; }

            if (clone is GameObject go) go.SetActive(false);
            else if (clone is Component comp) comp.gameObject.SetActive(false);

            _pools[prefab].Enqueue(clone);
        }

        public void Clear()
        {
            foreach (var kv in _pools)
                while (kv.Value.Count > 0)
                    Destroy(kv.Value.Dequeue());
            _pools.Clear();
            _originByClone.Clear();
        }

        private void OnDestroy() { if (Instance == this) Instance = null; }
    }
}
