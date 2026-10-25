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
        // O8 (r11) writes every island asset to its own folder so the O7 outputs stay as they were generated.
        static string IslandFolder => R07IslandR11 ? "Assets/Farm/GeneratedR11" : "Assets/Farm/GeneratedR09";
        static readonly Vector2 IslandWalls = new Vector2(17, 12);    // existing invisible boundary half extents
        public const float WaterfallAngle = .089f;                    // east cove, in line with the pond's middle
        const int IslandSamples = 288;
        const string IslandHorizon = "#DDEDF2";   // r10: fog, sky horizon and tower fog share this colour

        [Serializable] sealed class IslandRecord
        {
            public string utc, skyMaterial, revision = "sky-island-r10", technical = "authored_unverified_until_generated_on_the_Mac";
            public string visual = "pending_actual_viewing", userArt = "not_reviewed";
            public Color sunColor; public float sunIntensity, sunPitch;
            public float marginMinimum, marginMaximum, rimMinimumFromWall = 1.5f;
            public int edgeWallSegments, outlineSamples, groundTriangles, cliffTriangles, cloudPuffs, cloudTriangles, towerTriangles, birds, rimBushes, rimFlowers, rimTrees, meadowFlowers, coveReeds, islets, isletProps;
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
            if (R07IslandR11) { record.revision = "sky-island-r11"; record.note = "O8: walls follow the island edge (.8 m inside the rim), runtime bounds 52x42; route unchanged. Not user art acceptance."; }
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

            // 1b. Sunlit rim (r10): the last 1.8 m of grass reads a little warmer and brighter, so the edge stands out.
            {
                var rv = new List<Vector3>(); var rt = new List<int>(); var ruv = new List<Vector2>();
                for (int i = 0; i < angles.Count; i++)
                {
                    float a = angles[i]; Vector2 outer = IslandPoint(a), inner = outer - outer.normalized * (R07IslandR11 ? 2.4f : 1.8f);   // along the ray: IslandPoint(a, 1.8) collapses where the margin is < 1.8
                    rv.Add(new Vector3(inner.x, .004f, inner.y)); rv.Add(new Vector3(outer.x, .004f, outer.y)); ruv.Add(new Vector2(0, 0)); ruv.Add(new Vector2(0, 1));
                    int k = 2 * i, n = 2 * ((i + 1) % angles.Count);
                    rt.AddRange(new[] { k, n, n + 1, k, n + 1, k + 1 });   // faces up (inner→next inner→next outer)
                }
                var glowMat = IslandShaderMat("IslandRimLight-r10", "LuluFarm/IslandRimLight-r10");
                if (R07IslandR11) glowMat.SetColor("_Glow", new Color(.42f, .34f, .14f, 1));   // O7: not readable in the follow view
                var glow = MeshObject(root, "SunlitRim", IslandMesh("IslandRimLight-r10", rv, rt, true, ruv), glowMat, false);
                NoShadows(glow);
            }

            // 2. Cliff: crisp grass lip, macaron strata, tapering keel hidden in the cloud floor.
            var strata = new[] { grassMaterial, IslandMat("IslandSoil-r09", "#8E5E3C"), IslandMat("IslandCream-r09", "#E6C38C"),
                IslandMat("IslandClay-r09", "#A26E46"), IslandMat("IslandKeel-r09", "#7D5E4C") };
            var cliff = Cliff("IslandCliff-r09", Vector2.zero, 1, angles, strata, root);
            record.cliffTriangles = cliff.triangles.Length / 3;

            Vector2 lip = IslandPoint(WaterfallAngle), tangent = new Vector2(-Mathf.Sin(WaterfallAngle), Mathf.Cos(WaterfallAngle)), outward = lip.normalized;
            // O7: a grass and stone band separated stream and pond. r11 starts the stream over the bank turf (y .014 is above
            // the turf's flat outer band), so the bank stones stand in the stream mouth instead of between the two.
            var start = new Vector2(R07IslandR11 ? PondMaxX - .15f : PondMaxX + .45f, lip.y);
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
                    if (R07IslandR11) Box(tree.transform, "TrunkCollision", new Vector3(0, .65f, 0), new Vector3(.42f, 1.3f, .42f));   // now within reach
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

            // 6. Cloud sea: puffs hugging the rim and a far field (one mesh), a bluish floor hiding the keels (r10:
            //    separate, darker than the puffs so the sea has depth), and towering cumulus on the horizon (r10).
            var cloudMat = IslandShaderMat("SkyCloud-r09", "LuluFarm/SkyCloud-r09");
            // O7: puffs read grey and faceted in the follow view. r11: 14x8 segments within 60 m and a lighter, warmer shade.
            if (R07IslandR11) { cloudMat.SetColor("_Lit", Hex("#FFFBF4")); cloudMat.SetColor("_Shade", Hex("#C9D6E6")); }
            var cv = new List<Vector3>(); var ct = new List<int>(); int puffs = 0;
            void Puff(Vector3 c, float size)
            {
                bool near = new Vector2(c.x, c.z).magnitude < 60;   // r11 smooths the near puffs; the far field is fogged anyway
                for (int i = 0, n = 3 + random.Next(3); i < n; i++)
                    Ellipsoid(cv, ct, c + new Vector3(Next(-1, 1) * size * .8f, Next(-.15f, .25f) * size, Next(-1, 1) * size * .8f),
                        new Vector3(size * Next(.7f, 1.1f), size * Next(.45f, .6f), size * Next(.7f, 1.1f)), .45f, near ? CloudLon : 10, near ? CloudLat : 6);
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
            var floorVerts = new List<Vector3> { new Vector3(0, -9, 0) }; var floorTris = new List<int>(); const int FloorSides = 48;
            for (int i = 0; i < FloorSides; i++) { float a = i * 2 * Mathf.PI / FloorSides; floorVerts.Add(new Vector3(Mathf.Cos(a) * 170, -9, Mathf.Sin(a) * 170)); }
            for (int i = 0; i < FloorSides; i++) floorTris.AddRange(new[] { 0, 1 + (i + 1) % FloorSides, 1 + i });
            var floorMat = IslandShaderMat("SkyCloudFloor-r10", "LuluFarm/SkyCloud-r09");
            floorMat.SetColor("_Lit", Hex(R07IslandR11 ? "#E2EDF5" : "#D3E4F1")); floorMat.SetColor("_Shade", Hex(R07IslandR11 ? "#CADBEA" : "#B4CCE2")); floorMat.SetFloat("_Drift", 0);
            NoShadows(MeshObject(root, "CloudFloor", IslandMesh("IslandCloudFloor-r10", floorVerts, floorTris, true), floorMat, false));
            // Horizon towers 86–112 m out, 13 banks of three tiers; their own long fog keeps the shape (Unity fog ends at 80 m).
            var tv = new List<Vector3>(); var tt = new List<int>();
            for (int i = 0; i < 13; i++)
            {
                float a = -Mathf.PI + i * 2 * Mathf.PI / 13 + Next(-.12f, .12f), d = Next(86, 112), h = Next(.6f, 1f);
                var c = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d; var side = new Vector2(-Mathf.Sin(a), Mathf.Cos(a));
                var tiers = new[] { (n: 5, lo: 8f, hi: 11f, y0: -4f, y1: 0f), (n: 3, lo: 6f, hi: 8.5f, y0: 5f, y1: 9f), (n: 2, lo: 4f, hi: 6f, y0: 12f, y1: 18f) };
                for (int k = 0; k < tiers.Length; k++)
                    for (int j = 0, n = k < 2 || h > .75f ? tiers[k].n : 1; j < n; j++)
                    {
                        var q = c + side * Next(-1, 1) * (16 - k * 5); float size = Next(tiers[k].lo, tiers[k].hi);
                        Ellipsoid(tv, tt, new Vector3(q.x, Next(tiers[k].y0, tiers[k].y1) * h, q.y), new Vector3(size, size * Next(.65f, .8f), size), .3f, CloudLon, CloudLat);
                    }
            }
            var towerMat = IslandShaderMat("SkyCloudTowers-r10", "LuluFarm/SkyCloud-r09");
            if (R07IslandR11) { towerMat.SetColor("_Lit", Hex("#FFFBF4")); towerMat.SetColor("_Shade", Hex("#C9D6E6")); }
            towerMat.SetFloat("_OwnFog", 1); towerMat.SetFloat("_OwnFogStart", 70); towerMat.SetFloat("_OwnFogEnd", 190); towerMat.SetColor("_OwnFogColor", Hex(IslandHorizon));
            NoShadows(MeshObject(root, "CloudTowers", IslandMesh("IslandCloudTowers-r10", tv, tt, false), towerMat, false));
            record.towerTriangles = tt.Count / 3;

            // 7. Islets at mixed heights and distances (r10): the nearer ones carry a little life and are readable from the
            //    gameplay camera; the one above eye level shows its keel. Plus four bare floating rocks.
            var islets = new (Vector2 c, float y, float s, (string id, float x, float z, float k)[] props)[] {
                (new Vector2(34, 18), -2f, .30f, new[] { ("E08", -2.5f, 1f, 1f), ("E09", 2.6f, -.4f, .9f), ("deer", .3f, .6f, 1f), ("E10", -.8f, -2.2f, 1f), ("E11", 1.4f, 2f, .8f), ("E11", -3.6f, -1f, .7f) }),
                (new Vector2(-30, 26), 7f, .26f, new[] { ("E09", 0f, .4f, 1f), ("E11", -1.6f, -1.4f, .8f), ("E10", 2f, -.8f, .9f) }),
                (new Vector2(8, -36), -4f, .22f, new[] { ("S10", -1f, .2f, 1f), ("E15", 1.6f, -.6f, 1f), ("E11", .4f, 1.6f, .8f), ("E08", 2.2f, 1.4f, .8f) }),
                (new Vector2(-38, -20), 1f, .20f, new[] { ("alpaca", .5f, .2f, 1f), ("E08", -1.8f, .6f, .85f), ("E11", 1.6f, -1.2f, .7f) }),
                (new Vector2(55, -10), 10f, .14f, new[] { ("E08", 0f, 0f, .9f) }),
                (new Vector2(-60, 40), -2f, .16f, new[] { ("E08", 0f, 0f, 1f) }),
                (new Vector2(20, 52), 4f, .15f, new[] { ("E09", 0f, 0f, 1f) }),
                (new Vector2(24, -20), 3f, .05f, new (string, float, float, float)[0]), (new Vector2(-26, -9), -1f, .06f, new (string, float, float, float)[0]),
                (new Vector2(-12, 22), 5f, .045f, new (string, float, float, float)[0]), (new Vector2(27, 4), 1.5f, .04f, new (string, float, float, float)[0]) };
            var ring = angles.Where((a, i) => i % 4 == 0).ToList();
            foreach (var (c, y, s, props) in islets)
            {
                var islet = new GameObject(props.Length > 0 ? "Islet" : "FloatingRock").transform; islet.SetParent(root, false); islet.localPosition = new Vector3(c.x, y, c.y);
                var top = new List<Vector3> { Vector3.zero }; var topTris = new List<int>();
                foreach (float a in ring) { var p = IslandPoint(a) * s; top.Add(new Vector3(p.x, 0, p.y)); }
                for (int i = 0; i < ring.Count; i++) topTris.AddRange(new[] { 0, 1 + (i + 1) % ring.Count, 1 + i });
                MeshObject(islet, "IsletTop", IslandMesh("IsletTop-r10-" + record.islets, top, topTris, true), grassMaterial, false);
                Cliff("IsletCliff-r10-" + record.islets, Vector2.zero, s, ring, strata, islet);
                foreach (var (id, x, z, k) in props)
                {
                    // Static decoration only: no colliders, not part of the pasture or any animal motion.
                    var prop = Place(id, new Vector3(x, 0, z), islet, Next(0, 360), k);
                    if (prop == null) continue;
                    if (id == "E08" || id == "E09") RetainPolishLastLod(prop);
                    foreach (var col in prop.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(col);
                    prop.name = "IsletProp_" + id; record.isletProps++;
                }
                if (props.Length > 0) for (int i = 0; i < 3; i++) Puff(new Vector3(c.x + Next(-1, 1) * 12 * s, y - 15 * s * Next(.5f, .9f), c.y + Next(-1, 1) * 9 * s), 9 * s);
                record.islets++;
            }
            var clouds = MeshObject(root, "CloudSea", IslandMesh("IslandClouds-r09", cv, ct, false), cloudMat, false);
            NoShadows(clouds); record.cloudPuffs = puffs; record.cloudTriangles = ct.Count / 3;

            // 8b. Birds (r10): four loose flocks — above the island, below the rim (seen over the edge), high up, and
            //     around the deer islet. All motion is in SkyBirds-r10; the mesh only carries per-bird orbit data.
            BuildBirds(root, random, record);

            // 8. Meadow patches in the rim band (clusters with gaps, not a hedge) and reeds either side of the cove (r10).
            foreach (float deg in new[] { -150f, -120f, -95f, -60f, -35f, 40f, 75f, 100f, 140f, 185f })
                for (int i = 0; i < 6; i++)
                {
                    float b = deg * Mathf.Deg2Rad + Next(-.05f, .05f); var p = IslandPoint(b, Next(.5f, Mathf.Max(.6f, IslandMargin(b) - .4f)));
                    var flower = Place("E11", new Vector3(p.x, 0, p.y), rim, Next(0, 360), Next(.6f, .95f));
                    if (flower != null) { foreach (var col in flower.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(col); record.meadowFlowers++; }
                }
            for (int i = 0; i < 5; i++)
            {
                float b = WaterfallAngle + (i % 2 == 1 ? .11f : -.11f) + Next(-.03f, .03f); var p = IslandPoint(b, Next(.4f, 1f));
                var reed = Place("E12", new Vector3(p.x, 0, p.y), rim, Next(0, 360), Next(.7f, .9f));
                if (reed != null) { foreach (var col in reed.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(col); record.coveReeds++; }
            }

            if (R07IslandR11) record.edgeWallSegments = BuildEdgeWalls(landscape, root, angles);

            AssetDatabase.SaveAssets();
            islandRecord = record;
        }

        static IslandRecord islandRecord;
        // Runs after Lighting() and OpusSkyR08 so the island's fog/sky values are the ones saved in the scene.
        static void OpusSkyIslandSkyR10()
        {
            var record = islandRecord ?? throw new InvalidOperationException("Sky-island sky step needs OpusSkyIslandR09 first");
            // Sky and fog (r10): a deeper zenith, and a lighter horizon shared by fog, sky and tower fog so the cloud
            //    floor meets the sky without a seam. The farm itself sits inside the 32 m fog start and is unaffected.
            RenderSettings.fogColor = Hex(IslandHorizon);
            // O7 overview read washed out: r11 starts the fog later; the cloud field still fades out before the 120 m far clip.
            if (R07IslandR11) { RenderSettings.fogStartDistance = 40; RenderSettings.fogEndDistance = 110; }
            // Warm afternoon (user-approved direction 2026-10-24): a slightly lower, more golden sun and warmer fill.
            if (RenderSettings.sun != null)
            {
                RenderSettings.sun.color = Hex("#FFE3BC"); RenderSettings.sun.intensity = 1.32f;
                RenderSettings.sun.transform.rotation = Quaternion.Euler(42, -35, 0);
                record.sunColor = RenderSettings.sun.color; record.sunIntensity = RenderSettings.sun.intensity; record.sunPitch = 42;
            }
            RenderSettings.ambientSkyColor = Hex("#BED8EE"); RenderSettings.ambientEquatorColor = Hex("#E4E2CB"); RenderSettings.ambientGroundColor = Hex("#8FA663");
            if (RenderSettings.skybox != null)
            {
                var sky = Derived("FarmSky-r10", RenderSettings.skybox, RenderSettings.skybox.shader);
                sky.SetColor("_Horizon", Hex(IslandHorizon)); sky.SetColor("_Zenith", Hex("#4C97D6")); EditorUtility.SetDirty(sky);
                RenderSettings.skybox = sky; record.skyMaterial = AssetDatabase.GetAssetPath(sky);
            }
            record.utc = DateTime.UtcNow.ToString("o");
            string dir = "Evidence/r07/" + R07Task; Directory.CreateDirectory(dir);
            File.WriteAllText(dir + (R07IslandR11 ? "/sky-island-r11.json" : "/sky-island-r10.json"), JsonUtility.ToJson(record, true));
        }

        static void BuildBirds(Transform root, System.Random random, IslandRecord record)
        {
            float Next(float lo, float hi) => lo + (float)random.NextDouble() * (hi - lo);
            var v = new List<Vector3>(); var t = new List<int>(); var uv0 = new List<Vector2>(); var uv1 = new List<Vector4>(); var uv2 = new List<Vector4>(); var uv3 = new List<Vector4>();
            // (centre x, z, radius, height, angular speed rad/s, birds)
            var flocks = new[] { (0f, 0f, 26f, 4f, .12f, 5), (0f, 0f, 32f, -4f, -.09f, 4), (0f, 0f, 40f, 9f, .07f, 3), (34f, 18f, 8f, 1f, .25f, 3) };
            foreach (var (cx, cz, radius, height, speed, count) in flocks)
            {
                float lead = Next(0, 2 * Mathf.PI);
                for (int b = 0; b < count; b++)
                {
                    var orbit = new Vector4(radius + Next(-1.5f, 1.5f), height + Next(-.8f, .8f), speed * Next(.95f, 1.05f), lead - b * Next(.04f, .09f) * Mathf.Sign(speed));
                    var centre = new Vector4(cx, cz, Next(.3f, .7f), Next(7, 9)); var size = new Vector4(R07IslandR11 ? Next(2.0f, 2.6f) : Next(1.6f, 2.2f), 0, 0, 0);   // ~1 m span: 25–30 px at 26 m in the gameplay camera
                    void Tri(Vector3 a, Vector3 c, Vector3 d, float flapA, float flapC, float flapD, float side)
                    {
                        int k = v.Count; v.AddRange(new[] { a, c, d }); t.AddRange(new[] { k, k + 1, k + 2 });
                        uv0.AddRange(new[] { new Vector2(flapA, side), new Vector2(flapC, side), new Vector2(flapD, side) });
                        for (int i = 0; i < 3; i++) { uv1.Add(orbit); uv2.Add(centre); uv3.Add(size); }
                    }
                    // Body: a small double pyramid, nose +z.
                    Vector3 nose = new Vector3(0, 0, .16f), tail = new Vector3(0, .01f, -.14f), l = new Vector3(-.04f, 0, 0), r = new Vector3(.04f, 0, 0), top = new Vector3(0, .035f, 0), bottom = new Vector3(0, -.03f, 0);
                    foreach (var (a, c) in new[] { (l, top), (top, r), (r, bottom), (bottom, l) }) { Tri(nose, a, c, 0, 0, 0, 0); Tri(tail, c, a, 0, 0, 0, 0); }
                    // Wings: inner edge stays on the body, tips flap (weight = distance / span).
                    foreach (float side in new[] { -1f, 1f })
                    {
                        Vector3 innerF = new Vector3(side * .03f, 0, .05f), innerB = new Vector3(side * .03f, 0, -.05f), midF = new Vector3(side * .15f, 0, .03f), midB = new Vector3(side * .15f, 0, -.06f), tip = new Vector3(side * .27f, 0, -.05f);
                        float W(Vector3 p) => Mathf.Abs(p.x) / .27f;
                        Tri(innerF, midF, innerB, W(innerF), W(midF), W(innerB), side); Tri(innerB, midF, midB, W(innerB), W(midF), W(midB), side); Tri(midF, tip, midB, W(midF), W(tip), W(midB), side);
                    }
                    record.birds++;
                }
            }
            var mesh = new Mesh { name = "IslandBirds-r10", indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(v); mesh.SetTriangles(t, 0); mesh.SetUVs(0, uv0); mesh.SetUVs(1, uv1); mesh.SetUVs(2, uv2); mesh.SetUVs(3, uv3);
            mesh.SetNormals(Enumerable.Repeat(Vector3.up, v.Count).ToList());
            mesh.bounds = new Bounds(Vector3.zero, new Vector3(140, 40, 140));   // positions are computed in the shader
            mesh = SaveIslandMesh(mesh);
            var birds = new GameObject("Birds", typeof(MeshFilter), typeof(MeshRenderer)); birds.transform.SetParent(root, false);
            birds.GetComponent<MeshFilter>().sharedMesh = mesh; var birdMat = IslandShaderMat("SkyBirds-r10", "LuluFarm/SkyBirds-r10");
            if (R07IslandR11) birdMat.SetColor("_Shade", Hex("#C8D2DE"));   // O7: read as small grey silhouettes
            birds.GetComponent<MeshRenderer>().sharedMaterial = birdMat;
            NoShadows(birds);
        }

        // O8 (r11): O7's rectangular invisible walls stopped Lulu 1.5–4 m short of the edge ("撞空气"). The walls now follow
        // the outline .8 m inside the rim, on Ignore Raycast so the follow camera can still swing out over the clouds.
        static int BuildEdgeWalls(Transform landscape, Transform root, List<float> angles)
        {
            foreach (var name in new[] { "NorthBoundary", "SouthBoundary", "EastBoundary", "WestBoundary" })
            { var old = landscape.Find(name); if (old != null) Object.DestroyImmediate(old.gameObject); }
            var walls = new GameObject("IslandEdgeWalls").transform; walls.SetParent(root, false);
            var ring = angles.Where((a, i) => i % 2 == 0).Select(a => IslandPoint(a, .8f)).ToList(); int count = 0;
            for (int i = 0; i < ring.Count; i++)
            {
                Vector2 a = ring[i], b = ring[(i + 1) % ring.Count]; if ((b - a).sqrMagnitude < 1e-4f) continue;
                var segment = new GameObject("EdgeWall_" + count++); segment.layer = 2; segment.transform.SetParent(walls, false);
                var mid = (a + b) * .5f; segment.transform.localPosition = new Vector3(mid.x, 1, mid.y);
                segment.transform.localRotation = Quaternion.LookRotation(new Vector3(b.x - a.x, 0, b.y - a.y));
                segment.AddComponent<BoxCollider>().size = new Vector3(.2f, 2, (b - a).magnitude + .05f);
            }
            return count;
        }
        static void OpusIslandEdgeCameraR11(FarmRuntimeBootstrap runtime)
        {
            var rig = runtime.GetComponentInChildren<FarmThirdPersonCamera>(true);
            if (rig == null) rig = Object.FindFirstObjectByType<FarmThirdPersonCamera>();
            if (rig == null) throw new InvalidOperationException("O8 needs the follow camera to exclude the island edge walls");
            rig.obstructionLayers &= ~(1 << 2); EditorUtility.SetDirty(rig);
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

        static void NoShadows(GameObject go) { var r = go.GetComponent<Renderer>(); r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; }
        static int CloudLon => R07IslandR11 ? 14 : 10;
        static int CloudLat => R07IslandR11 ? 8 : 6;
        static void Ellipsoid(List<Vector3> v, List<int> t, Vector3 c, Vector3 r, float underside = .45f, int Lon = 10, int Lat = 6)
        {
            int k = v.Count;
            for (int i = 0; i <= Lat; i++) for (int j = 0; j < Lon; j++)
            {
                float th = Mathf.PI * i / Lat, ph = 2 * Mathf.PI * j / Lon;
                // Flattened underside: clouds sit on a soft base instead of a full sphere.
                float y = Mathf.Cos(th); y = y < 0 ? y * underside : y;
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
