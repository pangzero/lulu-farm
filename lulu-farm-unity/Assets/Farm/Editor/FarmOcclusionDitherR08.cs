using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace LuluFarm.Editor
{
    /// <summary>
    /// O3 r08. Replaces the transparent URP/Lit fade variants (ZWrite off, which layered roof / crown shells)
    /// with opaque screen-door variants built from the materials the renderer actually uses after D6.
    /// Plants keep the same wind deformation and lighting as LivingSurface-r07, so the swap does not pop.
    /// Original/imported/D6 materials are read only; the old OcclusionFade assets stay on disk unchanged.
    /// </summary>
    public static class FarmOcclusionDitherR08
    {
        // O7 uses the r09 revision (noise + keyhole, 15 % coverage) in its own folder; O6 output is unchanged.
        static bool R09 => FarmProjectBuilder.R07Island;
        static string Folder => R09 ? "Assets/Farm/GeneratedR09/OcclusionDither" : "Assets/Farm/GeneratedR08/OcclusionDither";
        const string Living = "LuluFarm/LivingSurface-"; // r07 (D6) or r08 (O6 amplitude revision)
        public const float FadedCoverageR08 = .25f, FadedCoverageR09 = .15f;
        static float FadedCoverage => R09 ? FadedCoverageR09 : FadedCoverageR08;
        static readonly string[] ColorProperties = { "_BaseColorFactor", "baseColorFactor", "_BaseColor", "baseColor", "_Color" };
        static readonly string[] TextureProperties = { "_BaseColorTexture", "baseColorTexture", "_BaseMap", "_MainTex", "_BaseColorMap" };
        static readonly string[] NormalProperties = { "normalTexture", "_NormalTexture", "_BumpMap" };

        [Serializable] sealed class Entry { public string occluder, renderer, source, sourceShader, derived; public bool livingCopy; }
        [Serializable] sealed class Record { public string utc, method, shader; public float fadedCoverage; public int occluders, bindings; public Entry[] materials; }

        public static void Apply(Transform world)
        {
            string shaderName = R09 ? "LuluFarm/OcclusionDither-r09" : "LuluFarm/OcclusionDither-r08";
            var shader = Shader.Find(shaderName);
            if (shader == null) throw new InvalidOperationException(shaderName + " shader missing");
            Directory.CreateDirectory(Folder); AssetDatabase.Refresh();
            var entries = new List<Entry>(); var cache = new Dictionary<Material, Material>();
            var occluders = world.GetComponentsInChildren<FarmCameraOccluder>(true);
            int bindingCount = 0;
            foreach (var occluder in occluders)
            {
                if (occluder.bindings == null || occluder.bindings.Length == 0) continue;
                foreach (var binding in occluder.bindings)
                {
                    if (binding?.renderer == null || binding.opaqueMaterials == null) continue;
                    bindingCount++;
                    binding.fadedMaterials = binding.opaqueMaterials.Select(source =>
                    {
                        if (!cache.TryGetValue(source, out var derived))
                        {
                            derived = MakeDither(source, shader);
                            cache.Add(source, derived);
                            entries.Add(new Entry { occluder = occluder.name, renderer = binding.renderer.name, source = AssetDatabase.GetAssetPath(source),
                                sourceShader = source.shader.name, derived = AssetDatabase.GetAssetPath(derived), livingCopy = source.shader.name.StartsWith(Living) });
                        }
                        return derived;
                    }).ToArray();
                }
                occluder.targetRenderer = occluder.bindings[0].renderer;
                occluder.opaqueMaterials = occluder.bindings[0].opaqueMaterials;
                occluder.fadedMaterials = occluder.bindings[0].fadedMaterials;
                occluder.fadedOpacity = FadedCoverage;
                if (!occluder.HasSafeFadeMaterials) throw new InvalidOperationException("Dither fade binding rejected by occluder: " + occluder.name);
                EditorUtility.SetDirty(occluder);
            }
            AssetDatabase.SaveAssets();
            string dir = "Evidence/r07/" + FarmProjectBuilder.R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + (R09 ? "/occlusion-dither-r09.json" : "/occlusion-dither-r08.json"), JsonUtility.ToJson(new Record { utc = DateTime.UtcNow.ToString("o"),
                method = R09 ? "Opaque AlphaTest screen-door fade, interleaved gradient noise, clear keyhole around Lulu, ZWrite on, shadows kept; built from in-use materials" : "Opaque AlphaTest screen-door fade (4x4 ordered dither), ZWrite on, shadows kept; built from in-use materials",
                shader = shaderName, fadedCoverage = FadedCoverage, occluders = occluders.Length, bindings = bindingCount, materials = entries.ToArray() }, true));
        }

        static Material MakeDither(Material source, Shader shader)
        {
            if (!AssetDatabase.TryGetGUIDAndLocalFileIdentifier(source, out string guid, out long localId) || string.IsNullOrEmpty(guid))
                throw new InvalidOperationException("Dither fade needs an asset-backed source material: " + source.name);
            string location = Folder + "/" + guid + "-" + localId + ".mat";
            var fade = AssetDatabase.LoadAssetAtPath<Material>(location);
            if (fade == null) { fade = new Material(shader); AssetDatabase.CreateAsset(fade, location); }
            fade.shader = shader; fade.name = source.name + " — dither fade r08";
            if (source.shader.name.StartsWith(Living))
            {
                // Same property names: identical wind, phase, normal scale and specular as the D6 opaque material.
                fade.CopyPropertiesFromMaterial(source);
            }
            else
            {
                string cp = ColorProperties.FirstOrDefault(source.HasProperty);
                string tp = TextureProperties.FirstOrDefault(p => source.HasProperty(p) && source.GetTexture(p) != null);
                string np = NormalProperties.FirstOrDefault(p => source.HasProperty(p) && source.GetTexture(p) != null);
                string rough = new[] { "roughnessFactor", "_RoughnessFactor" }.FirstOrDefault(source.HasProperty);
                if (cp == null && tp == null) Debug.LogWarning("Dither fade found no base colour on " + source.name + " / " + source.shader.name);
                fade.SetColor("_BaseColor", cp == null ? Color.white : source.GetColor(cp));
                fade.SetTexture("_BaseMap", tp == null ? Texture2D.whiteTexture : source.GetTexture(tp));
                fade.SetTextureScale("_BaseMap", tp == null ? Vector2.one : source.GetTextureScale(tp));
                fade.SetTextureOffset("_BaseMap", tp == null ? Vector2.zero : source.GetTextureOffset(tp));
                fade.SetTexture("_NormalMap", np == null ? null : source.GetTexture(np));
                fade.SetFloat("_NormalScale", np == null ? 0 : 1);
                fade.SetFloat("_Smoothness", rough == null ? .08f : 1 - source.GetFloat(rough));
                fade.SetFloat("_SpecularFactor", source.HasProperty("specularFactor") ? source.GetFloat("specularFactor") : .4f);
                fade.SetFloat("_MotionMode", 0);
                bool twoSided = source.doubleSidedGI || (source.HasProperty("_Cull") && Mathf.Approximately(source.GetFloat("_Cull"), 0)) ||
                    (source.HasProperty("_CullMode") && Mathf.Approximately(source.GetFloat("_CullMode"), 0));
                fade.SetFloat("_Cull", twoSided ? 0 : 2);
            }
            fade.SetFloat("_FadeOpacity", 1);
            if (R09) fade.SetFloat("_FadeFloor", FadedCoverageR09);
            fade.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
            fade.enableInstancing = true;
            EditorUtility.SetDirty(fade);
            return fade;
        }
    }
}
