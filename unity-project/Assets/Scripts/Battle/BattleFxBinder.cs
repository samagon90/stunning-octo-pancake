using UnityEngine;
using DreamMasters.Core;
using DreamMasters.UI;

namespace DreamMasters.Battle
{
    /// <summary>
    /// Связывает бой и «картинку»: цифры урона (пул), HP-бары, окраска капсул по стихиям.
    /// Вешается рядом с BattleManager. Префаб цифр опционален — создастся сам.
    /// </summary>
    public class BattleFxBinder : MonoBehaviour
    {
        [SerializeField] private GameObject damageTextPrefab; // TextMesh «0» + FloatingDamageText
        [SerializeField] private Camera battleCamera;

        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor"); // URP
        private static readonly int ColorId = Shader.PropertyToID("_Color");        // Built-in

        private static readonly Color[] ElementColors =
        {
            new Color(0.93f, 0.32f, 0.20f),
            new Color(0.75f, 0.88f, 0.98f),
            new Color(0.55f, 0.72f, 0.35f),
            new Color(0.30f, 0.55f, 0.95f)
        };

        private MaterialPropertyBlock _mpb;
        private GameObject _autoPrefab;

        private void Start()
        {
            var bm = BattleManager.Instance;
            if (bm == null) return;
            if (battleCamera == null) battleCamera = Camera.main;
            _mpb = new MaterialPropertyBlock();

            foreach (var hero in bm.Heroes) Hook(hero, isHero: true);
            foreach (var enemy in bm.Enemies) Hook(enemy, isHero: false);
            bm.HeroesChanged += HookHeroes;      // команда меняется (спавн)
            bm.EnemySpawned += HookEnemySpawned; // враги приходят волнами / PvP
        }

        private void HookEnemySpawned(BattleUnit unit) => Hook(unit, isHero: false);

        private void HookHeroes(System.Collections.Generic.IReadOnlyList<BattleUnit> units)
        {
            for (int i = 0; i < units.Count; i++) Hook(units[i], true);
        }

        private void OnDestroy()
        {
            var bm = BattleManager.Instance;
            if (bm != null)
            {
                bm.HeroesChanged -= HookHeroes;
                bm.EnemySpawned -= HookEnemySpawned;
            }
        }

        private void Hook(BattleUnit unit, bool isHero)
        {
            if (unit == null) return;
            unit.Damaged += OnDamaged;
            unit.AbilityCast += OnAbilityCast;
            TintByElement(unit);
            if (battleCamera != null) UnitHealthBarUI.Attach(unit, battleCamera);
            if (isHero) return;
        }

        private void OnDamaged(BattleUnit unit, float amount, bool crit)
        {
            var prefab = damageTextPrefab != null ? damageTextPrefab : GetAutoPrefab();
            Color color = crit ? new Color(1f, 0.55f, 0.1f) : (unit.Team == Team.Player ? Color.red : Color.white);
            FloatingDamageText.Spawn(prefab, unit.UiAnchorPosition, ((int)amount).ToString(), color);
            if (Core.AudioManager.Instance != null)
                Core.AudioManager.Instance.Play(crit ? Core.Sfx.Crit : Core.Sfx.Hit, unit.Team == Team.Enemy ? 0.8f : 1f);
        }

        private void OnAbilityCast(BattleUnit unit, Data.AbilityData ability, bool manual)
        {
            var prefab = damageTextPrefab != null ? damageTextPrefab : GetAutoPrefab();
            if (manual)
                FloatingDamageText.Spawn(prefab, unit.UiAnchorPosition, ability.displayName, new Color(1f, 0.85f, 0.2f));
            if (Core.AudioManager.Instance != null)
                Core.AudioManager.Instance.Play(
                    ability.targetType == AbilityTargetType.HealAlly ? Core.Sfx.Heal : Core.Sfx.Cast, 0.7f);
        }

        private void TintByElement(BattleUnit unit)
        {
            var renderers = unit.GetComponentsInChildren<Renderer>();
            if (renderers == null || renderers.Length == 0) return;
            _mpb.Clear();
            Color c = ElementColors[(int)unit.Element];
            if (unit.Team == Team.Enemy) c = Color.Lerp(c, Color.black, 0.35f);
            _mpb.SetColor(BaseColorId, c);
            _mpb.SetColor(ColorId, c);
            for (int i = 0; i < renderers.Length; i++) renderers[i].SetPropertyBlock(_mpb);
            if (unit.IsBoss && Core.AudioManager.Instance != null)
                Core.AudioManager.Instance.Play(Core.Sfx.BossRoar, 1f);
        }

        private GameObject GetAutoPrefab()
        {
            if (_autoPrefab != null) return _autoPrefab;
            var go = new GameObject("DamageTextProto");
            var tm = go.AddComponent<TextMesh>();
            tm.fontSize = 48;
            tm.characterSize = 0.12f;
            tm.anchor = TextAnchor.MiddleCenter;
            go.AddComponent<FloatingDamageText>();
            go.SetActive(false);
            _autoPrefab = go;
            return _autoPrefab;
        }
    }
}
