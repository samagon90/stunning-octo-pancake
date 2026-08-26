using System;
using System.IO;
using DreamMasters.Core;
using DreamMasters.Progress;
using UnityEngine;

namespace DreamMasters.Services
{
    /// <summary>
    /// Локальные сохранения: JSON в persistentDataPath (кеш быстрой загрузки).
    /// Пишет атомарно (временный файл + переименование), чтобы обрыв записи
    /// не убил профиль (урок оригинала: потеря прогресса = потеря игрока).
    /// </summary>
    public class LocalSaveService : ISaveService
    {
        private readonly string _path;
        private readonly int _expectedVersion;

        public LocalSaveService(GameConfig config)
        {
            _path = Path.Combine(Application.persistentDataPath,
                config != null ? config.profileFileName : "profile.json");
            _expectedVersion = config != null ? config.profileVersion : 1;
        }

        public bool Exists() => File.Exists(_path);

        public PlayerProfile Load()
        {
            try
            {
                if (!Exists()) return null;
                string json = File.ReadAllText(_path);
                var profile = JsonUtility.FromJson<PlayerProfile>(json);
                if (profile == null) return null;
                if (profile.profileVersion > _expectedVersion)
                    Debug.LogWarning("[Save] Профиль от более новой версии игры — запускаем как есть.");
                return profile;
            }
            catch (Exception e)
            {
                Debug.LogError($"[Save] Не удалось прочитать профиль: {e.Message}. Бэкап: {_path}.bak");
                TryBackupCorrupted();
                return null;
            }
        }

        public void Save(PlayerProfile profile)
        {
            if (profile == null) return;
            try
            {
                profile.lastSaveUtc = DateTime.UtcNow.ToString("o");
                string json = JsonUtility.ToJson(profile, prettyPrint: false);
                string tmp = _path + ".tmp";
                File.WriteAllText(tmp, json);
                if (File.Exists(_path)) File.Copy(_path, _path + ".bak", overwrite: true);
                if (File.Exists(_path)) File.Delete(_path);
                File.Move(tmp, _path);
            }
            catch (Exception e)
            {
                Debug.LogError($"[Save] Ошибка сохранения: {e.Message}");
            }
        }

        public void Delete()
        {
            if (File.Exists(_path)) File.Delete(_path);
            if (File.Exists(_path + ".bak")) File.Delete(_path + ".bak");
        }

        private void TryBackupCorrupted()
        {
            try
            {
                if (Exists()) File.Copy(_path, _path + ".corrupted", overwrite: true);
            }
            catch { /* лучший effort */ }
        }
    }
}
