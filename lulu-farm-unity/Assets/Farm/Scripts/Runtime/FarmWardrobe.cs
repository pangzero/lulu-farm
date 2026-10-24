using System;
using System.Collections.Generic;
using UnityEngine;

namespace LuluFarm
{
    [Serializable]
    public sealed class FarmWardrobeBinding
    {
        public Renderer renderer;
        public Material[] original;
        public Material[] blueStars;
        public Material[] watermelon;
    }

    public sealed class FarmWardrobe : MonoBehaviour
    {
        public FarmWardrobeBinding[] bindings = Array.Empty<FarmWardrobeBinding>();
        public int CurrentIndex { get; private set; }
        public string CurrentName => CurrentIndex == 0 ? "原版短裤" : CurrentIndex == 1 ? "蓝色星星" : "西瓜短裤";
        public bool IsConfigured => ValidatePreset(0) && ValidatePreset(1) && ValidatePreset(2);
        public bool SetPreset(int index)
        {
            index = Mathf.Clamp(index, 0, 2);
            if (!ValidatePreset(index)) return false;
            foreach (var binding in bindings)
                binding.renderer.sharedMaterials = index == 0 ? binding.original : index == 1 ? binding.blueStars : binding.watermelon;
            CurrentIndex = index;
            return true;
        }
        public bool ValidatePreset(int index)
        {
            if (bindings == null || bindings.Length == 0 || index < 0 || index > 2) return false;
            var seen = new HashSet<Renderer>();
            foreach (var binding in bindings)
            {
                if (binding == null || binding.renderer == null || !seen.Add(binding.renderer)) return false;
                Material[] materials = index == 0 ? binding.original : index == 1 ? binding.blueStars : binding.watermelon;
                if (materials == null || materials.Length == 0 || materials.Length != binding.renderer.sharedMaterials.Length) return false;
                foreach (Material material in materials) if (material == null || material.shader == null) return false;
            }
            return true;
        }
        public bool CurrentPresetIsApplied()
        {
            if (!ValidatePreset(CurrentIndex)) return false;
            foreach (var binding in bindings)
            {
                var expected = CurrentIndex == 0 ? binding.original : CurrentIndex == 1 ? binding.blueStars : binding.watermelon;
                var actual = binding.renderer.sharedMaterials;
                for (int i = 0; i < expected.Length; i++) if (actual[i] != expected[i]) return false;
            }
            return true;
        }
    }
}
