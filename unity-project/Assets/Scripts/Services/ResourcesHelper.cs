using UnityEngine;
using DreamMasters.Data;

namespace DreamMasters.Services
{
    /// <summary>Мелкие помощники доступа к контенту (каталог и т.п.).</summary>
    public static class ResourcesHelper
    {
        private static HeroCatalog _cache;

        public static HeroCatalog Catalog()
        {
            if (_cache != null) return _cache;
            var found = Resources.LoadAll<HeroCatalog>("DreamMasters");
            if (found.Length > 0) _cache = found[0];
            else Debug.LogWarning("[ResourcesHelper] HeroCatalog не найден в Resources/DreamMasters.");
            return _cache;
        }
    }
}
