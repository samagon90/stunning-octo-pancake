using UnityEngine;

namespace DreamMasters.Core
{
    /// <summary>
    /// Глобальные настройки проекта. Создать один ассет:
    /// Assets → Create → Dream Masters → Game Config.
    /// </summary>
    [CreateAssetMenu(fileName = "GameConfig", menuName = "Dream Masters/Game Config")]
    public class GameConfig : ScriptableObject
    {
        [Header("Производительность")]
        [Tooltip("Целевой FPS. 60 — бой, можно 30 ради батареи в казуальных сценах.")]
        public int targetFrameRate = 60;

        [Header("Бой")]
        public float elementAdvantageMultiplier = 1.25f;   // превосходящая стихия
        public float elementDisadvantageMultiplier = 0.80f; // подчинённая стихия
        public float reviveInvulnerabilitySeconds = 1.5f;
        public bool allowSpeedX2 = true;

        [Header("Сохранения")]
        public string profileFileName = "profile.json";
        public int profileVersion = 1; // версия протокола данных — не терять старых игроков при обновлениях

        [Header("Сеть")]
        [Tooltip("Адрес API. Пусто = локальная заглушка (offline-режим).")]
        public string apiBaseUrl = "";

        [Header("Дебаг")]
        public bool skipTutorial = false;
        public bool debugGodMode = false;
    }
}
