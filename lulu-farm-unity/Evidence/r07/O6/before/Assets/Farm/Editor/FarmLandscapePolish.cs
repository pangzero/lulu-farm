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
    public static partial class FarmProjectBuilder
    {
        [Serializable] sealed class PolishInstance
        {
            public string asset, role, representation;
            public Vector3 position;
            public float scale, yaw;
            public int residentTrianglesAllLods, peakVisibleTriangles, shadowCastingRenderers, colliders;
        }
        [Serializable] sealed class PolishBudget
        {
            public string utc, revision = "landscape-polish-r01", technical = "authored_pending_actual_Unity_render_and_walkthrough";
            public string visual = "pending_actual_viewing", device = "not_profiled";
            public int addedInstances, distantTrees, edgeProps, waterLilies, residentTrianglesAllLods, peakVisibleTrianglesSum, uniqueMeshTriangles, uniqueMeshes;
            public string farPolicy = "Only the existing last mesh LOD is retained on distant scene instances; no model/prefab source edits, no shadows, no colliders, automatic screen culling below 0.006.";
            public string fishPolicy = "No additional E16 fish: its 112582-triangle LOD1 remains a resource exception. Existing scene fish retained.";
            public string groundTextureStatus, skyMaterial;
            public string[] notes = {
                "Triangle sums are authored resource bounds, not measured visible draw cost or device performance.",
                "No exposure, sun direction, character, source model, or imported model material is changed.",
                "Border decorations are outside roads and route markers; actual rotating-camera and walking inspection remains required.",
                "The sky requires the gameplay camera clearFlags=Skybox; no extra camera is created."
            };
            public PolishInstance[] instances;
        }
        [Serializable] sealed class PolishGroundEvidence
        {
            public string utc, revision = "ground-polish-r02", technical = "authored_pending_same_camera_Unity_review";
            public string visual = "pending_actual_viewing", device = "not_profiled";
            public string originalGrass, originalRoad, derivedGrass, derivedRoad, roadMask;
            public Color grassBase, grassLow, grassHigh, roadBase;
            public int roadSegments, maskWidth = 1024, maskHeight = 512, addedInstances = 0;
            public float edgeFeather = .16f, maximumEdgeWander = .015f, fineGrainAmplitude = .008f;
            public Vector4 maskWorldRect;
            public string method = "Independent generated-surface materials; world-coordinate low-frequency pigment clouds; opaque road-to-identical-grass transition inside original road geometry. No lighting/exposure/URP/source-model changes.";
        }

        // Call once after LandscapeInstances(landscape), before saving the full scene.
        static void PolishLandscape(Transform landscape)
        {
            if (landscape == null) throw new ArgumentNullException(nameof(landscape));
            if (landscape.Find("LandscapePolish_r01") != null)
                throw new InvalidOperationException("Landscape polish already exists. Rebuild the scene instead of stacking it twice.");
            foreach (string id in new[] { "E08", "E09", "E10", "E11", "E14" })
                if (Record(id) == null || !CanIntegrate(Record(id))) throw new InvalidOperationException("Missing or excluded polish input: " + id);
            var root = new GameObject("LandscapePolish_r01").transform;
            root.SetParent(landscape, false);
            var distant = new GameObject("DistantTreeLine_NoCollision_NoShadows").transform; distant.SetParent(root, false);
            var edges = new GameObject("LowBoundaryPlanting_ClearRoutes").transform; edges.SetParent(root, false);
            var lilies = new GameObject("AdditionalWaterLilies").transform; lilies.SetParent(root, false);
            var records = new List<PolishInstance>();
            var meshSet = new HashSet<Mesh>();

            // An irregular second band beyond the +/-17 X, +/-12 Z playable boundary.
            // It leaves broad gaps rather than making an enclosing wall of large close trees.
            Vector2[] farPositions = {
                new Vector2(-24,21),new Vector2(-18,24),new Vector2(-11,22),new Vector2(-4,26),
                new Vector2(4,23),new Vector2(10,25),new Vector2(18,22),new Vector2(25,24),
                new Vector2(-22,-23),new Vector2(-15,-21),new Vector2(-7,-24),new Vector2(2,-22),new Vector2(12,-24),new Vector2(22,-21),
                new Vector2(-24,-14),new Vector2(-22,-6),new Vector2(-26,2),new Vector2(-23,10),new Vector2(-28,17),
                new Vector2(23,-16),new Vector2(25,-8),new Vector2(22,0),new Vector2(27,8),new Vector2(24,16)
            };
            for (int i = 0; i < farPositions.Length; i++)
            {
                string id = i % 6 == 3 ? "E09" : "E08";
                float scale = .68f + (i % 4) * .12f;
                var position = new Vector3(farPositions[i].x, 0, farPositions[i].y);
                var tree = Place(id, position, distant, (i * 137.5f) % 360, scale);
                if (tree == null) throw new InvalidOperationException("Could not instantiate distant " + id);
                RetainPolishLastLod(tree);
                foreach (var collider in tree.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(collider);
                foreach (var renderer in tree.GetComponentsInChildren<Renderer>(true))
                { renderer.shadowCastingMode = ShadowCastingMode.Off; renderer.receiveShadows = false; }
                records.Add(PolishRecord(tree, id, "distant_tree", "last_existing_mesh_lod_only", scale, (i * 137.5f) % 360, meshSet));
            }

            // None is placed on the main house -> field -> pasture -> pond -> back-house route.
            Vector2[] clusters = { new Vector2(-13.1f,-4.8f), new Vector2(-9.1f,-3.8f), new Vector2(-13.5f,3.5f),
                new Vector2(-7.8f,7.5f), new Vector2(7.1f,8.5f) };
            for (int i = 0; i < clusters.Length; i++)
            {
                var position = new Vector3(clusters[i].x, 0, clusters[i].y);
                float scale = .56f + (i % 3) * .08f;
                var bush = Place("E10", position, edges, i * 71, scale);
                records.Add(PolishRecord(bush, "E10", "low_edge_bush", "existing_lod_chain", scale, i * 71, meshSet));
                var flowerPosition = position + new Vector3(i % 2 == 0 ? .32f : -.31f, 0, -.25f);
                var flower = Place("E11", flowerPosition, edges, 35 + i * 59, .58f);
                records.Add(PolishRecord(flower, "E11", "edge_white_flowers", "existing_lod_chain", .58f, 35 + i * 59, meshSet));
            }
            foreach (var point in new[] { new Vector2(-1.8f,10.6f), new Vector2(15.5f,-6.8f) })
            {
                var flower = Place("E11", new Vector3(point.x, 0, point.y), edges, point.x * 11, .52f);
                records.Add(PolishRecord(flower, "E11", "edge_white_flowers", "existing_lod_chain", .52f, point.x * 11, meshSet));
            }
            // The existing boat is centred at (10.9,-1), the dock ends at X=9.7, Z=DockZ.
            // These three lilies keep clear of both footprints and the open dock entrance.
            Vector3[] lilyPositions = { new Vector3(9.8f,-.09f,3.6f), new Vector3(12.2f,-.09f,.8f), new Vector3(13.8f,-.09f,-1.1f) };
            for (int i = 0; i < lilyPositions.Length; i++)
            {
                float scale = new[] { .72f, .82f, .64f }[i];
                var lily = Place("E14", lilyPositions[i], lilies, 50 + i * 113, scale);
                records.Add(PolishRecord(lily, "E14", "water_lily", "existing_lod_chain", scale, 50 + i * 113, meshSet));
            }

            string textureStatus = R07Ground ? ConfigureGroundR03(landscape) : ConfigurePolishGroundTextures(landscape);
            string skyPath = ConfigurePolishSky();
            var budget = new PolishBudget {
                utc = DateTime.UtcNow.ToString("o"), addedInstances = records.Count, distantTrees = farPositions.Length,
                edgeProps = clusters.Length * 2 + 2, waterLilies = lilyPositions.Length,
                residentTrianglesAllLods = records.Sum(r => r.residentTrianglesAllLods), peakVisibleTrianglesSum = records.Sum(r => r.peakVisibleTriangles),
                uniqueMeshes = meshSet.Count, uniqueMeshTriangles = meshSet.Sum(PolishTriangleCount),
                groundTextureStatus = textureStatus, skyMaterial = skyPath, instances = records.ToArray()
            };
            Directory.CreateDirectory("Evidence");
            File.WriteAllText("Evidence/landscape-polish-budget.json", JsonUtility.ToJson(budget, true));
            Debug.Log("Landscape polish authored: " + records.Count + " instances, " + budget.peakVisibleTrianglesSum + " summed peak triangles (not measured visibility). Actual scene review pending.");
        }

        static void RetainPolishLastLod(GameObject instance)
        {
            var group = instance.GetComponent<LODGroup>();
            if (group == null) throw new InvalidOperationException("Distant tree needs its registered existing LOD: " + instance.name);
            var lods = group.GetLODs();
            if (lods.Length < 2) throw new InvalidOperationException("Distant tree is missing its lower LOD: " + instance.name);
            var keep = lods[lods.Length - 1].renderers.Where(r => r != null).ToArray();
            if (keep.Length == 0) throw new InvalidOperationException("Empty last tree LOD: " + instance.name);
            group.SetLODs(new[] { new LOD(.006f, keep) });
            foreach (var renderer in instance.GetComponentsInChildren<Renderer>(true).Where(r => !keep.Contains(r)))
            {
                var filter = renderer.GetComponent<MeshFilter>();
                Object.DestroyImmediate(renderer);
                if (filter != null) Object.DestroyImmediate(filter);
            }
            // Serialized single-LOD configuration survives scene reload; ForceLOD alone would not.
            foreach (var renderer in keep) { renderer.gameObject.SetActive(true); renderer.enabled = true; }
            group.RecalculateBounds();
        }

        static PolishInstance PolishRecord(GameObject instance, string id, string role, string representation, float scale, float yaw, HashSet<Mesh> meshSet)
        {
            if (instance == null) throw new InvalidOperationException("Missing polish instance " + id);
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            foreach (var renderer in renderers) { var mesh = PolishMesh(renderer); if (mesh != null) meshSet.Add(mesh); }
            var group = instance.GetComponent<LODGroup>();
            int resident = renderers.Sum(r => PolishTriangleCount(PolishMesh(r)));
            int peak = group != null ? group.GetLODs().Max(l => l.renderers.Where(r => r != null).Sum(r => PolishTriangleCount(PolishMesh(r)))) : resident;
            return new PolishInstance { asset = id, role = role, representation = representation, position = instance.transform.position,
                scale = scale, yaw = yaw, residentTrianglesAllLods = resident, peakVisibleTriangles = peak,
                shadowCastingRenderers = renderers.Count(r => r.shadowCastingMode != ShadowCastingMode.Off),
                colliders = instance.GetComponentsInChildren<Collider>(true).Length };
        }
        static Mesh PolishMesh(Renderer renderer)
        {
            if (renderer is SkinnedMeshRenderer skin) return skin.sharedMesh;
            var filter = renderer.GetComponent<MeshFilter>(); return filter != null ? filter.sharedMesh : null;
        }
        static int PolishTriangleCount(Mesh mesh)
        {
            if (mesh == null) return 0;
            int count = 0; for (int i = 0; i < mesh.subMeshCount; i++) if (mesh.GetTopology(i) == MeshTopology.Triangles) count += (int)mesh.GetIndexCount(i) / 3;
            return count;
        }

        static string ConfigurePolishGroundTextures(Transform landscape)
        {
            var targets = landscape.GetComponentsInChildren<MeshFilter>(true).Where(m => m.sharedMesh != null &&
                (m.sharedMesh.name == "GroundWithSoilAndPondOpenings" || m.sharedMesh.name == "RoadNetwork")).ToArray();
            if (targets.Length != 2) throw new InvalidOperationException("Expected exactly the generated ground and road meshes for ground polish.");
            var shader = Shader.Find("LuluFarm/FarmGround");
            if (shader == null) throw new InvalidOperationException("Import independent FarmGround.shader before building the new ground pass.");
            var road = targets.Single(t => t.sharedMesh.name == "RoadNetwork");
            Vector4 maskRect; int segmentCount;
            Texture2D mask = PolishRoadMask(road, out maskRect, out segmentCount);
            Color baseGrass = grass.GetColor("_BaseColor"), baseRoad = path.GetColor("_BaseColor");
            Color grassLow = new Color(baseGrass.r * .89f, baseGrass.g * .94f, baseGrass.b * .88f, 1);
            Color grassHigh = new Color(baseGrass.r * 1.07f, baseGrass.g * 1.035f, baseGrass.b * 1.10f, 1);
            Material groundMaterial = PolishSurfaceMaterial("Grass-polish-r02", shader, baseGrass, baseRoad, grassLow, grassHigh, mask, maskRect, false);
            Material roadMaterial = PolishSurfaceMaterial("WarmPath-polish-r02", shader, baseGrass, baseRoad, grassLow, grassHigh, mask, maskRect, true);
            targets.Single(t => t.sharedMesh.name == "GroundWithSoilAndPondOpenings").GetComponent<Renderer>().sharedMaterial = groundMaterial;
            road.GetComponent<Renderer>().sharedMaterial = roadMaterial;
            var evidence = new PolishGroundEvidence { utc = DateTime.UtcNow.ToString("o"),
                originalGrass = AssetDatabase.GetAssetPath(grass), originalRoad = AssetDatabase.GetAssetPath(path),
                derivedGrass = AssetDatabase.GetAssetPath(groundMaterial), derivedRoad = AssetDatabase.GetAssetPath(roadMaterial),
                roadMask = AssetDatabase.GetAssetPath(mask), roadSegments = segmentCount, maskWorldRect = maskRect,
                grassBase = baseGrass, grassLow = grassLow, grassHigh = grassHigh, roadBase = baseRoad };
            Directory.CreateDirectory("Evidence");
            File.WriteAllText("Evidence/ground-polish-r02.json", JsonUtility.ToJson(evidence, true));
            return "ground-polish-r02: independent world-space pigment materials plus 1024x512 road-edge mask; original Grass/WarmPath assets untouched; actual viewing pending";
        }
        static Material PolishSurfaceMaterial(string name, Shader shader, Color baseGrass, Color baseRoad,
            Color grassLow, Color grassHigh, Texture2D mask, Vector4 maskRect, bool road)
        {
            string folder = Base + "Materials/LandscapePolish"; Directory.CreateDirectory(folder);
            string file = folder + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(file);
            if (material == null) { material = new Material(shader) { name = name }; AssetDatabase.CreateAsset(material, file); }
            material.shader = shader;
            material.SetColor("_GrassBase", baseGrass); material.SetColor("_GrassLow", grassLow); material.SetColor("_GrassHigh", grassHigh);
            material.SetColor("_RoadBase", baseRoad); material.SetFloat("_RoadMode", road ? 1 : 0);
            material.SetTexture("_RoadMask", mask); material.SetVector("_RoadMaskWorldRect", maskRect);
            material.SetFloat("_Smoothness", road ? .08f : .14f);
            material.SetFloat("_FineGrain", .008f);
            material.enableInstancing = true;
            EditorUtility.SetDirty(material);
            return material;
        }
        static Texture2D PolishRoadMask(MeshFilter road, out Vector4 worldRect, out int segmentCount)
        {
            // Read the actual generated mesh, not a second hand-maintained list of routes.
            // CreatePaths currently emits four quad vertices and two 26-vertex end caps per segment.
            var vertices = road.sharedMesh.vertices;
            const int stride = 56;
            if (vertices.Length == 0 || vertices.Length % stride != 0)
                throw new InvalidOperationException("Road mesh layout changed; update mask extraction explicitly instead of painting a stale route mask.");
            var segments = new List<Vector4>();
            float minX = float.MaxValue, minZ = float.MaxValue, maxX = float.MinValue, maxZ = float.MinValue;
            foreach (var vertex in vertices)
            {
                var p = road.transform.TransformPoint(vertex);
                minX = Mathf.Min(minX, p.x); minZ = Mathf.Min(minZ, p.z); maxX = Mathf.Max(maxX, p.x); maxZ = Mathf.Max(maxZ, p.z);
            }
            for (int i = 0; i < vertices.Length; i += stride)
            {
                var a0 = road.transform.TransformPoint(vertices[i]); var b0 = road.transform.TransformPoint(vertices[i+1]);
                var b1 = road.transform.TransformPoint(vertices[i+2]); var a1 = road.transform.TransformPoint(vertices[i+3]);
                if (Mathf.Abs(Vector3.Distance(a0, a1) - 1.8f) > .002f || Mathf.Abs(Vector3.Distance(b0, b1) - 1.8f) > .002f)
                    throw new InvalidOperationException("Road width differs from the measured 1.8-unit road. Recompute edge parameters before applying the mask.");
                Vector3 a = (a0+a1)*.5f, b = (b0+b1)*.5f;
                segments.Add(new Vector4(a.x,a.z,b.x,b.z));
            }
            minX -= 1; minZ -= 1; maxX += 1; maxZ += 1;
            worldRect = new Vector4(minX, minZ, 1/(maxX-minX), 1/(maxZ-minZ)); segmentCount = segments.Count;
            const int width = 1024, height = 512;
            var image = new Texture2D(width, height, TextureFormat.RGB24, false, true);
            var pixels = new Color32[width * height];
            for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
            {
                Vector2 p = new Vector2(Mathf.Lerp(minX,maxX,(x+.5f)/width), Mathf.Lerp(minZ,maxZ,(y+.5f)/height));
                float distance = float.MaxValue;
                foreach (var segment in segments)
                {
                    Vector2 a = new Vector2(segment.x,segment.y), b = new Vector2(segment.z,segment.w), direction = b-a;
                    float along = Mathf.Clamp01(Vector2.Dot(p-a,direction)/Mathf.Max(.0001f,direction.sqrMagnitude));
                    distance = Mathf.Min(distance,Vector2.Distance(p,a+direction*along));
                }
                // Stay within the road's geometric silhouette. A slight 1.5 cm wander softens the mathematical line.
                distance += .015f*Mathf.Sin(p.x*1.7f+.6f)*Mathf.Sin(p.y*1.3f-.2f);
                float value = 1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.715f,.875f,distance));
                byte channel = (byte)Mathf.RoundToInt(value*255);
                pixels[y*width+x] = new Color32(channel,channel,channel,255);
            }
            image.SetPixels32(pixels); image.Apply(false, false);
            string folder = Base + "Materials/LandscapePolish"; Directory.CreateDirectory(folder);
            string file = folder + "/RoadEdgeMask-r02.png";
            byte[] bytes = image.EncodeToPNG(); Object.DestroyImmediate(image);
            if (!File.Exists(file) || !File.ReadAllBytes(file).SequenceEqual(bytes)) File.WriteAllBytes(file, bytes);
            AssetDatabase.ImportAsset(file, ImportAssetOptions.ForceSynchronousImport);
            var importer = (TextureImporter)AssetImporter.GetAtPath(file);
            importer.textureType = TextureImporterType.Default; importer.sRGBTexture = false;
            importer.wrapMode = TextureWrapMode.Clamp; importer.filterMode = FilterMode.Trilinear; importer.anisoLevel = 2;
            importer.mipmapEnabled = true; importer.maxTextureSize = 1024; importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(file);
        }
        static string ConfigurePolishSky()
        {
            var shader = Shader.Find("LuluFarm/FarmSky");
            if (shader == null) throw new InvalidOperationException("Import the independent FarmSky.shader before building polish.");
            string file = Base + "Materials/FarmSky-r01.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(file);
            if (material == null) { material = new Material(shader) { name = "FarmSky-r01" }; AssetDatabase.CreateAsset(material, file); }
            material.shader = shader;
            material.SetColor("_Horizon", new Color(.62f, .80f, .85f, 1));
            material.SetColor("_Zenith", new Color(.34f, .62f, .82f, 1));
            material.SetColor("_Cloud", new Color(.97f, .98f, .94f, 1));
            material.SetFloat("_CloudOpacity", .74f);
            RenderSettings.skybox = material;
            EditorUtility.SetDirty(material);
            return file;
        }
    }
}
