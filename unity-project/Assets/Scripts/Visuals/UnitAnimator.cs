using UnityEngine;
using DreamMasters.Battle;

namespace DreamMasters.Visuals
{
    /// <summary>
    /// Процедурная анимация юнита (без AnimationClip): спавн-«поп», дыхание в идле,
    /// наклон в движении, выпад при атаке, вздрагивание при уроне. Вешается UnitVisualBuilder'ом.
    /// </summary>
    public class UnitAnimator : MonoBehaviour
    {
        private BattleUnit _unit;
        private Transform _visual;
        private Vector3 _baseScale;
        private float _spawnT;
        private float _lunge;
        private float _flinch;
        private float _bobPhase;
        private Vector3 _lastPos;

        public void Bind(BattleUnit unit, Transform visualRoot)
        {
            _unit = unit;
            _visual = visualRoot;
            _baseScale = visualRoot.localScale;
            _spawnT = 0.3f;
            _bobPhase = Random.value * Mathf.PI * 2f;
            _lastPos = transform.position;
            _lunge = 0f; _flinch = 0f;

            unit.Damaged += OnDamaged;
            unit.Attacked += OnAttacked;
            unit.AbilityCast += OnAbilityCast;
        }

        private void OnDestroy()
        {
            if (_unit == null) return;
            _unit.Damaged -= OnDamaged;
            _unit.Attacked -= OnAttacked;
            _unit.AbilityCast -= OnAbilityCast;
        }

        private void OnDamaged(BattleUnit unit, float amount, bool crit) => _flinch = 1f;
        private void OnAttacked() => _lunge = 1f;
        private void OnAbilityCast(BattleUnit unit, Data.AbilityData data, bool manual) => _lunge = 1.4f;

        private void Update()
        {
            if (_visual == null || _unit == null || !_unit.IsAlive) return;

            float dt = Time.deltaTime;

            // Спавн: пружинка к базовому масштабу
            if (_spawnT > 0f)
            {
                _spawnT -= dt;
                float k = 1f - Mathf.Clamp01(_spawnT / 0.3f);
                _visual.localScale = _baseScale * (1.25f - 0.25f * k);
            }
            else _visual.localScale = _baseScale;

            // Движение: наклон в сторону хода + быстрее «шаги»
            Vector3 delta = transform.position - _lastPos;
            _lastPos = transform.position;
            float speed01 = Mathf.Clamp01(delta.magnitude / Mathf.Max(0.001f, dt) / 4f);

            // Выпад вперёд (к цели) и вздрагивание гаснут
            _lunge = Mathf.Max(0f, _lunge - dt * 4f);
            _flinch = Mathf.Max(0f, _flinch - dt * 5f);

            _bobPhase += dt * (3f + speed01 * 9f);
            float bob = Mathf.Sin(_bobPhase) * (0.02f + speed01 * 0.05f);

            _visual.localPosition = new Vector3(
                0f,
                bob - _flinch * 0.08f,
                _unit.Team == Team.Player ? _lunge * 0.25f : -_lunge * 0.25f);

            _visual.localRotation = Quaternion.Euler(
                _flinch * 12f,
                0f,
                -delta.x * 4f); // лёгкий крен при стрейфе
        }
    }
}
