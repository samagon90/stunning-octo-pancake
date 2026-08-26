using System;
using System.Collections.Generic;
using UnityEngine;
using DreamMasters.Data;

namespace DreamMasters.Battle
{
    /// <summary>Сторона юнита в бою.</summary>
    public enum Team { Player = 0, Enemy = 1 }

    /// <summary>
    /// Юнит на поле боя (герой или враг). Простое поведение без NavMesh:
    /// танки идут вперёд, дальние держат дистанцию; авто-атака + умения.
    /// Ноль аллокаций в Update (все ссылки закешированы).
    /// </summary>
    public class BattleUnit : MonoBehaviour
    {
        [Header("Визуал (прототип: капсулы)")]
        [SerializeField] private Renderer[] tintRenderers;
        [SerializeField] private Transform uiAnchor;

        public string DisplayName { get; private set; }
        public Element Element { get; private set; }
        public AttackRange Range { get; private set; }
        public Team Team { get; private set; }
        public HeroStatsBlock Stats { get; private set; }
        public float MaxHp { get; private set; }
        public float CurrentHp { get; private set; }
        public bool IsAlive => CurrentHp > 0f;
        public bool IsBoss { get; private set; }

        /// <summary>Пассивный бонус синергии к шансу крита.</summary>
        public float BonusCritChance { get; set; }

        /// <summary>Скриптованные множители (канон: первый босс непобедим).</summary>
        public float IncomingDamageMultiplier { get; set; } = 1f;

        private BattleUnit _target;
        private float _attackTimer;
        private AbilityRuntime[] _abilities = Array.Empty<AbilityRuntime>();
        private bool _paused;

        public event Action<BattleUnit, float, bool> Damaged;   // юнит, урон, крит
        public event Action<BattleUnit> Died;
        public event Action<BattleUnit, AbilityData, bool> AbilityCast; // кто, что, вручную?
        public event Action Attacked;                            // обычная атака (анимация/звук)

        public void Initialize(string name, Element element, AttackRange range, Team team,
                               HeroStatsBlock stats, bool isBoss = false)
        {
            DisplayName = name;
            Element = element;
            Range = range;
            Team = team;
            Stats = stats;
            IsBoss = isBoss;
            MaxHp = stats.maxHp;
            CurrentHp = MaxHp;
            _target = null;
            _attackTimer = 0f;
        }

        public void SetAbilities(AbilityRuntime[] abilities, int[] abilityLevels)
        {
            _abilities = abilities ?? Array.Empty<AbilityRuntime>();
            if (abilityLevels != null)
                for (int i = 0; i < _abilities.Length && i < abilityLevels.Length; i++)
                    _abilities[i].Level = abilityLevels[i];
        }

        private static float AttackDistance(AttackRange r) => r switch
        {
            AttackRange.Melee => 1.6f,
            AttackRange.Mid => 5f,
            _ => 8f
        };

        private void Update()
        {
            if (_paused || !IsAlive) return;
            var bm = BattleManager.Instance;
            if (bm == null) return;

            _attackTimer -= Time.deltaTime;
            TickAbilities(bm, autoCast: BattleManager.AutoMode || Team == Team.Enemy);

            if (_target == null || !_target.IsAlive) _target = bm.FindNearestEnemy(this);
            if (_target == null) return;

            float dist = Vector3.Distance(transform.position, _target.transform.position);
            float reach = AttackDistance(Range);

            if (dist > reach) MoveTowards(_target.transform.position);
            else if (_attackTimer <= 0f)
            {
                _attackTimer = 1f / Mathf.Max(0.2f, Stats.attackSpeed);
                BasicAttack(bm);
            }

            RegenHp();
        }

        private void MoveTowards(Vector3 point)
        {
            Vector3 dir = point - transform.position;
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.001f) return;
            transform.position += dir.normalized * (Stats.moveSpeed * Time.deltaTime);
        }

        private void BasicAttack(BattleManager bm)
        {
            float dmg = DamageCalculator.Compute(Stats.attack, _target.Stats.defense, 1f,
                Element, _target.Element, Stats.critChance + BonusCritChance, Stats.critDamage,
                BattleManager.ElementAdvantage, BattleManager.ElementDisadvantage,
                _target.IncomingDamageMultiplier);
            _target.ReceiveDamage(dmg, crit: false);
            Attacked?.Invoke();
        }

        private void TickAbilities(BattleManager bm, bool autoCast)
        {
            for (int i = 0; i < _abilities.Length; i++)
            {
                var ab = _abilities[i];
                if (ab == null) continue;
                ab.Tick();
                if (autoCast && ab.IsReady)
                {
                    ab.Cast();
                    ApplyAbility(bm, ab);
                    AbilityCast?.Invoke(this, ab.Data, false);
                }
            }
        }

        /// <summary>Ручной каст с кнопки HUD. true — умение применено.</summary>
        public bool TryCastManually(int abilityIndex)
        {
            if (_paused || !IsAlive || abilityIndex < 0 || abilityIndex >= _abilities.Length) return false;
            var ab = _abilities[abilityIndex];
            var bm = BattleManager.Instance;
            if (bm == null || ab == null || !ab.IsReady) return false;
            ab.Cast();
            ApplyAbility(bm, ab);
            AbilityCast?.Invoke(this, ab.Data, true);
            return true;
        }

        private void ApplyAbility(BattleManager bm, AbilityRuntime ab)
        {
            var data = ab.Data;
            float power = data.powerCoefficient * (1f + 0.15f * (ab.Level - 1)); // +15% за уровень умения

            switch (data.targetType)
            {
                case AbilityTargetType.HealAlly:
                    BattleUnit wounded = bm.FindMostWoundedAlly(this);
                    if (wounded != null) wounded.Heal(Stats.attack * data.supportValue);
                    break;

                case AbilityTargetType.BuffTeam:
                    bm.ApplyTeamBuff(Team, data.supportValue, data.buffDuration);
                    break;

                case AbilityTargetType.AoeRadius:
                {
                    var enemies = bm.FindEnemiesInRadius(this, transform.position, data.effectRadius);
                    for (int i = 0; i < enemies.Count; i++)
                        enemies[i].ReceiveDamage(Stats.attack * power, Element, Stats.critChance + BonusCritChance);
                    break;
                }

                case AbilityTargetType.Line:
                {
                    var lineTargets = bm.FindEnemiesInRadius(this, transform.position, data.castRange);
                    for (int i = 0; i < lineTargets.Count; i++)
                        lineTargets[i].ReceiveDamage(Stats.attack * power, Element, Stats.critChance + BonusCritChance);
                    break;
                }

                default: // SingleTarget
                {
                    var target = _target != null && _target.IsAlive ? _target : bm.FindNearestEnemy(this);
                    if (target != null)
                        target.ReceiveDamage(Stats.attack * power, Element, Stats.critChance + BonusCritChance);
                    break;
                }
            }
        }

        /// <summary>0..1 готовность умения для HUD.</summary>
        public float GetAbilityReadiness(int index)
        {
            if (index < 0 || index >= _abilities.Length) return 0f;
            var ab = _abilities[index];
            return ab == null ? 0f : ab.Readiness01;
        }

        public void ReceiveDamage(float amount, bool crit)
        {
            if (!IsAlive) return;
            CurrentHp -= amount;
            Damaged?.Invoke(this, amount, crit);
            if (CurrentHp <= 0f)
            {
                CurrentHp = 0f;
                Died?.Invoke(this);
                gameObject.SetActive(false);
            }
        }

        /// <summary>Перегрузка для умений: полный расчёт по формуле с стихией атакующего.</summary>
        public void ReceiveDamage(float attackPower, Element attackerElement, float critChance, float abilityCoefficient = 1f)
        {
            float dmg = DamageCalculator.Compute(attackPower, Stats.defense, abilityCoefficient,
                attackerElement, Element, critChance, Stats.critDamage,
                BattleManager.ElementAdvantage, BattleManager.ElementDisadvantage, IncomingDamageMultiplier);
            ReceiveDamage(dmg, crit: false);
        }

        public void Heal(float amount)
        {
            if (!IsAlive) return;
            CurrentHp = Mathf.Min(MaxHp, CurrentHp + amount);
        }

        private void RegenHp()
        {
            if (Stats.hpRegen <= 0f) return;
            CurrentHp = Mathf.Min(MaxHp, CurrentHp + Stats.hpRegen * Time.deltaTime);
        }

        public void SetPaused(bool paused) => _paused = paused;

        public Vector3 UiAnchorPosition => (uiAnchor != null ? uiAnchor : transform).position + Vector3.up * 2.2f;

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Team == Team.Player ? Color.green : Color.red;
            Gizmos.DrawWireSphere(transform.position, AttackDistance(Range));
        }
    }
}
