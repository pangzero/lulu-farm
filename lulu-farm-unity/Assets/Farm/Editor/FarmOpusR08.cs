using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace LuluFarm.Editor
{
    /// <summary>
    /// O4 revisions applied only to the Opus O6 stage. Each step derives a new material from the one the
    /// earlier stage produced; D5–D6 materials, shaders and Builder output are left as delivered.
    /// </summary>
    public static partial class FarmProjectBuilder
    {
        const string OpusMaterials = "Assets/Farm/GeneratedR08/Materials";
        public const float AnimalBreathR08 = .01f, AnimalTurnR08 = .1f;

        [Serializable] sealed class OpusR08Record
        {
            public string utc, groundMaterial, groundShader = "LuluFarm/FarmGround-r04", skyMaterial;
            public Color skyHorizon, fogColor;
            public int animalMaterials, vegetationMaterials;
            public float animalBreath = AnimalBreathR08, animalTurnRadians = AnimalTurnR08;
            public string note = "Unverified until generated, built and viewed on the Mac; not user art acceptance";
        }
        static readonly OpusR08Record opusRecord = new OpusR08Record();

        // Round pebbles: same mask, colours and parameters as Ground-polish-r03; only the shader differs.
        static void OpusGroundR04(Transform landscape)
        {
            var ground = landscape.GetComponentsInChildren<MeshFilter>(true).Single(m => m.sharedMesh != null && m.sharedMesh.name == "GroundWithSoilAndPondOpenings").GetComponent<Renderer>();
            var shader = Shader.Find("LuluFarm/FarmGround-r04"); if (shader == null) throw new InvalidOperationException("FarmGround-r04 shader missing");
            var material = Derived("Ground-polish-r04", ground.sharedMaterial, shader);
            ground.sharedMaterial = material; opusRecord.groundMaterial = AssetDatabase.GetAssetPath(material);
        }

        // Spec C's lighter fog no longer matched the untouched sky horizon, so the fully fogged far ground
        // edge showed against the sky. Match the horizon to the fog colour instead of moving the fog.
        static void OpusSkyR08()
        {
            var source = RenderSettings.skybox; var shader = Shader.Find("LuluFarm/FarmSky");
            if (source == null || shader == null) throw new InvalidOperationException("FarmSky material missing before O6 sky revision");
            var material = Derived("FarmSky-r08", source, shader);
            material.SetColor("_Horizon", RenderSettings.fogColor); EditorUtility.SetDirty(material);
            RenderSettings.skybox = material;
            opusRecord.skyMaterial = AssetDatabase.GetAssetPath(material); opusRecord.skyHorizon = RenderSettings.fogColor; opusRecord.fogColor = RenderSettings.fogColor;
        }

        // Larger, still procedural animal breathing / head turn. Runs after FarmLivingSetupR07 and before the
        // dither fade copies the in-use materials, so fades keep the same motion.
        static void OpusLivingR08(Transform world)
        {
            var shader = Shader.Find("LuluFarm/LivingSurface-r08"); if (shader == null) throw new InvalidOperationException("LivingSurface-r08 shader missing");
            var swapped = new Dictionary<Material, Material>();
            foreach (var r in world.GetComponentsInChildren<MeshRenderer>(true))
            {
                var mats = r.sharedMaterials; bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    var m = mats[i]; if (m == null || m.shader.name != "LuluFarm/LivingSurface-r07") continue;
                    if (!swapped.TryGetValue(m, out var d))
                    {
                        d = Derived(Path.GetFileNameWithoutExtension(AssetDatabase.GetAssetPath(m)) + "-r08", m, shader);
                        bool animal = m.GetFloat("_MotionMode") > 1.5f;
                        d.SetFloat("_BreathAmp", animal ? AnimalBreathR08 : .003f); d.SetFloat("_TurnAmp", animal ? AnimalTurnR08 : .035f);
                        EditorUtility.SetDirty(d); swapped.Add(m, d);
                        if (animal) opusRecord.animalMaterials++; else opusRecord.vegetationMaterials++;
                    }
                    mats[i] = d; changed = true;
                }
                if (!changed) continue;
                r.sharedMaterials = mats;
                var occluder = r.GetComponentInParent<FarmCameraOccluder>();
                if (occluder != null && occluder.bindings != null)
                    foreach (var binding in occluder.bindings) if (binding.renderer == r) binding.opaqueMaterials = mats;
            }
        }

        static void OpusWriteRecord()
        {
            AssetDatabase.SaveAssets();
            opusRecord.utc = DateTime.UtcNow.ToString("o");
            string dir = "Evidence/r07/" + R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + "/opus-r08-revisions.json", JsonUtility.ToJson(opusRecord, true));
        }

        static Material Derived(string name, Material source, Shader shader)
        {
            Directory.CreateDirectory(OpusMaterials); AssetDatabase.Refresh();
            string file = OpusMaterials + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(file);
            if (material == null) { material = new Material(shader) { name = name }; AssetDatabase.CreateAsset(material, file); }
            material.shader = shader; material.CopyPropertiesFromMaterial(source); material.shader = shader;
            material.enableInstancing = source.enableInstancing; material.renderQueue = source.renderQueue;
            EditorUtility.SetDirty(material); return material;
        }
    }
}
