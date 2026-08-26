using DreamMasters.Progress;

namespace DreamMasters.Services
{
    /// <summary>
    /// Слой сохранений. Сейчас — локальный JSON; при подключении бэкенда сюда
    /// добавится облачная реализация с тем же интерфейсом (урок оригинала:
    /// сохранения обязаны переживать любое обновление и смену устройства).
    /// </summary>
    public interface ISaveService
    {
        PlayerProfile Load();
        void Save(PlayerProfile profile);
        void Delete();
        bool Exists();
    }
}
