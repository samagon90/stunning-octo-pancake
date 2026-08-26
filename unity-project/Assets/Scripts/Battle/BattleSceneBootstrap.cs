using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Core;
using DreamMasters.Data;
using DreamMasters.Progress;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Автозапуск боя в сцене Battle: Колизей (BattleLaunch.Pvp) или уровень мира
    /// (BattleLaunch.PendingWorld/LevelIndex, иначе прогресс профиля).
    /// </summary>
    public class BattleSceneBootstrap : MonoBehaviour
    {
        private void Start()
        {
            var bm = BattleManager.Instance;
            var gm = GameManager.Instance;
            if (bm == null || gm == null)
            {
                Debug.LogError("[Bootstrap] Нет BattleManager/GameManager в сцене. Смотри README-SETUP.md.");
                return;
            }

            var catalog = Resources.LoadAll<HeroCatalog>("DreamMasters");
            if (catalog.Length == 0)
            {
                Debug.LogError("[Bootstrap] HeroCatalog не найден в Assets/Resources/DreamMasters.");
                return;
            }
            var cat = catalog[0];

            // ---------- Колизей (PvP) ----------
            if (BattleLaunch.Pvp != null)
            {
                var setup = new BattleManager.PvpSetup
                {
                    Catalog = cat,
                    OpponentName = BattleLaunch.Pvp.OpponentName,
                    OpponentRating = BattleLaunch.Pvp.OpponentRating
                };

                // Уровень соперника ≈ средний уровень команды игрока (честно для среза).
                float avg = AverageTeamLevel(gm);
                foreach (var id in BattleLaunch.Pvp.TeamHeroIds)
                {
                    var data = cat.GetHero(id);
                    if (data == null) continue;
                    var inst = new HeroInstance(data.heroId) { level = Mathf.Max(1, (int)avg), stars = 3 };
                    setup.EnemyTeam.Add((inst, data));
                }
                if (setup.EnemyTeam.Count == 0)
                {
                    // Заглушка не прислала состав — собираем случайных из каталога.
                    var rnd = new System.Random();
                    foreach (var h in cat.heroes)
                    {
                        if (setup.EnemyTeam.Count >= 4) break;
                        if (rnd.Next(2) == 0) continue;
                        var inst = new HeroInstance(h.heroId) { level = Mathf.Max(1, (int)avg), stars = 3 };
                        setup.EnemyTeam.Add((inst, h));
                    }
                }

                Debug.Log($"[Bootstrap] Колизей: против {setup.OpponentName} (x{setup.EnemyTeam.Count})");
                bm.StartPvpBattle(setup);
                return;
            }

            // ---------- PvE: мир и уровень ----------
            var world = ResolveWorld(cat, gm, out int worldIndex);
            if (world == null || world.levels.Count == 0)
            {
                Debug.LogError("[Bootstrap] Миры не настроены в каталоге.");
                return;
            }

            int index = BattleLaunch.PendingLevelIndex >= 0
                ? BattleLaunch.PendingLevelIndex
                : Mathf.Clamp(gm.Profile.campaignLevel - 1, 0, world.levels.Count - 1);
            index = Mathf.Clamp(index, 0, world.levels.Count - 1);

            if (!BattleLaunch.IsRetry)
                BattleLaunch.PendingLevelIndex = index; // для «Ещё раз» в BattleResultUI

            var level = world.levels[index];
            Debug.Log($"[Bootstrap] Мир {worldIndex + 1}, уровень {index + 1}: {level.displayName}");
            bm.StartBattle(level, cat, world, worldIndex, index);
        }

        private static float AverageTeamLevel(GameManager gm)
        {
            int sum = 0, count = 0;
            foreach (var id in gm.Profile.teamHeroIds)
            {
                var hero = gm.Profile.FindHero(id);
                if (hero == null) continue;
                sum += hero.level; count++;
            }
            return count > 0 ? (float)sum / count : 5f;
        }

        private static WorldData ResolveWorld(HeroCatalog cat, GameManager gm, out int worldIndex)
        {
            worldIndex = Mathf.Clamp(BattleLaunch.PendingWorld, 0, Mathf.Max(0, cat.worlds.Count - 1));
            if (cat.worlds.Count > 0) return cat.worlds[worldIndex];

            // Фолббек: каталог без миров (старый контент) — собираем мир 1 на лету.
            worldIndex = 0;
            var w = ScriptableObject.CreateInstance<WorldData>();
            w.worldId = "w1_fallback";
            w.worldName = "Первый сон";
            w.levels = new List<LevelData>(cat.world1Levels);
            return w;
        }
    }
}
