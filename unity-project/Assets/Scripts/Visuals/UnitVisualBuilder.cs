using UnityEngine;
using DreamMasters.Battle;
using DreamMasters.Data;

namespace DreamMasters.Visuals
{
    /// <summary>
    /// Процедурный «модельщик» юнитов: тело+голова+оружие по роли, цвет стихии,
    /// боссам — корона и масштаб. Пока нет 3D-художника — персонажи узнаваемые и разные.
    /// Позже просто заменяется на префабы через HeroData.portrait / EnemyData.viewPrefab.
    /// </summary>
    public static class UnitVisualBuilder
    {
        private static readonly Color[] ElementColors =
        {
            new Color(0.93f, 0.32f, 0.20f), // Огонь
            new Color(0.78f, 0.88f, 0.98f), // Воздух
            new Color(0.55f, 0.72f, 0.35f), // Земля
            new Color(0.30f, 0.55f, 0.95f)  // Вода
        };

        private static MaterialPropertyBlock _mpb;
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");

        /// <summary>Собирает визуал под юнита (тело/голова/оружие/корона) и вешает на него.</summary>
        public static void Attach(BattleUnit unit, HeroRole role, AttackRange range, bool isBoss, bool isEnemy)
        {
            if (unit == null) return;
            if (_mpb == null) _mpb = new MaterialPropertyBlock();

            Color element = ElementColors[(int)unit.Element];
            Color bodyColor = isEnemy ? Color.Lerp(element, Color.black, 0.45f) : element;

            var root = new GameObject("Visual");
            root.transform.SetParent(unit.transform, false);

            float scale = isBoss ? 1.8f : (role == HeroRole.Tank ? 1.2f : 1f);

            // Тело
            var body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            DisableCollider(body);
            body.name = "Body";
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.95f * scale, 0f);
            body.transform.localScale = new Vector3(0.75f * scale, 0.55f * scale, 0.75f * scale);
            Paint(body, Color.Lerp(bodyColor, Color.white, 0.15f));

            // Голова
            var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            DisableCollider(head);
            head.name = "Head";
            head.transform.SetParent(root.transform, false);
            head.transform.localPosition = new Vector3(0f, 1.85f * scale, 0f);
            head.transform.localScale = Vector3.one * (0.55f * scale);
            Paint(head, Color.Lerp(element, Color.white, 0.65f));

            // Оружие по дальнобойности (канон: ближняя — танки, средняя — бойцы, дальняя — поддержка)
            var weapon = GameObject.CreatePrimitive(range == AttackRange.Melee ? PrimitiveType.Cube : PrimitiveType.Cylinder);
            DisableCollider(weapon);
            weapon.name = range == AttackRange.Melee ? "Sword" : "Staff";
            weapon.transform.SetParent(root.transform, false);
            if (range == AttackRange.Melee)
            {
                weapon.transform.localPosition = new Vector3(0.55f * scale, 1.05f * scale, 0.15f);
                weapon.transform.localRotation = Quaternion.Euler(0, 0, -35f);
                weapon.transform.localScale = new Vector3(0.12f, 1.1f * scale, 0.3f);
            }
            else
            {
                weapon.transform.localPosition = new Vector3(0.55f * scale, 1.0f * scale, 0.1f);
                weapon.transform.localRotation = Quaternion.Euler(15f, 0, -12f);
                weapon.transform.localScale = new Vector3(0.09f, 1.5f * scale, 0.09f);
            }
            Paint(weapon, role == HeroRole.Support ? new Color(0.95f, 0.85f, 0.35f) : new Color(0.8f, 0.8f, 0.85f));

            // Корона босса
            if (isBoss)
            {
                var crown = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                DisableCollider(crown);
                crown.name = "Crown";
                crown.transform.SetParent(root.transform, false);
                crown.transform.localPosition = new Vector3(0f, 2.25f * scale, 0f);
                crown.transform.localScale = new Vector3(0.45f * scale, 0.08f, 0.45f * scale);
                Paint(crown, new Color(1f, 0.8f, 0.15f));
            }

            // Аниматор: спавн-поп, дыхание, выпады, вздрагивания (без AnimationClip)
            var animator = root.AddComponent<UnitAnimator>();
            animator.Bind(unit, root.transform);
        }

        private static void DisableCollider(GameObject go)
        {
            var col = go.GetComponent<Collider>();
            if (col != null) col.enabled = false;
        }

        private static void Paint(GameObject go, Color color)
        {
            var r = go.GetComponent<Renderer>();
            _mpb.Clear();
            _mpb.SetColor(BaseColorId, color);
            _mpb.SetColor(ColorId, color);
            r.SetPropertyBlock(_mpb);
        }
    }
}
