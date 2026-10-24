using System.Collections.Generic;
using UnityEngine;

namespace LuluFarm
{
    /// <summary>
    /// O7 (user request 2026-10-24: "正常的走路，你看它是走的而不是平移就行"). Slow pasture wander for one animal:
    /// idle, turn toward a free spot, walk there, idle again. The legs are animated by LivingSurface-r10 from the
    /// distance actually travelled, so the feet do not slide. No path finding, needs or interaction with Lulu
    /// beyond stopping when she is close. Uses the same pause and motion switches as the other r07 ambient motion.
    /// </summary>
    public sealed class FarmAnimalWalkR10 : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public Renderer[] renderers = new Renderer[0];
        public Rect area;                       // walkable pasture interior (x, z)
        public Rect[] blocked = new Rect[0];    // barn, trough, hay, Lulu's route corridor (already expanded)
        public float speed = .3f, turnDegreesPerSecond = 90, strideWorld = .28f, headSign = 1, personalSpace = 1.1f;
        public int seed = 1;

        static readonly List<FarmAnimalWalkR10> Herd = new List<FarmAnimalWalkR10>();
        static readonly int PhaseId = Shader.PropertyToID("_GaitPhase"), AmountId = Shader.PropertyToID("_GaitAmount"), MotionId = Shader.PropertyToID("_FarmR07MotionEnabled");
        System.Random random; MaterialPropertyBlock block; Vector3 target; float wait, phase, amount; bool walking;

        public Vector3 Target => walking ? target : transform.position;

        void OnEnable() { Herd.Add(this); }
        void OnDisable() { Herd.Remove(this); }
        void Start() { random = new System.Random(seed); block = new MaterialPropertyBlock(); wait = Next(1, 4); Apply(); }

        float Next(float lo, float hi) => lo + (float)random.NextDouble() * (hi - lo);
        Vector3 Forward => transform.forward * headSign;

        void Update()
        {
            if (Shader.GetGlobalFloat(MotionId) < .5f || (runtime != null && runtime.Input != null && runtime.Input.Paused))
            { if (amount > 0) { amount = 0; Apply(); } return; }
            float dt = Time.deltaTime; bool moving = false, turning = false;
            if (!walking)
            {
                wait -= dt;
                if (wait <= 0 && PickTarget()) walking = true; else if (wait <= 0) wait = Next(1, 3);
            }
            if (walking)
            {
                var to = target - transform.position; to.y = 0;
                if (to.magnitude < .12f) { walking = false; wait = Next(2.5f, 7f); }
                else
                {
                    float signed = Vector3.SignedAngle(Forward, to, Vector3.up);
                    float turn = Mathf.Clamp(signed, -turnDegreesPerSecond * dt, turnDegreesPerSecond * dt);
                    transform.Rotate(0, turn, 0, Space.World); turning = Mathf.Abs(turn) > .01f;
                    if (Mathf.Abs(signed) < 25)
                    {
                        float step = Mathf.Min(speed * dt * Mathf.Cos(signed * Mathf.Deg2Rad), to.magnitude);
                        var next = transform.position + Forward * step;
                        if (Crowded(next)) { walking = false; wait = Next(1.5f, 3f); }
                        else { transform.position = next; phase += step / strideWorld * Mathf.PI * 2; moving = true; }
                    }
                }
            }
            // Turning on the spot still shuffles the feet a little; standing still settles them back.
            if (turning && !moving) phase += dt * Mathf.PI * 2 * .6f;
            amount = Mathf.MoveTowards(amount, moving ? 1 : turning ? .6f : 0, dt * 3);
            Apply();
        }

        bool Crowded(Vector3 p)
        {
            var player = runtime != null && runtime.playerRoot != null ? runtime.playerRoot.transform : null;
            if (player != null && Flat(player.position - p) < 1.4f) return true;
            foreach (var other in Herd)
                if (other != this && Flat(other.transform.position - p) < personalSpace && Flat(other.transform.position - p) < Flat(other.transform.position - transform.position)) return true;
            return false;
        }

        bool PickTarget()
        {
            var here = new Vector2(transform.position.x, transform.position.z);
            for (int attempt = 0; attempt < 24; attempt++)
            {
                var p = new Vector2(Next(area.xMin, area.xMax), Next(area.yMin, area.yMax));
                if ((p - here).magnitude < 1.2f || (p - here).magnitude > 4.5f) continue;
                if (!Clear(here, p)) continue;
                bool near = false;
                foreach (var other in Herd)
                    if (other != this && (Flat(other.Target - new Vector3(p.x, 0, p.y)) < personalSpace + .4f || Flat(other.transform.position - new Vector3(p.x, 0, p.y)) < personalSpace + .4f)) near = true;
                if (near) continue;
                target = new Vector3(p.x, transform.position.y, p.y); return true;
            }
            return false;
        }

        // The segment may leave a blocked rect the animal already stands in, but never enter one.
        bool Clear(Vector2 a, Vector2 b)
        {
            foreach (var r in blocked)
            {
                bool startInside = r.Contains(a);
                for (int i = 1; i <= 10; i++) if (r.Contains(Vector2.Lerp(a, b, i / 10f)) && !startInside) return false;
                if (startInside && r.Contains(b)) return false;
            }
            return true;
        }

        static float Flat(Vector3 v) { v.y = 0; return v.magnitude; }

        void Apply()
        {
            if (block == null) return;
            foreach (var r in renderers)
            {
                if (r == null) continue;
                r.GetPropertyBlock(block); block.SetFloat(PhaseId, phase); block.SetFloat(AmountId, amount); r.SetPropertyBlock(block);
            }
        }
    }
}
