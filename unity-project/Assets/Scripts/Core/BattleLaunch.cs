using System.Collections.Generic;

namespace DreamMasters.Core
{
    /// <summary>
    /// Передача параметров боя между сценами (Home → Battle).
    /// Мир/уровень −1 = взять из прогресса профиля. Pvp ≠ null — бой Колизея.
    /// </summary>
    public static class BattleLaunch
    {
        public static int PendingWorld = 0;      // индекс мира (0..8)
        public static int PendingLevelIndex = -1;
        public static bool IsRetry;

        /// <summary>Контекст PvP-боя Колизея.</summary>
        public class PvpContext
        {
            public string OpponentName;
            public int OpponentRating;
            public List<string> TeamHeroIds = new List<string>();
        }

        public static PvpContext Pvp;

        public static void ClearLevel()
        {
            PendingWorld = 0;
            PendingLevelIndex = -1;
            IsRetry = false;
        }
    }
}
