using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace LuluFarm.Editor
{
    /// <summary>
    /// O7 animal walking: LivingSurface-r10 materials (r08 + gait) for the five pasture animals and one
    /// FarmAnimalWalkR10 per animal. Runs after OpusLivingR08; source meshes and earlier materials stay unchanged.
    /// Gait numbers were measured from the LOD0 meshes and previewed with Scripts/opus-r07-gait-preview.py.
    /// </summary>
    public static partial class FarmProjectBuilder
    {
        sealed class Gait { public float top0, top1, midZ, stride, lift, bob, biped, roll, speed; }
        static readonly Dictionary<string, Gait> GaitTable = new Dictionary<string, Gait> {
            { "cow",     new Gait { top0 = .15f, top1 = .28f, midZ = -.11f, stride = .10f, lift = .06f, bob = .012f, speed = .32f } },
            { "sheep",   new Gait { top0 = .08f, top1 = .21f, midZ = -.08f, stride = .09f, lift = .05f, bob = .012f, speed = .30f } },
            { "pig",     new Gait { top0 = .05f, top1 = .15f, midZ = -.11f, stride = .09f, lift = .05f, bob = .010f, speed = .28f } },
            { "chicken", new Gait { top0 = .06f, top1 = .19f, midZ = 0,     stride = .10f, lift = .07f, bob = .030f, biped = 1, roll = .03f, speed = .25f } },
            { "duck",    new Gait { top0 = .10f, top1 = .21f, midZ = 0,     stride = .09f, lift = .05f, bob = .020f, biped = 1, roll = .07f, speed = .22f } },
        };

        [Serializable] sealed class WalkEntry { public string animal; public float headSign, strideWorld, speed, cyclesPerSecond; public int renderers, materials; public Vector3 start; }
        [Serializable] sealed class WalkRecord
        {
            public string utc, method = "Vertex gait in LivingSurface-r10 driven by distance travelled; pasture wander with blocked barn/trough/hay/route corridor";
            public Rect area; public Rect[] blocked; public WalkEntry[] animals;
            public string note = "Unverified until generated and played on the Mac; not user art acceptance";
        }

        static void OpusAnimalWalkR10(Transform world, FarmRuntimeBootstrap runtime)
        {
            var shader = Shader.Find("LuluFarm/LivingSurface-r10"); if (shader == null) throw new InvalidOperationException("LivingSurface-r10 shader missing");
            var pasture = world.Find("Pasture"); if (pasture == null) throw new InvalidOperationException("Pasture group missing");
            // Fences run x -3.6..6, z -6.5..1.9; keep animals .8 m inside them.
            var area = Rect.MinMaxRect(-2.8f, -5.7f, 5.2f, 1.1f);
            var blocked = new List<Rect> { Rect.MinMaxRect(1.3f, -6.6f, 5.0f, -2.4f) };   // gate → trough → gate route corridor
            foreach (Transform child in pasture)
                if (child.name.StartsWith("S02") || child.name.StartsWith("S09") || child.name.StartsWith("E15"))
                { var b = BoundsOf(child.gameObject); blocked.Add(Rect.MinMaxRect(b.min.x - .7f, b.min.z - .7f, b.max.x + .7f, b.max.z + .7f)); }
            var entries = new List<WalkEntry>(); var derived = new Dictionary<Material, Material>(); int seed = 0;
            foreach (Transform child in pasture)
            {
                if (!GaitTable.TryGetValue(child.name, out var g)) continue;
                var renderers = child.GetComponentsInChildren<MeshRenderer>(true);
                var lod0 = renderers.Select(r => r.GetComponent<MeshFilter>()?.sharedMesh).FirstOrDefault(m => m != null);
                if (lod0 == null) throw new InvalidOperationException("No mesh on " + child.name);
                float headSign = HeadSign(lod0);
                foreach (var r in renderers)
                {
                    var mats = r.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                    {
                        var m = mats[i]; if (m == null || !m.shader.name.StartsWith("LuluFarm/LivingSurface-")) continue;
                        if (!derived.TryGetValue(m, out var d))
                        {
                            d = Derived(Path.GetFileNameWithoutExtension(AssetDatabase.GetAssetPath(m)) + "-r10", m, shader);
                            d.SetFloat("_GaitTop0", g.top0); d.SetFloat("_GaitTop1", g.top1); d.SetFloat("_GaitMidZ", g.midZ * headSign);
                            d.SetFloat("_GaitStride", g.stride * headSign); d.SetFloat("_GaitLift", g.lift); d.SetFloat("_GaitBob", g.bob);
                            d.SetFloat("_GaitBiped", g.biped); d.SetFloat("_GaitRoll", g.roll); d.SetFloat("_GaitPhase", 0); d.SetFloat("_GaitAmount", 0);
                            EditorUtility.SetDirty(d); derived.Add(m, d);
                        }
                        mats[i] = d;
                    }
                    r.sharedMaterials = mats;
                }
                // Object → world scale of the mesh (prefab adapter × placement); body travel per gait cycle is 4 × stride.
                float scale = renderers[0].transform.lossyScale.y, strideWorld = 4 * g.stride * scale;
                var walker = child.gameObject.AddComponent<FarmAnimalWalkR10>();
                walker.runtime = runtime; walker.renderers = renderers; walker.area = area; walker.blocked = blocked.ToArray();
                walker.speed = g.speed; walker.strideWorld = strideWorld; walker.headSign = headSign; walker.seed = 51024 + 97 * seed++;
                var body = child.GetComponent<Rigidbody>(); if (body == null) body = child.gameObject.AddComponent<Rigidbody>();
                body.isKinematic = true; body.useGravity = false;   // its footprint collider now moves
                EditorUtility.SetDirty(walker);
                entries.Add(new WalkEntry { animal = child.name, headSign = headSign, strideWorld = strideWorld, speed = g.speed, cyclesPerSecond = g.speed / strideWorld,
                    renderers = renderers.Length, materials = renderers.Sum(r => r.sharedMaterials.Length), start = child.position });
            }
            if (entries.Count != GaitTable.Count) throw new InvalidOperationException("Expected five pasture animals for walking, found " + entries.Count);
            AssetDatabase.SaveAssets();
            string dir = "Evidence/r07/" + R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + "/animal-walk-r10.json", JsonUtility.ToJson(new WalkRecord { utc = DateTime.UtcNow.ToString("o"), area = area, blocked = blocked.ToArray(), animals = entries.ToArray() }, true));
        }

        // +1 when the head (upper 40 % of the body) lies toward +z in mesh space, as measured on the source glTFs.
        static float HeadSign(Mesh mesh)
        {
            if (!mesh.isReadable) Debug.LogWarning("Gait head direction read from a non-readable mesh in the Editor: " + mesh.name);
            var v = mesh.vertices; if (v.Length == 0) throw new InvalidOperationException("Gait needs mesh vertices: " + mesh.name);
            float lo = v.Min(p => p.y), hi = v.Max(p => p.y), cut = lo + .6f * (hi - lo);
            var upper = v.Where(p => p.y > cut).ToArray();
            return upper.Length == 0 || upper.Average(p => p.z) >= 0 ? 1 : -1;
        }
    }
}
