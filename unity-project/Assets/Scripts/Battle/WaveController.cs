using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Visuals;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Дирижёр волн уровня: спавнит пачки по расписанию, следит за зачисткой,
    /// запускает босса. Спавн через пул — без Instantiate/Destroy в цикле боя.
    /// Визуал врагов — процедурный (UnitVisualBuilder), пока нет моделей.
    /// </summary>
    public class WaveController : MonoBehaviour
    {
        [SerializeField] private Transform[] spawnPoints; // назначить в Инспекторе (по умолчанию — авто)

        /// <summary>Активный контроллер волн сцены (для HUD).</summary>
        public static WaveController Active { get; private set; }

        private LevelData _level;
        private readonly List<BattleUnit> _spawned = new List<BattleUnit>();
        private int _currentWave;
        private bool _running;

        public event Action<int, int> WaveStarted;   // индекс волны, всего волн
        public event Action AllWavesCleared;

        public int CurrentWave => _currentWave;
        public int TotalWaves => _level != null ? _level.waves.Count : 0;
        public IReadOnlyList<BattleUnit> AliveEnemies => _spawned;

        private void Awake() => Active = this;
        private void OnDestroy() { if (Active == this) Active = null; }

        public void Begin(LevelData level, Vector3[] fallbackSpawnPoints)
        {
            _level = level;
            if (spawnPoints == null || spawnPoints.Length == 0)
                _fallback = new List<Vector3>(fallbackSpawnPoints);
            _currentWave = -1;
            _running = true;
            StartCoroutine(NextWaveRoutine());
        }

        private List<Vector3> _fallback;

        private Vector3 RandomSpawnPoint()
        {
            if (spawnPoints != null && spawnPoints.Length > 0)
                return spawnPoints[UnityEngine.Random.Range(0, spawnPoints.Length)].position;
            if (_fallback != null && _fallback.Count > 0)
                return _fallback[UnityEngine.Random.Range(0, _fallback.Count)];
            return new Vector3(0f, 0f, 12f);
        }

        private IEnumerator NextWaveRoutine()
        {
            _currentWave++;
            if (_level == null || _currentWave >= _level.waves.Count)
            {
                _running = false;
                AllWavesCleared?.Invoke();
                yield break;
            }

            WaveStarted?.Invoke(_currentWave, TotalWaves);
            var wave = _level.waves[_currentWave];

            for (int i = 0; i < wave.count; i++)
            {
                SpawnEnemy(wave.enemy);
                if (i < wave.count - 1) yield return new WaitForSeconds(wave.spawnInterval);
            }
        }

        private void SpawnEnemy(EnemyData enemy)
        {
            if (enemy == null) return;
            Vector3 pos = RandomSpawnPoint();

            GameObject go;
            if (enemy.viewPrefab != null && PoolManager.Instance != null)
            {
                go = PoolManager.Instance.Get(enemy.viewPrefab, pos, Quaternion.identity);
                var existing = go.GetComponent<BattleUnit>();
                if (existing != null) go = DetachFromPrefab(go);
            }
            else
            {
                go = new GameObject("Enemy_" + enemy.enemyId);
                go.transform.position = pos;
            }

            var unit = go.GetComponent<BattleUnit>();
            if (unit == null) unit = go.AddComponent<BattleUnit>();
            go.transform.position = pos;

            unit.Initialize(enemy.displayName, enemy.element, AttackRange.Melee, Team.Enemy, enemy.stats, enemy.isBoss);
            unit.IncomingDamageMultiplier = 1f;
            UnitVisualBuilder.Attach(unit, enemy.isBoss ? HeroRole.Tank : HeroRole.Damage, AttackRange.Melee,
                isBoss: enemy.isBoss, isEnemy: true);

            if (BattleManager.Instance != null)
                BattleManager.Instance.RegisterEnemy(unit, enemy);
            _spawned.Add(unit);
            unit.Died += OnEnemyDied;
        }

        /// <summary>Пooled-префаб переиспользуется: визуал не должен висеть на нём между спавнами — оборачиваем.</summary>
        private static GameObject DetachFromPrefab(GameObject pooled)
        {
            var host = new GameObject("Enemy");
            pooled.transform.SetParent(host.transform, true);
            return host;
        }

        private void OnEnemyDied(BattleUnit unit)
        {
            unit.Died -= OnEnemyDied;
            _spawned.Remove(unit);
            if (_running && _spawned.Count == 0) StartCoroutine(NextWaveRoutine());
        }

        public void KillAll()
        {
            for (int i = _spawned.Count - 1; i >= 0; i--) _spawned[i].ReceiveDamage(999999f, false);
        }
    }
}
