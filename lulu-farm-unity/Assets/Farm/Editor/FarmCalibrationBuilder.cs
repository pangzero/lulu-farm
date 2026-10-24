using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace LuluFarm.Editor
{
    public static partial class FarmProjectBuilder
    {
        const string CalibrationScene = Base + "Scenes/FarmCalibration.unity";
        [MenuItem("Farm/01c Exercise current calibration with simulated input")]
        public static void ExerciseCalibration()
        {
            if (!Application.isPlaying || SceneManager.GetActiveScene().path != CalibrationScene)
                throw new InvalidOperationException("Play FarmCalibration first. This check uses input events and does not certify manual mouse or device acceptance.");
            var runtime = UnityEngine.Object.FindFirstObjectByType<FarmRuntimeBootstrap>();
            if (runtime == null) throw new InvalidOperationException("Calibration runtime missing.");
            var playback = runtime.GetComponent<FarmRoutePlayback>();
            if (playback == null) playback = runtime.gameObject.AddComponent<FarmRoutePlayback>();
            playback.runtime = runtime;
            Vector3[] points = { new Vector3(0,0,1.4f), new Vector3(-2,0,.6f), new Vector3(-3.2f,0,2),
                new Vector3(-3.2f,0,7.5f), new Vector3(0,0,7.5f), new Vector3(3.4f,0,7.5f),
                new Vector3(3.4f,0,4.2f), new Vector3(1.7f,0,2), new Vector3(0,0,1.4f) };
            string[] labels = { "M1-front", "M1-crops", "M1-west-approach", "M1-west-back", "M1-back",
                "M1-east-back", "M1-east-side", "M1-shore-front", "M1-return" };
            playback.waypoints = points.Select((p,i) => new FarmRouteWaypoint { name=labels[i], position=p,
                screenshot=true, orbit=i==0||i==4||i==6 }).ToArray();
            playback.Begin();
        }
        const float CalibrationPondMinX = 2.6f, CalibrationPondMinZ = -2.6f;
        static float CalibrationPondMaxX => CalibrationPondMinX + 2.4f + 2 * BankRadius;
        static float CalibrationPondMaxZ => CalibrationPondMinZ + 2.4f + 2 * BankRadius;

        [Serializable] sealed class CalibrationAsset
        {
            public string id, version, source, sourceSHA256, importSHA256;
            public float worldHeight;
        }
        [Serializable] sealed class CalibrationQuality
        {
            public string utc, editor, scene, registrySHA256, generation;
            public string technical = "scene_authored_pending_engine_checks";
            public string visual = "pending_actual_viewing";
            public string userArt = "pending_user_acceptance";
            public string optimization = "authored_resource_counts_only_not_draw_cost";
            public string device = "not_tested";
            public string fullFarmAcceptance = "not_applicable_representative_calibration_only";
            public string[] issues, requiredChecks, actualScreenshots = Array.Empty<string>();
            public CalibrationAsset[] assets;
            public int authoredRenderersIncludingInactiveAndAllLods, authoredTrianglesIncludingInactiveAndAllLods;
            public int uniqueMaterials, uniqueMeshes, cropPairs;
            public float tileSize = 1.2f, groundDatum = 0, waterDatum = -.105f;
            public float perspectiveFov = 52, cameraDistance = 5.1f, pitchMinimum = 15, pitchMaximum = 55;
            public string lighting = "FarmProjectBuilder.Lighting shared with FarmWorld; no exposure/scale adjustment";
            public string pipeline = "FarmWorld shared DesktopURP/MobileURP assets";
            public string camera = "FarmRuntimeBootstrap.Attach with Cinemachine Third Person Follow; same runtime defaults";
            public string cropPairDisplay = "Three paired stage objects; use the existing HUD to switch mature/seedling. No height normalization beyond imported prefabs.";
        }

        [MenuItem("Farm/01b Build representative calibration")]
        public static void BuildRepresentativeCalibration()
        {
            RequireCurrentStamp("Evidence/import-stamp.json", "imported_pending_visual_review");
            registry = JsonUtility.FromJson<AssetRegistry>(File.ReadAllText(Base + "Data/asset-registry.json"));
            string[] ids = { "Lulu", "S01", "S05", "S05-endcap", "E01", "E08", "E05", "E05-corner",
                "cabbage-mature", "cabbage-seedling", "tomato-mature", "tomato-seedling", "corn-mature", "corn-seedling" };
            foreach (string id in ids)
            {
                if (Record(id) == null || !CanIntegrate(Record(id)) || AssetDatabase.LoadAssetAtPath<GameObject>(Base + "Prefabs/" + id + ".prefab") == null)
                    throw new InvalidOperationException("Current imported calibration prefab is unavailable: " + id);
            }
            // Read existing formal-scene materials. Do not tune shared assets for the small scene.
            grass = CalibrationMaterial("Grass");
            water = CalibrationMaterial("PondWater");
            var desktop = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Base + "Settings/DesktopURP.asset");
            var mobile = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(Base + "Settings/MobileURP.asset");
            if (desktop == null || mobile == null) throw new InvalidOperationException("Run Configure and import before calibration; shared URP settings are missing.");
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (Application.isBatchMode && Enumerable.Range(0, SceneManager.sceneCount).Any(i => SceneManager.GetSceneAt(i).isDirty))
                throw new InvalidOperationException("Refusing to replace unsaved scenes in batch calibration.");

            issues.Clear(); prefabs.Clear();
            Directory.CreateDirectory(Base + "Scenes"); Directory.CreateDirectory("Evidence");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            world = new GameObject("FarmCalibration — M1 representative gate, not complete farm").transform;
            var landscape = Group("CalibrationLandscape");
            CalibrationGround(landscape);
            CalibrationPond(landscape);
            var house = Place("S01", new Vector3(0, 0, 4.8f), Group("RepresentativeHouse"), 180);
            HouseCollision(house); FarmOcclusionSetup.Configure(house, false);
            FenceLine(Group("ThreeContinuousFenceSegments"), new Vector3(-5.4f, 0, -3.5f), 3, 0);
            var tree = Place("E08", new Vector3(5.8f, 0, 4.7f), landscape);
            Box(tree.transform, "TrunkCollision", new Vector3(0, .65f, 0), new Vector3(.42f, 1.3f, .42f));
            FarmOcclusionSetup.Configure(tree, true);
            var crops = CalibrationCrops(Group("ThreeCropPairs"));

            Lighting();
            var player = new GameObject("LuluPlayer"); player.transform.position = new Vector3(0, .05f, 1.4f);
            var orientation = new GameObject("PlayerOrientation"); orientation.transform.SetParent(player.transform, false);
            var lulu = Place("Lulu", Vector3.zero, orientation.transform);
            var cameraGO = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)); cameraGO.tag = "MainCamera";
            var camera = cameraGO.GetComponent<Camera>(); camera.fieldOfView = 52; camera.nearClipPlane = .1f; camera.farClipPlane = 90;
            camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.58f, .80f, .91f);
            cameraGO.transform.position = player.transform.position + new Vector3(0, 3.6f, -4.5f);
            cameraGO.transform.LookAt(player.transform.position + Vector3.up * .7f);
            var rt = FarmRuntimeBootstrap.Attach(player, orientation.transform, camera, new Bounds(new Vector3(0, 0, 1.5f), new Vector3(17.2f, 20, 14.2f)));
            rt.crops = crops; rt.sceneRevision = "M1-calibration-r01"; rt.assetRegistryRevision = RegistryHash();
            rt.uiFont = AssetDatabase.LoadAssetAtPath<Font>(Base + "Fonts/NotoSansCJKsc-Regular.otf");
            rt.mobilePipeline = mobile; rt.desktopPipeline = desktop;
            var clips = AssetDatabase.LoadAllAssetsAtPath(Record("Lulu").path).OfType<AnimationClip>().ToArray();
            rt.idleClip = clips.FirstOrDefault(c => c.name.Contains("Idle"));
            rt.walkClip = clips.FirstOrDefault(c => c.name.Contains("Walk"));
            rt.runClip = clips.FirstOrDefault(c => c.name.Contains("Run"));
            if (rt.idleClip == null || rt.walkClip == null || rt.runClip == null) issues.Add("Calibration needs actual imported Idle/Walk/Run clips.");
            SetupWardrobe(lulu, rt);
            // No full-farm route is attached to this smaller calibration scene.
            rt.routeMarkers = Array.Empty<FarmRouteMarker>();
            var renderers = world.GetComponentsInChildren<Renderer>(true).Concat(lulu.GetComponentsInChildren<Renderer>(true)).ToArray();
            if (renderers.Any(r => r.sharedMaterials.Any(m => m == null || m.shader == null || m.shader.name.Contains("InternalError"))))
                issues.Add("Calibration has missing or error materials.");
            if (!EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), CalibrationScene)) issues.Add("Calibration scene save failed.");
            AssetDatabase.SaveAssets();
            // This menu deliberately never assigns EditorBuildSettings.scenes or writes FarmWorld.unity.
            var meshes = world.GetComponentsInChildren<MeshFilter>(true).Select(f => f.sharedMesh)
                .Concat(lulu.GetComponentsInChildren<MeshFilter>(true).Select(f => f.sharedMesh))
                .Concat(lulu.GetComponentsInChildren<SkinnedMeshRenderer>(true).Select(r => r.sharedMesh)).Where(m => m != null).ToArray();
            var quality = new CalibrationQuality
            {
                utc = DateTime.UtcNow.ToString("o"), editor = Application.unityVersion, scene = CalibrationScene,
                registrySHA256 = RegistryHash(), generation = issues.Count == 0 ? "generated_pending_actual_viewing" : "generation_errors",
                issues = issues.ToArray(), cropPairs = crops.Length,
                authoredRenderersIncludingInactiveAndAllLods = renderers.Length,
                authoredTrianglesIncludingInactiveAndAllLods = meshes.Sum(m => m.triangles.Length / 3),
                uniqueMeshes = meshes.Distinct().Count(), uniqueMaterials = renderers.SelectMany(r => r.sharedMaterials).Where(m => m != null).Distinct().Count(),
                assets = ids.Select(id => Record(id)).Select(a => new CalibrationAsset { id = a.id, version = a.version, source = a.source,
                    sourceSHA256 = a.sourceSHA256, importSHA256 = a.importSHA256, worldHeight = a.worldHeight }).ToArray(),
                requiredChecks = new[] {
                    "Actually open and view FarmCalibration in Unity; inspect main house front, side, back, roof and door/window thickness.",
                    "Compare volumes, matte materials and color continuity with the approved B01/B02 images and farm overview under these shared settings.",
                    "Inspect Lulu stature, root/feet contact, imported Idle/Walk/Run and all-LOD wardrobe with actual movement.",
                    "Switch the three crop pairs through both stages; inspect real 1.2-unit soil holes, raised borders, thickness and shadows.",
                    "Inspect all three fence joints, tree back/crown and straight-to-corner shore/water contact from rotating third-person view.",
                    "Record actual Unity screenshots, then perform a separate uncaptured resource/performance baseline; this JSON is not visual approval.",
                    "Continue full FarmWorld checks separately; this representative scene cannot satisfy complete-farm delivery." }
            };
            File.WriteAllText("Evidence/m1-calibration-quality.json", JsonUtility.ToJson(quality, true));
            WriteStamp("Evidence/calibration-generation-status.json", quality.generation);
            if (issues.Count > 0) throw new InvalidOperationException(string.Join("\n", issues));
            Debug.Log("M1 representative scene saved. Actual viewing and user art acceptance remain pending: Evidence/m1-calibration-quality.json");
        }

        static Material CalibrationMaterial(string name)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(Base + "Materials/" + name + ".mat");
            if (material == null) throw new InvalidOperationException("Shared FarmWorld material missing: " + name);
            return material;
        }

        static FarmCropStage[] CalibrationCrops(Transform parent)
        {
            string[] species = { "cabbage", "tomato", "corn" };
            var result = new List<FarmCropStage>();
            for (int i = 0; i < species.Length; i++)
            {
                var cell = new GameObject("CalibrationPlot_" + species[i]); cell.transform.SetParent(parent, false);
                cell.transform.localPosition = new Vector3(-5.4f + i * 1.2f, 0, .6f);
                var soil = Place("E01", Vector3.zero, cell.transform);
                var lod = soil.GetComponent<LODGroup>();
                var renderers = lod != null ? lod.GetLODs()[0].renderers : soil.GetComponentsInChildren<Renderer>(true);
                foreach (var renderer in renderers.Where(r => r.name.Contains("edge rail") || r.name.Contains("corner joint")))
                { var collider = renderer.gameObject.AddComponent<BoxCollider>(); collider.center = renderer.localBounds.center; collider.size = renderer.localBounds.size; }
                Box(cell.transform, "SoilWalkSurface", new Vector3(0, -.055f, 0), new Vector3(1.2f, .1f, 1.2f));
                var stage = cell.AddComponent<FarmCropStage>(); stage.assetId = "M1-" + species[i]; stage.species = species[i];
                stage.seedling = Place(species[i] + "-seedling", Vector3.zero, cell.transform);
                stage.mature = Place(species[i] + "-mature", Vector3.zero, cell.transform);
                stage.seedlingSourceVersion = Record(species[i] + "-seedling").version;
                stage.matureSourceVersion = Record(species[i] + "-mature").version;
                stage.SetMature(true); result.Add(stage);
            }
            return result.ToArray();
        }

        static List<Vector2> CalibrationPondLoop(float expansion = 0)
        {
            float r = BankRadius + expansion;
            Vector2[] centers = { new Vector2(CalibrationPondMaxX - BankRadius, CalibrationPondMaxZ - BankRadius),
                new Vector2(CalibrationPondMinX + BankRadius, CalibrationPondMaxZ - BankRadius),
                new Vector2(CalibrationPondMinX + BankRadius, CalibrationPondMinZ + BankRadius),
                new Vector2(CalibrationPondMaxX - BankRadius, CalibrationPondMinZ + BankRadius) };
            var loop = new List<Vector2>();
            for (int c = 0; c < 4; c++) for (int i = 0; i <= 12; i++)
            { float angle = (c * 90 + i * 7.5f) * Mathf.Deg2Rad; loop.Add(centers[c] + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * r); }
            return loop;
        }

        static Vector2 CalibrationPondSpan(List<Vector2> loop, float z)
        {
            var xs = new List<float>();
            for (int i = 0; i < loop.Count; i++)
            {
                Vector2 a = loop[i], b = loop[(i + 1) % loop.Count];
                if (z < Mathf.Min(a.y, b.y) - .0001f || z > Mathf.Max(a.y, b.y) + .0001f) continue;
                if (Mathf.Abs(a.y - b.y) < .0001f) { xs.Add(a.x); xs.Add(b.x); }
                else xs.Add(Mathf.Lerp(a.x, b.x, Mathf.Clamp01((z - a.y) / (b.y - a.y))));
            }
            if (xs.Count < 2) throw new InvalidOperationException("Calibration pond band could not be measured at Z " + z);
            return new Vector2(xs.Min(), xs.Max());
        }

        static void CalibrationGround(Transform parent)
        {
            var loop = CalibrationPondLoop(.60f);
            var levels = loop.Select(p => p.y).Concat(new[] { -6f, 0f, 1.2f, 9f }).Distinct().OrderBy(z => z).ToArray();
            var vertices = new List<Vector3>(); var triangles = new List<int>();
            for (int i = 0; i < levels.Length - 1; i++)
            {
                float a = levels[i], b = levels[i + 1], mid = (a + b) * .5f;
                if (b - a < .00001f) continue;
                bool soil = mid > 0 && mid < 1.2f, pond = mid > CalibrationPondMinZ - .6f && mid < CalibrationPondMaxZ + .6f;
                float left = -9;
                if (soil) { GroundBand(vertices, triangles, a, b, left, left, -6, -6, false); left = -2.4f; }
                if (pond)
                {
                    Vector2 aa = CalibrationPondSpan(loop, a), bb = CalibrationPondSpan(loop, b);
                    GroundBand(vertices, triangles, a, b, left, left, aa.x, bb.x, false);
                    GroundBand(vertices, triangles, a, b, aa.y, bb.y, 9, 9, false);
                }
                else GroundBand(vertices, triangles, a, b, left, left, 9, 9, false);
            }
            MeshObject(parent, "CalibrationGround_RealSoilAndPondOpenings", MeshAsset("M1CalibrationGround", vertices, triangles), grass, true);
        }

        static void CalibrationPond(Transform parent)
        {
            var loop = CalibrationPondLoop();
            var vertices = new List<Vector3> { new Vector3((CalibrationPondMinX + CalibrationPondMaxX) * .5f, -.105f, (CalibrationPondMinZ + CalibrationPondMaxZ) * .5f) };
            vertices.AddRange(loop.Select(p => new Vector3(p.x, -.105f, p.y)));
            var triangles = new List<int>();
            for (int i = 0; i < loop.Count; i++) triangles.AddRange(new[] { 0, 1 + (i + 1) % loop.Count, 1 + i });
            var surface = MeshObject(parent, "CalibrationWater_ContinuousSameDatum", MeshAsset("M1CalibrationWater", vertices, triangles), water, false);
            surface.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var outer = CalibrationPondLoop(.60f); vertices.Clear(); triangles.Clear();
            for (int i = 0; i < loop.Count; i++) { vertices.Add(new Vector3(loop[i].x, -.28f, loop[i].y)); vertices.Add(new Vector3(outer[i].x, -.065f, outer[i].y)); }
            for (int i = 0; i < loop.Count; i++) { int a = i * 2, b = (i + 1) % loop.Count * 2; triangles.AddRange(new[] { a, b + 1, a + 1, a, b, b + 1 }); }
            // Same backing definition as BuildPond; the original shore meshes provide the visible art surface.
            var bank = Mat("BankBacking", new Color(.54f, .58f, .35f), .12f);
            MeshObject(parent, "CalibrationBankBacking", MeshAsset("M1CalibrationBankBacking", vertices, triangles), bank, false);
            for (int i = 0; i < loop.Count; i++) ShoreGuard(parent, "M1-" + i, loop[i], loop[(i + 1) % loop.Count]);
            for (int i = 0; i < 2; i++)
            {
                float x = CalibrationPondMinX + BankRadius + .6f + i * 1.2f;
                float z = CalibrationPondMinZ + BankRadius + .6f + i * 1.2f;
                Place("E05", new Vector3(x, 0, CalibrationPondMinZ), parent);
                Place("E05", new Vector3(x, 0, CalibrationPondMaxZ), parent, 180);
                Place("E05", new Vector3(CalibrationPondMinX, 0, z), parent, 90);
                Place("E05", new Vector3(CalibrationPondMaxX, 0, z), parent, -90);
            }
            Place("E05-corner", new Vector3(CalibrationPondMinX + BankRadius, 0, CalibrationPondMinZ + BankRadius), parent);
            Place("E05-corner", new Vector3(CalibrationPondMaxX - BankRadius, 0, CalibrationPondMinZ + BankRadius), parent, -90);
            Place("E05-corner", new Vector3(CalibrationPondMaxX - BankRadius, 0, CalibrationPondMaxZ - BankRadius), parent, 180);
            Place("E05-corner", new Vector3(CalibrationPondMinX + BankRadius, 0, CalibrationPondMaxZ - BankRadius), parent, 90);
        }
    }
}
