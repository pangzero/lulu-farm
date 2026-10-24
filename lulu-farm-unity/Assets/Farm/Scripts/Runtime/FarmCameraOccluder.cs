using System;
using System.Collections.Generic;
using UnityEngine;

namespace LuluFarm
{
    [Serializable]
    public sealed class FarmOcclusionBinding
    {
        public Renderer renderer;
        public Material[] opaqueMaterials;
        public Material[] fadedMaterials;
    }

    // Assigned only to deliberate house/tree blockers. Imported material objects are never edited.
    public sealed class FarmCameraOccluder : MonoBehaviour
    {
        static readonly HashSet<FarmCameraOccluder> live = new HashSet<FarmCameraOccluder>();
        public static IEnumerable<FarmCameraOccluder> Active => live;
        // Retained for compatibility with the original single-renderer API.
        public Renderer targetRenderer;
        public Material[] opaqueMaterials;
        public Material[] fadedMaterials;
        public FarmOcclusionBinding[] bindings = Array.Empty<FarmOcclusionBinding>();
        public Collider[] occlusionColliders = Array.Empty<Collider>();
        [Range(.05f, .5f)] public float fadedOpacity = .07f;
        public float transitionSeconds = .12f;
        public bool AllowsCameraPassThrough => applied && opacity <= .35f;
        public bool IsOccluded => wanted;
        public float CurrentOpacity => opacity;
        bool wanted, applied;
        float opacity = 1;
        MaterialPropertyBlock[][] savedBlocks, fadeBlocks;
        FarmOcclusionBinding[] activeBindings;

        public bool HasSafeFadeMaterials
        {
            get
            {
                if (bindings != null && bindings.Length > 0)
                {
                    foreach (var binding in bindings) if (!Valid(binding)) return false;
                    return true;
                }
                return Valid(targetRenderer, opaqueMaterials, fadedMaterials);
            }
        }

        static bool Valid(FarmOcclusionBinding b) => b != null && Valid(b.renderer, b.opaqueMaterials, b.fadedMaterials);
        static bool Valid(Renderer renderer, Material[] original, Material[] faded)
        {
            if (renderer == null || original == null || faded == null || original.Length == 0 || original.Length != faded.Length) return false;
            for (int i = 0; i < original.Length; i++)
                if (original[i] == null || faded[i] == null || !faded[i].HasProperty("_BaseColor")
                    || !faded[i].HasProperty("_Surface") || faded[i].GetFloat("_Surface") < .5f
                    || !faded[i].HasProperty("_ZWrite") || faded[i].GetFloat("_ZWrite") > .5f
                    || faded[i].renderQueue < (int)UnityEngine.Rendering.RenderQueue.Transparent) return false;
            return true;
        }

        // Physical wall/trunk proxies intentionally omit decoration. Check the prepared renderers too,
        // so a window box or a low crown cannot hide Lulu before a wall collider is encountered.
        public bool IntersectsViewCorridor(Vector3 origin, Vector3 direction, float length, float radius, out float entry)
        {
            entry = float.PositiveInfinity;
            if (!isActiveAndEnabled) return false;
            if (bindings != null && bindings.Length > 0)
            {
                foreach (var binding in bindings)
                    if (binding != null) CorridorEntry(binding.renderer, origin, direction, length, radius, ref entry);
            }
            else CorridorEntry(targetRenderer, origin, direction, length, radius, ref entry);
            return !float.IsPositiveInfinity(entry);
        }

        static void CorridorEntry(Renderer renderer, Vector3 origin, Vector3 direction, float length, float radius, ref float entry)
        {
            if (renderer == null || !renderer.enabled || !renderer.gameObject.activeInHierarchy) return;
            Bounds bounds = renderer.bounds;
            bounds.Expand(radius * 2);
            if (bounds.Contains(origin)) { entry = 0; return; }
            if (length > .001f && bounds.IntersectRay(new Ray(origin, direction), out float hit) && hit <= length)
                entry = Mathf.Min(entry, hit);
        }

        public bool OwnsCollider(Collider candidate)
        {
            if (candidate == null) return false;
            if (occlusionColliders != null && occlusionColliders.Length > 0)
            {
                foreach (var collider in occlusionColliders) if (collider == candidate) return true;
                return false;
            }
            // Single-renderer compatibility is intentionally narrow: only a collider on the same object.
            return candidate.gameObject == gameObject;
        }

        public void SetOccluded(bool value, bool immediatePassage = false)
        {
            if (!HasSafeFadeMaterials) return;
            wanted = value;
            if (value && !applied) BeginFade();
            // A sudden orbit/near overlap must not spend a frame at opacity 1 while the camera
            // collapses into the character. Only prepared, independent fade materials are affected.
            if (value && immediatePassage && opacity > .35f)
            {
                opacity = Mathf.Min(fadedOpacity, .35f);
                ApplyOpacity();
            }
        }

        void BeginFade()
        {
            activeBindings = bindings != null && bindings.Length > 0 ? bindings :
                new[] { new FarmOcclusionBinding { renderer = targetRenderer, opaqueMaterials = opaqueMaterials, fadedMaterials = fadedMaterials } };
            savedBlocks = new MaterialPropertyBlock[activeBindings.Length][];
            fadeBlocks = new MaterialPropertyBlock[activeBindings.Length][];
            for (int i = 0; i < activeBindings.Length; i++)
            {
                var binding = activeBindings[i];
                savedBlocks[i] = new MaterialPropertyBlock[binding.opaqueMaterials.Length];
                fadeBlocks[i] = new MaterialPropertyBlock[binding.opaqueMaterials.Length];
                for (int slot = 0; slot < savedBlocks[i].Length; slot++)
                {
                    savedBlocks[i][slot] = new MaterialPropertyBlock();
                    binding.renderer.GetPropertyBlock(savedBlocks[i][slot], slot);
                    fadeBlocks[i][slot] = new MaterialPropertyBlock();
                }
                binding.renderer.sharedMaterials = binding.fadedMaterials;
            }
            opacity = 1; applied = true;
            ApplyOpacity();
        }

        void Update()
        {
            if (!applied) return;
            opacity = Mathf.MoveTowards(opacity, wanted ? Mathf.Min(fadedOpacity, .35f) : 1, Time.unscaledDeltaTime / Mathf.Max(.01f, transitionSeconds));
            ApplyOpacity();
            if (!wanted && opacity >= .999f) Restore();
        }

        void ApplyOpacity()
        {
            for (int i = 0; i < activeBindings.Length; i++)
            {
                var binding = activeBindings[i];
                if (binding.renderer == null) continue;
                for (int slot = 0; slot < binding.fadedMaterials.Length; slot++)
                {
                    Color color = binding.fadedMaterials[slot].GetColor("_BaseColor"); color.a = opacity;
                    fadeBlocks[i][slot].SetColor("_BaseColor", color);
                    binding.renderer.SetPropertyBlock(fadeBlocks[i][slot], slot);
                }
            }
        }

        void Restore()
        {
            if (!applied) return;
            for (int i = 0; i < activeBindings.Length; i++)
            {
                var binding = activeBindings[i];
                if (binding.renderer == null) continue;
                binding.renderer.sharedMaterials = binding.opaqueMaterials;
                for (int slot = 0; slot < savedBlocks[i].Length; slot++) binding.renderer.SetPropertyBlock(savedBlocks[i][slot], slot);
            }
            wanted = applied = false; opacity = 1;
            activeBindings = null; savedBlocks = fadeBlocks = null;
        }
        void OnEnable() { live.Add(this); }
        void OnDisable() { live.Remove(this); Restore(); }
        void OnDestroy() { live.Remove(this); Restore(); }
    }
}
