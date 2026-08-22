using DreamMasters.Core;
using DreamMasters.Progress;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// Локально-первая стратегия: сохранение мгновенно пишется на устройство (JSON),
    /// асинхронно уходит в облако. Офлайн-игра не блокируется ничем
    /// (GDD §8: «прогресс не теряется никогда»).
    /// </summary>
    public class HybridSaveService : ISaveService
    {
        private readonly LocalSaveService _local;
        private readonly CloudSaveService _cloud;

        public HybridSaveService(GameConfig config)
        {
            _local = new LocalSaveService(config);
            _cloud = new CloudSaveService(config);
        }

        public PlayerProfile Load() => _local.Load();
        public void Delete() => _local.Delete();
        public bool Exists() => _local.Exists();

        public void Save(PlayerProfile profile)
        {
            _local.Save(profile);            // истина — всегда на устройстве
            _ = _cloud.PushAsync(profile);   // фон, без ожидания: игра не зависит от сети
        }
    }
}
