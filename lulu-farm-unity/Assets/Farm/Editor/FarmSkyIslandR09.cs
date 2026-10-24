using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    /// <summary>
    /// O7 sky island (user decision 2026-10-24: the farm floats above a cloud sea; nobody can walk off it).
    /// Gameplay cameras never see the cliff (pitch 15–55°), so the island reads through a crisp grass edge, clouds
    /// hugging the rim, a waterfall cove and distant islets. The playable area, invisible walls and runtime bounds
    /// stay exactly as in O6; the rim lies 1.5–4 m outside the walls. Generated meshes/materials are new assets under
    /// GeneratedR09; GroundWithSoilAndPondOpenings and every older asset keep their content.
    /// </summary>
    public static partial class FarmProjectBuilder
    {
        const string IslandFolder = "Assets/Farm/GeneratedR09";
        static readonly Vector2 IslandWalls = new Vector2(17, 12);    // existing invisible boundary half extents
        public const float WaterfallAngle = .089f;                    // east cove, in line with the pond's middle
        const int IslandSamples = 288;

        [Serializable] sealed class IslandRecord
        {
            public string utc, revision = "sky-island-r09", technical = "authored_unverified_until_generated_on_the_Mac";
            public string visual = "pending_actual_viewing", userArt = "not_reviewed";
            public float marginMinimum, marginMaximum, rimMinimumFromWall = 1.5f;
            public int outlineSamples, groundTriangles, cliffTriangles, cloudPuffs, cloudTriangles, rimBushes, rimFlowers, rimTrees, islets;
            public string[] removed;
            public string note = "Playable bounds, walls and route unchanged. Cliff is only visible from islets/overview; not user art acceptance.";
        }

        // Distance of the rim beyond the wall rectangle at polar angle a (radians, x = cos, z = sin).
        public static float IslandMargin(float a)
        {
            float m = 2.7f + .8f * Mathf.Sin(3 * a + .7f) + .5f * Mathf.Sin(5 * a + 2.1f) + .3f * Mathf.Sin(11 * a);
            float d = Mathf.DeltaAngle(WaterfallAngle * Mathf.Rad2Deg, a * Mathf.Rad2Deg) * Mathf.Deg2Rad;
            float G(float x, float w) => Mathf.Exp(-x * x / (2 * w * w));
            m += -1.8f * G(d, .06f) + 1.5f * (G(d - .21f, .07f) + G(d + .21f, .07f));   // cove flanked by two headlands
            return Mathf.Max(1.5f, m);
        }
        static float WallDistance(Vector2 p) => new Vector2(Mathf.Max(Mathf.Abs(p.x) - IslandWalls.x, 0), Mathf.Max(Mathf.Abs(p.y) - IslandWalls.y, 0)).magnitude;
        public static Vector2 IslandPoint(float a, float inset = 0)
        {
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a)); float lo = 0, hi = 80, target = IslandMargin(a) - inset;
            for (int i = 0; i < 48; i++) { float t = (lo + hi) * .5f; if (WallDistance(dir * t) < target) lo = t; else hi = t; }
            return dir * lo;
        }
        static Vector2 WallPoint(float a)
        {
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            float t = Mathf.Min(Mathf.Abs(dir.x) < 1e-6f ? 1e9f : IslandWalls.x / Mathf.Abs(dir.x), Mathf.Abs(dir.y) < 1e-6f ? 1e9f : IslandWalls.y / Mathf.Abs(dir.y));
            return dir * t;
        }
        public static bool InsideIsland(Vector2 p, float inset = 0) => WallDistance(p) <= IslandMargin(Mathf.Atan2(p.y, p.x)) - inset;
        static List<float> IslandAngles()
        {
            var angles = Enumerable.Range(0, IslandSamples).Select(i => -Mathf.PI + i * 2 * Mathf.PI / IslandSamples).ToList();
            foreach (var c in new[] { new Vector2(1, 1), new Vector2(-1, 1), new Vector2(-1, -1), new Vector2(1, -1) })
                angles.Add(Mathf.Atan2(c.y * IslandWalls.y, c.x * IslandWalls.x));   // exact wall corners keep the seam straight
            angles.Sort(); return angles.Where((a, i) => i == 0 || a - angles[i - 1] > 1e-5f).ToList();
        }

        static void OpusSkyIslandR09(Transform landscape)
        {
            Directory.CreateDirectory(IslandFolder + "/Meshes"); Directory.CreateDirectory(IslandFolder + "/Materials"); AssetDatabase.Refresh();
            var record = new IslandRecord(); var removed = new List<string>();
            var root = new GameObject("SkyIsland_r09").transform; root.SetParent(landscape, false);
            var angles = IslandAngles(); record.outlineSamples = angles.Count;
            record.marginMinimum = angles.Min(IslandMargin); record.marginMaximum = angles.Max(IslandMargin);

            // 1. Ground: the O6 ground clipped to the wall rectangle plus a ring out to the rim. Same GameObject,
            //    material and collider owner, so contact audit, polish and route code still find it by name.
            var groundFilter = landscape.GetComponentsInChildren<MeshFilter>(true).Single(m => m.name == "ContinuousGroundWithSoilAndPondOpenings");
            var v = new List<Vector3>(); var t = new List<int>();
            var source = groundFilter.sharedMesh; var sv = source.vertices; var st = source.triangles;
            foreach (var p in sv) v.Add(new Vector3(Mathf.Clamp(p.x, -IslandWalls.x, IslandWalls.x), p.y, Mathf.Clamp(p.z, -IslandWalls.y, IslandWalls.y)));
            for (int i = 0; i < st.Length; i += 3)
                if (Vector3.Cross(v[st[i + 1]] - v[st[i]], v[st[i + 2]] - v[st[i]]).sqrMagnitude > 1e-10f) t.AddRange(new[] { st[i], st[i + 1], st[i + 2] });
            for (int i = 0; i < angles.Count; i++)
            {
                float a = angles[i], b = angles[(i + 1) % angles.Count]; Vector2 wa = WallPoint(a), wb = WallPoint(b), oa = IslandPoint(a), ob = IslandPoint(b);
                int k = v.Count; v.AddRange(new[] { new Vector3(wa.x, 0, wa.y), new Vector3(wb.x, 0, wb.y), new Vector3(ob.x, 0, ob.y), new Vector3(oa.x, 0, oa.y) });
                t.AddRange(new[] { k, k + 1, k + 2, k, k + 2, k + 3 });
            }
            var ground = IslandMesh("IslandGround-r09", v, t, true);
            groundFilter.sharedMesh = ground; var groundCollider = groundFilter.GetComponent<MeshCollider>(); if (groundCollider != null) groundCollider.sharedMesh = ground;
            record.groundTriangles = t.Count / 3;
            var grassMaterial = groundFilter.GetComponent<Renderer>().sharedMaterial;

            // 2. Cliff: crisp grass lip, macaron strata, tapering keel hidden in the cloud floor.
            var strata = new[] { grassMaterial, IslandMat("IslandSoil-r09", "#8E5E3C"), IslandMat("IslandCream-r09", "#E6C38C"),
                IslandMat("IslandClay-r09", "#A26E46"), IslandMat("IslandKeel-r09", "#7D5E4C") };
            var cliff = Cliff("IslandCliff-r09", Vector2.zero, 1, angles, strata, root);
            record.cliffTriangles = cliff.triangles.Length / 3;

            Vector2 lip = IslandPoint(WaterfallAngle), tangent = new Vector2(-Mathf.Sin(WaterfallAngle), Mathf.Cos(WaterfallAngle)), outward = lip.normalized;
            var start = new Vector2(PondMaxX + .45f, lip.y);
            float StreamDistance(Vector2 p) { var d = lip - start; float u = Mathf.Clamp01(Vector2.Dot(p - start, d) / d.sqrMagnitude); return Vector2.Distance(p, start + d * u); }

            // 3. Remove everything that would now stand in the air, plus the old distant tree line and the even
            //    outer tree ring (both replaced by rim planting and the cloud sea).
            foreach (var tr in landscape.GetComponentsInChildren<Transform>(true).ToArray())
            {
                if (tr == null || tr == root || tr.IsChildOf(root) || !PrefabUtility.IsOutermostPrefabInstanceRoot(tr.gameObject)) continue;
                var p = new Vector2(tr.position.x, tr.position.z);
                bool distant = tr.parent != null && tr.parent.name == "DistantTreeLine_NoCollision_NoShadows";
                bool outerTree = (tr.name == "E08" || tr.name == "E09") && WallDistance(p) > .01f;
                if (distant || outerTree || StreamDistance(p) < 1.1f || !InsideIsland(p, .4f)) { removed.Add(tr.name + " @ " + p.ToString("F2")); Object.DestroyImmediate(tr.gameObject); }
            }
            record.removed = removed.ToArray();

            // 4. Rim planting between wall and edge: hides the invisible wall, keeps the waterfall cove open.
            var rim = new GameObject("RimPlanting").transform; rim.SetParent(root, false);
            var random = new System.Random(91024);
            float Next(float lo, float hi) => lo + (float)random.NextDouble() * (hi - lo);
            bool NearCove(float a) => Mathf.Abs(Mathf.DeltaAngle(a * Mathf.Rad2Deg, WaterfallAngle * Mathf.Rad2Deg)) < 9;
            for (float arc = 0; arc < 2 * Mathf.PI; arc += Next(.08f, .13f))   // loose border (~2–3 m): a hedge would read as a hill, not an edge
            {
                float a = arc - Mathf.PI; if (NearCove(a)) continue;
                var p = IslandPoint(a, Next(.6f, Mathf.Min(1.2f, IslandMargin(a) - .3f)));
                bool flower = random.NextDouble() < .45;
                var go = Place(flower ? "E11" : "E10", new Vector3(p.x, 0, p.y), rim, Next(0, 360), flower ? Next(.55f, .8f) : Next(.8f, 1.1f));
                if (go == null) continue; foreach (var c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
                if (flower) record.rimFlowers++; else record.rimBushes++;
            }
            // Clusters of 2–3 trees on the wide headlands only; the south view and the cove stay open.
            foreach (float deg in new[] { 22f, 58f, 128f, 162f, 205f, 232f })
            {
                float a = deg * Mathf.Deg2Rad; if (IslandMargin(a) < 3.1f) continue;
                for (int i = 0, n = 2 + random.Next(2); i < n; i++)
                {
                    float b = a + Next(-.04f, .04f); var p = IslandPoint(b, IslandMargin(b) * Next(.45f, .6f));
                    var tree = Place(random.NextDouble() < .7 ? "E08" : "E09", new Vector3(p.x, 0, p.y), rim, Next(0, 360), Next(.8f, 1.05f));
                    if (tree == null) continue;
                    foreach (var c in tree.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
                    FarmOcclusionSetup.Configure(tree, true); record.rimTrees++;
                }
            }

            // 5. Stream from the pond's east bank to the cove, and the waterfall into the clouds.
            v.Clear(); t.Clear();
            for (int i = 0; i <= 10; i++)
            {
                float s = i / 10f; var c = Vector2.Lerp(start, lip + outward * .04f, s) + tangent * Mathf.Sin(s * Mathf.PI) * .35f; float w = Mathf.Lerp(.55f, .7f, s);
                v.Add(new Vector3(c.x - tangent.x * w, .014f, c.y - tangent.y * w)); v.Add(new Vector3(c.x + tangent.x * w, .014f, c.y + tangent.y * w));
                if (i > 0) { int k = v.Count - 4; t.AddRange(new[] { k, k + 1, k + 3, k, k + 3, k + 2 }); }   // faces up
            }
            var stream = MeshObject(root, "WaterfallStream", IslandMesh("IslandStream-r09", v, t, false), water, false);
            stream.GetComponent<Renderer>().shadowCastingMode = ShadowCastingMode.Off;
            v.Clear(); t.Clear(); var uv = new List<Vector2>();
            for (int j = 0; j <= 16; j++)
            {
                float drop = j * .6f, off = 2.0f * Mathf.Sqrt(drop / 9.81f * 2);   // ballistic, 2 m/s over the lip: from inside the walls only the first metre is in view
                var c = lip + outward * off; float w = .7f + drop * .03f;
                v.Add(new Vector3(c.x - tangent.x * w, .014f - drop, c.y - tangent.y * w)); v.Add(new Vector3(c.x + tangent.x * w, .014f - drop, c.y + tangent.y * w));
                uv.Add(new Vector2(0, drop)); uv.Add(new Vector2(1, drop));
                if (j > 0) { int k = v.Count - 4; t.AddRange(new[] { k, k + 1, k + 3, k, k + 3, k + 2 }); }
            }
            var fallMesh = IslandMesh("IslandWaterfall-r09", v, t, false, uv);
            var fall = MeshObject(root, "Waterfall", fallMesh, IslandShaderMat("Waterfall-r09", "LuluFarm/Waterfall-r09"), false);
            fall.GetComponent<Renderer>().shadowCastingMode = ShadowCastingMode.Off;

            // 6. Cloud sea: puffs hugging the rim, a far field fading into fog, and a floor hiding the keels.
            var cloudMat = IslandShaderMat("SkyCloud-r09", "LuluFarm/SkyCloud-r09");
            var cv = new List<Vector3>(); var ct = new List<int>(); int puffs = 0;
            void Puff(Vector3 c, float size)
            {
                for (int i = 0, n = 3 + random.Next(3); i < n; i++)
                    Ellipsoid(cv, ct, c + new Vector3(Next(-1, 1) * size * .8f, Next(-.15f, .25f) * size, Next(-1, 1) * size * .8f),
                        new Vector3(size * Next(.7f, 1.1f), size * Next(.45f, .6f), size * Next(.7f, 1.1f)));
                puffs++;
            }
            for (float arc = 0; arc < 2 * Mathf.PI; arc += Next(.07f, .11f))
            {
                float a = arc - Mathf.PI; var p = IslandPoint(a); var o = p.normalized;
                var c = p + o * Next(1.2f, 4.5f); Puff(new Vector3(c.x, Next(-3.4f, -2.6f), c.y), Next(1.6f, 2.8f));   // tops stay below the grass (max ≈ -.2 m)
            }
            Puff(new Vector3(lip.x + outward.x * 2.6f, -4.6f, lip.y + outward.y * 2.6f), 2.4f);   // where the fall vanishes
            Puff(new Vector3(lip.x + outward.x * 2.2f, -1.6f, lip.y + outward.y * 2.2f), 1.5f);   // spray rising to rim height, visible from the play area
            for (int i = 0; i < 170; i++)
            {
                float a = Next(-Mathf.PI, Mathf.PI), d = Next(28, 112); Puff(new Vector3(Mathf.Cos(a) * d, Next(-10, -5), Mathf.Sin(a) * d), Next(3, 7.5f));
            }
            var floor = 48; int f0 = cv.Count; cv.Add(new Vector3(0, -9, 0));
            for (int i = 0; i < floor; i++) { float a = i * 2 * Mathf.PI / floor; cv.Add(new Vector3(Mathf.Cos(a) * 170, -9, Mathf.Sin(a) * 170)); }
            for (int i = 0; i < floor; i++) ct.AddRange(new[] { f0, f0 + 1 + (i + 1) % floor, f0 + 1 + i });
            var clouds = MeshObject(root, "CloudSea", IslandMesh("IslandClouds-r09", cv, ct, false), cloudMat, false);
            var cloudRenderer = clouds.GetComponent<Renderer>(); cloudRenderer.shadowCastingMode = ShadowCastingMode.Off; cloudRenderer.receiveShadows = false;
            record.cloudPuffs = puffs; record.cloudTriangles = ct.Count / 3;

            // 7. Three distant islets give the sky depth (inside the fog band, 50–60 m out).
            foreach (var (c, y, s, yaw) in new[] { (new Vector2(46, 30), -1.5f, .16f, 20f), (new Vector2(-52, 24), 2.5f, .12f, 140f), (new Vector2(30, -47), -3.5f, .14f, 260f) })
            {
                var islet = new GameObject("Islet").transform; islet.SetParent(root, false); islet.localPosition = new Vector3(c.x, y, c.y);
                var top = new List<Vector3> { Vector3.zero }; var tt = new List<int>(); var ring = angles.Where((a, i) => i % 4 == 0).ToList();
                foreach (float a in ring) { var p = IslandPoint(a) * s; top.Add(new Vector3(p.x, 0, p.y)); }
                for (int i = 0; i < ring.Count; i++) tt.AddRange(new[] { 0, 1 + (i + 1) % ring.Count, 1 + i });
                var cap = MeshObject(islet, "IsletTop", IslandMesh("IsletTop-r09-" + record.islets, top, tt, true), grassMaterial, false);
                cap.GetComponent<Renderer>().shadowCastingMode = ShadowCastingMode.Off;
                Cliff("IsletCliff-r09-" + record.islets, Vector2.zero, s, ring, strata, islet);
                var tree = Place("E08", Vector3.zero, islet, yaw, s * 9);
                if (tree != null)
                {
                    RetainPolishLastLod(tree); foreach (var col in tree.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(col);
                    foreach (var r in tree.GetComponentsInChildren<Renderer>(true)) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; }
                }
                record.islets++;
            }

            AssetDatabase.SaveAssets();
            record.utc = DateTime.UtcNow.ToString("o");
            string dir = "Evidence/r07/" + R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + "/sky-island-r09.json", JsonUtility.ToJson(record, true));
        }

        static Mesh Cliff(string name, Vector2 center, float scale, List<float> angles, Material[] strata, Transform parent)
        {
            // (radial scale about the island centre, height, stratum); each stratum has its own vertices for hard colour edges.
            var bands = new[] {
                new[] { new Vector2(1, 0), new Vector2(1.004f, -.07f), new Vector2(1.004f, -.16f) },
                new[] { new Vector2(1.004f, -.16f), new Vector2(1.008f, -.6f), new Vector2(1.0f, -1.0f) },
                new[] { new Vector2(1.0f, -1.0f), new Vector2(1.006f, -1.3f), new Vector2(.996f, -1.6f) },
                new[] { new Vector2(.996f, -1.6f), new Vector2(.985f, -2.5f), new Vector2(.955f, -3.4f) },
                new[] { new Vector2(.955f, -3.4f), new Vector2(.89f, -5.2f), new Vector2(.77f, -7.6f), new Vector2(.58f, -10.2f), new Vector2(.36f, -12.6f), new Vector2(.14f, -14.6f), new Vector2(.02f, -15.6f) } };
            var v = new List<Vector3>(); var subs = new List<List<int>>(); var rim = angles.Select(a => IslandPoint(a)).ToList();
            foreach (var band in bands)
            {
                var t = new List<int>(); int b0 = v.Count;
                foreach (var ring in band) foreach (var p in rim) { var q = center + p * ring.x * scale; v.Add(new Vector3(q.x, ring.y * scale, q.y)); }
                int n = rim.Count;
                for (int r = 0; r < band.Length - 1; r++) for (int i = 0; i < n; i++)
                {
                    int u0 = b0 + r * n + i, u1 = b0 + r * n + (i + 1) % n, l0 = u0 + n, l1 = u1 + n;
                    t.AddRange(new[] { u0, u1, l0, u1, l1, l0 });
                }
                subs.Add(t);
            }
            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(v); mesh.subMeshCount = subs.Count;
            for (int i = 0; i < subs.Count; i++) mesh.SetTriangles(subs[i], i);
            mesh.SetUVs(0, v.Select(p => new Vector2(p.x, p.z)).ToList()); mesh.RecalculateNormals(); mesh.RecalculateBounds();
            mesh = SaveIslandMesh(mesh);
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer)); go.transform.SetParent(parent, false);
            go.GetComponent<MeshFilter>().sharedMesh = mesh; var renderer = go.GetComponent<MeshRenderer>(); renderer.sharedMaterials = strata;
            renderer.shadowCastingMode = ShadowCastingMode.Off; return mesh;
        }

        static void Ellipsoid(List<Vector3> v, List<int> t, Vector3 c, Vector3 r)
        {
            const int Lon = 10, Lat = 6; int k = v.Count;
            for (int i = 0; i <= Lat; i++) for (int j = 0; j < Lon; j++)
            {
                float th = Mathf.PI * i / Lat, ph = 2 * Mathf.PI * j / Lon;
                // Flattened underside: clouds sit on a soft base instead of a full sphere.
                float y = Mathf.Cos(th); y = y < 0 ? y * .45f : y;
                v.Add(c + new Vector3(Mathf.Sin(th) * Mathf.Cos(ph) * r.x, y * r.y, Mathf.Sin(th) * Mathf.Sin(ph) * r.z));
            }
            for (int i = 0; i < Lat; i++) for (int j = 0; j < Lon; j++)
            {
                int a = k + i * Lon + j, b = k + i * Lon + (j + 1) % Lon, c2 = a + Lon, d = b + Lon;
                t.AddRange(new[] { a, b, c2, b, d, c2 });
            }
        }

        static Mesh IslandMesh(string name, List<Vector3> v, List<int> t, bool flatUp, List<Vector2> uv = null)
        {
            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(v); mesh.SetTriangles(t, 0);
            mesh.SetUVs(0, uv ?? v.Select(p => new Vector2(p.x, p.z)).ToList());
            if (flatUp) mesh.SetNormals(Enumerable.Repeat(Vector3.up, v.Count).ToList()); else mesh.RecalculateNormals();
            mesh.RecalculateBounds(); return SaveIslandMesh(mesh);
        }
        static Mesh SaveIslandMesh(Mesh mesh)
        {
            string p = IslandFolder + "/Meshes/" + mesh.name + ".asset"; var existing = AssetDatabase.LoadAssetAtPath<Mesh>(p);
            if (existing != null) { EditorUtility.CopySerialized(mesh, existing); Object.DestroyImmediate(mesh); return existing; }
            AssetDatabase.CreateAsset(mesh, p); return mesh;
        }
        static Material IslandMat(string name, string hex)
        {
            var m = IslandShaderMat(name, "Universal Render Pipeline/Lit");
            m.SetColor("_BaseColor", Hex(hex)); m.SetFloat("_Smoothness", .08f); m.SetFloat("_Metallic", 0); EditorUtility.SetDirty(m); return m;
        }
        static Material IslandShaderMat(string name, string shaderName)
        {
            var shader = Shader.Find(shaderName); if (shader == null) throw new InvalidOperationException(shaderName + " shader missing");
            string p = IslandFolder + "/Materials/" + name + ".mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(p);
            if (m == null) { m = new Material(shader); AssetDatabase.CreateAsset(m, p); }
            m.shader = shader; m.enableInstancing = true; EditorUtility.SetDirty(m); return m;
        }
    }
}
