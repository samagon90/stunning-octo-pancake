using System;
using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;
using DreamMasters.Visuals;

namespace DreamMasters.Battle
{
    /// <summary>Итог боя.</summary>
    public class BattleOutcome
    {
        public bool Victory;
        public bool ScriptedLoss;  // канон: первый бой — сюжетный проигрыш
        public bool IsPvp;         // Колизей
        public int RatingDelta;    // изменение рейтинга (PvP)
        public int Gold;
        public int Crystals;
        public int Shards;
        public int Runes;
        public string JoinedHeroName; // Мастер сна присоединился (канон!)
    }

    /// <summary>
    /// Оркестратор боя: отряд 4 героев против волн уровня (PvE) или противника (Колизей, PvP).
    /// Реестр юнитов, автобой, ×2, синергии, скриптованный проигрыш первого боя,
    /// прогресс миров и присоединение побеждённых Мастеров.
    /// </summary>
    public class BattleManager : MonoBehaviour
    {
        public static BattleManager Instance { get; private set; }

        [Header("Ссылки сцены")]
        [SerializeField] private WaveController waveController;
        [SerializeField] private Transform[] playerSpawnPoints; // 4 точки отряда

        private readonly List<BattleUnit> _heroes = new List<BattleUnit>();
        private readonly List<BattleUnit> _enemies = new List<BattleUnit>();
        private LevelData _level;
        private HeroCatalog _catalog;
        private WorldData _world;
        private int _worldIndex;
        private int _levelIndexInWorld = -1;
        private bool _isPvp;
        private string _pvpOpponentName;
        private bool _finished;
        private float _elapsed;
        private static bool _appPaused;

        public static float ElementAdvantage = 1.25f;
        public static float ElementDisadvantage = 0.80f;

        public static bool AutoMode { get; private set; }
        public static bool SpeedX2 { get; private set; }
        public bool BattlePaused => _appPaused || _finished;

        public IReadOnlyList<BattleUnit> Heroes => _heroes;
        public IReadOnlyList<BattleUnit> Enemies => _enemies;
        public string OpponentName => _pvpOpponentName;

        public event Action<BattleOutcome> BattleEnded;
        public event Action<System.Collections.Generic.IReadOnlyList<BattleUnit>> HeroesChanged;

        /// <summary>Появился враг (волна/PvP) — эффекты вешают HP-бар и цифры.</summary>
        public event Action<BattleUnit> EnemySpawned;

        private void Awake()
        {
            Instance = this;
            var cfg = GameManager.Instance != null ? GameManager.Instance.Config : null;
            if (cfg != null)
            {
                ElementAdvantage = cfg.elementAdvantageMultiplier;
                ElementDisadvantage = cfg.elementDisadvantageMultiplier;
            }
            AutoMode = false; SpeedX2 = false;
        }

        private void Update()
        {
            if (BattlePaused) return;
            _elapsed += Time.deltaTime;
        }

        // ---------------- PvE ----------------

        /// <summary>Старт PvE-боя: команда игрока против уровня мира.</summary>
        public void StartBattle(LevelData level, HeroCatalog catalog, WorldData world = null, int worldIndex = 0, int levelIndexInWorld = -1)
        {
            _level = level;
            _catalog = catalog;
            _world = world;
            _worldIndex = worldIndex;
            _levelIndexInWorld = levelIndexInWorld;
            _isPvp = false;
            _pvpOpponentName = null;
            _finished = false;
            _elapsed = 0f;

            if (waveController == null) waveController = GetComponent<WaveController>();
            if (waveController == null) waveController = gameObject.AddComponent<WaveController>();

            SpawnTeam();
            waveController.Begin(level, new[] { new Vector3(0f, 0f, 12f), new Vector3(4f, 0f, 11f), new Vector3(-4f, 0f, 11f) });
            waveController.AllWavesCleared += OnAllWavesCleared;
        }

        // ---------------- PvP (Колизей) ----------------

        /// <summary>Старт PvP-боя Колизея: команда соперника спавнится как враги.</summary>
        public void StartPvpBattle(PvpSetup setup)
        {
            _catalog = setup.Catalog;
            _level = null; _world = null;
            _isPvp = true;
            _pvpOpponentName = setup.OpponentName;
            _finished = false;
            _elapsed = 0f;

            SpawnTeam();

            var spawn = new[]
            {
                new Vector3(0f, 0f, 11f), new Vector3(4f, 0f, 12f),
                new Vector3(-4f, 0f, 12f), new Vector3(2f, 0f, 13f)
            };
            for (int i = 0; i < setup.EnemyTeam.Count && i < 4; i++)
            {
                var pair = setup.EnemyTeam[i];
                var go = CreateUnitObject();
                go.transform.position = spawn[i];
                var unit = go.AddComponent<BattleUnit>();
                unit.Initialize(pair.Data.heroName, pair.Data.element, pair.Data.attackRange, Team.Enemy, pair.Instance.ComputeStats(pair.Data));
                UnitVisualBuilder.Attach(unit, pair.Data.role, pair.Data.attackRange, isBoss: false, isEnemy: true);
                _enemies.Add(unit);
                unit.Died += OnEnemyDied;
                EnemySpawned?.Invoke(unit);
            }
        }

        /// <summary>Набор параметров PvP-боя (собирает BattleSceneBootstrap).</summary>
        public class PvpSetup
        {
            public HeroCatalog Catalog;
            public string OpponentName;
            public int OpponentRating;
            public List<(HeroInstance Instance, HeroData Data)> EnemyTeam = new List<(HeroInstance, HeroData)>();
        }

        private void SpawnTeam()
        {
            var gm = GameManager.Instance;
            if (gm == null || _catalog == null) return;
            var teamIds = gm.Profile.teamHeroIds;
            for (int i = 0; i < teamIds.Count && i < HeroCollectionService.TeamSize; i++)
            {
                var inst = gm.Profile.FindHero(teamIds[i]);
                var data = _catalog.GetHero(teamIds[i]);
                if (inst == null || data == null) continue;
                SpawnHero(inst, data, i);
            }
        }

        private void SpawnHero(HeroInstance inst, HeroData data, int slot)
        {
            Vector3 pos = playerSpawnPoints != null && playerSpawnPoints.Length > slot
                ? playerSpawnPoints[slot].position
                : new Vector3(slot * 2f - 3f, 0f, -8f);

            var go = CreateUnitObject();
            go.transform.position = pos;
            var unit = go.AddComponent<BattleUnit>();

            // Синергии: парные бонусы применяются к статам (канон: Чейни+Эш = +20% АТК).
            var stats = inst.ComputeStats(data);
            var teamDatas = new List<HeroData>();
            var gm = GameManager.Instance;
            foreach (var id in gm.Profile.teamHeroIds)
            {
                var d = _catalog.GetHero(id);
                if (d != null) teamDatas.Add(d);
            }
            var synergies = _catalog.GetSynergiesFor(data, teamDatas);
            stats.attack = DamageCalculator.SynergyMultiplier(SynergyBonusType.AttackPercent, synergies, stats.attack);
            stats.defense = DamageCalculator.SynergyMultiplier(SynergyBonusType.DefensePercent, synergies, stats.defense);
            stats.maxHp = DamageCalculator.SynergyMultiplier(SynergyBonusType.HpPercent, synergies, stats.maxHp);

            unit.Initialize(data.heroName, data.element, data.attackRange, Team.Player, stats);
            unit.BonusCritChance = DamageCalculator.SynergyFlat(SynergyBonusType.CritChance, synergies);
            UnitVisualBuilder.Attach(unit, data.role, data.attackRange, isBoss: false, isEnemy: false);

            var runtimes = new AbilityRuntime[Math.Min(data.abilities.Count, AbilityData.MaxAbilitiesPerHero)];
            for (int a = 0; a < runtimes.Length; a++)
            {
                int lvl = a < inst.abilityLevels.Length ? inst.abilityLevels[a] : 0;
                if (a >= inst.UnlockedAbilitySlots) lvl = 0;
                runtimes[a] = new AbilityRuntime(data.abilities[a], lvl);
            }
            unit.SetAbilities(runtimes, inst.abilityLevels);

            if (_level != null && _level.scriptedPlayerLoss)
                unit.IncomingDamageMultiplier = 3.0f; // канон: первый босс непобедим

            unit.Died += OnHeroDied;
            _heroes.Add(unit);
            HeroesChanged?.Invoke(_heroes);
        }

        private static GameObject CreateUnitObject()
        {
            var go = new GameObject("Unit");
            go.hideFlags = HideFlags.DontSave;
            return go;
        }

        public void RegisterEnemy(BattleUnit unit, EnemyData enemy)
        {
            if (_level != null && _level.scriptedPlayerLoss)
                unit.IncomingDamageMultiplier = 0.1f; // сюжетная неуязвимость босса завязки
            _enemies.Add(unit);
            unit.Died += OnEnemyDied;
            EnemySpawned?.Invoke(unit);
        }

        private void OnEnemyDied(BattleUnit unit)
        {
            unit.Died -= OnEnemyDied;
            _enemies.Remove(unit);
            if (_isPvp && !_finished)
            {
                bool allDead = _enemies.Count == 0;
                if (allDead) FinishBattle(victory: true);
            }
        }

        private void OnHeroDied(BattleUnit unit)
        {
            unit.Died -= OnHeroDied;
            if (_finished) return;
            bool allDead = true;
            for (int i = 0; i < _heroes.Count; i++) if (_heroes[i].IsAlive) allDead = false;
            if (allDead) FinishBattle(victory: false);
        }

        private void OnAllWavesCleared()
        {
            if (waveController != null) waveController.AllWavesCleared -= OnAllWavesCleared;
            if (!_finished) FinishBattle(victory: true);
        }

        private void FinishBattle(bool victory)
        {
            _finished = true;
            var gm = GameManager.Instance;
            var outcome = new BattleOutcome { Victory = victory, IsPvp = _isPvp };

            if (gm == null) { BattleEnded?.Invoke(outcome); return; }

            if (_isPvp)
            {
                outcome.RatingDelta = gm.Arena != null ? gm.Arena.RecordColosseum(victory) : 0;
                outcome.Gold = victory ? 150 : 40;
                outcome.Shards = victory ? 10 : 0;
            }
            else if (_level != null)
            {
                outcome.ScriptedLoss = _level.scriptedPlayerLoss && !victory;
                outcome.Gold = victory ? _level.goldReward : _level.goldReward / 4;
                outcome.Crystals = victory ? _level.crystalReward : 0;
                outcome.Shards = victory ? _level.shardReward : 0;
                outcome.Runes = victory ? _level.runeReward : 0;

                if (victory)
                {
                    gm.Currencies.Grant(CurrencyType.Gold, outcome.Gold, "battle");
                    gm.Currencies.Grant(CurrencyType.Crystal, outcome.Crystals, "battle");
                    gm.Currencies.Grant(CurrencyType.Shard, outcome.Shards, "battle");
                    gm.Currencies.Grant(CurrencyType.Rune, outcome.Runes, "battle");

                    // Канон: побеждённый Мастер сна присоединяется к отряду игрока.
                    bool worldFinal = _world != null && _levelIndexInWorld >= 0 && _levelIndexInWorld == _world.levels.Count - 1;
                    if (worldFinal && _world.bossHero != null)
                    {
                        gm.Heroes.Obtain(_world.bossHero.heroId);
                        outcome.JoinedHeroName = _world.bossHero.heroName;
                    }
                    gm.Profile.RecordLevelCleared(_worldIndex, _levelIndexInWorld);
                }
            }

            gm.Save.Save(gm.Profile);
            BattleEnded?.Invoke(outcome);
        }

        // ---------- Поиск целей (без аллокаций: буфер переиспользуется) ----------

        private static readonly List<BattleUnit> _queryBuffer = new List<BattleUnit>(16);

        public BattleUnit FindNearestEnemy(BattleUnit from)
        {
            var list = from.Team == Team.Player ? _enemies : _heroes;
            BattleUnit best = null;
            float bestSq = float.MaxValue;
            for (int i = 0; i < list.Count; i++)
            {
                var u = list[i];
                if (!u.IsAlive) continue;
                float sq = (u.transform.position - from.transform.position).sqrMagnitude;
                if (sq < bestSq) { bestSq = sq; best = u; }
            }
            return best;
        }

        public BattleUnit FindMostWoundedAlly(BattleUnit from)
        {
            var list = from.Team == Team.Player ? _heroes : _enemies;
            BattleUnit best = null;
            float lowest = 1f;
            for (int i = 0; i < list.Count; i++)
            {
                var u = list[i];
                if (!u.IsAlive) continue;
                float ratio = u.CurrentHp / u.MaxHp;
                if (ratio < lowest) { lowest = ratio; best = u; }
            }
            return best;
        }

        public List<BattleUnit> FindEnemiesInRadius(BattleUnit from, Vector3 center, float radius)
        {
            _queryBuffer.Clear();
            var list = from.Team == Team.Player ? _enemies : _heroes;
            float sq = radius * radius;
            for (int i = 0; i < list.Count; i++)
            {
                var u = list[i];
                if (u.IsAlive && (u.transform.position - center).sqrMagnitude <= sq)
                    _queryBuffer.Add(u);
            }
            return _queryBuffer;
        }

        public void ApplyTeamBuff(Team team, float percent, float duration)
        {
            var list = team == Team.Player ? _heroes : _enemies;
            for (int i = 0; i < list.Count; i++)
                list[i].Heal(list[i].MaxHp * percent); // срез: баф = лечение; полные бафы — след. итерация
        }

        public static bool AutoCastEnabled(BattleUnit unit) => unit.Team == Team.Enemy || AutoMode;

        public static void ToggleAuto() { AutoMode = !AutoMode; }
        public static void ToggleSpeed()
        {
            SpeedX2 = !SpeedX2;
            Time.timeScale = SpeedX2 ? 2f : 1f;
        }

        /// <summary>Пауза при сворачивании приложения — из GameManager.OnApplicationPause.</summary>
        public static void OnApplicationPaused(bool paused)
        {
            _appPaused = paused;
            if (Instance == null) return;
            Time.timeScale = paused ? 0f : (SpeedX2 ? 2f : 1f);
            foreach (var h in Instance._heroes) h.SetPaused(paused);
            foreach (var e in Instance._enemies) e.SetPaused(paused);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
            Time.timeScale = 1f;
        }
    }
}
