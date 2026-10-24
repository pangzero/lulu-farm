using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Unity.Cinemachine;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    /// <summary>Produces actual Unity technical observations and framebuffer evidence; never marks visual/user/device acceptance.</summary>
    public static class FarmAcceptanceRunner
    {
        const string Root = "Assets/Farm/";
        const int ReviewLayer = 30;
        static string output;
        static readonly List<Shot> shots = new List<Shot>();
        static readonly List<string> renderIssues = new List<string>();
        static readonly string[] Views = { "front", "side", "back", "quarter", "top" };
        static readonly Vector3[] Directions = { Vector3.forward, Vector3.right, Vector3.back, new Vector3(1, .72f, 1).normalized, Vector3.up };
        const string RouteRequest = "LuluFarm.RunSimulatedRoute";

        [InitializeOnLoadMethod]
        static void RegisterRoutePlayback()
        {
            EditorApplication.playModeStateChanged -= RoutePlayModeChanged;
            EditorApplication.playModeStateChanged += RoutePlayModeChanged;
        }

        [MenuItem("Farm/07 Play simulated-input acceptance route")]
        public static void PlayInputRoute()
        {
            if (EditorApplication.isPlaying)
            {
                var runtime = Object.FindFirstObjectByType<FarmRuntimeBootstrap>();
                if (runtime == null) throw new InvalidOperationException("Farm runtime is missing from the playing scene");
                FarmRoutePlayback.StartFor(runtime);
                return;
            }
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (!File.Exists(Root + "Scenes/FarmWorld.unity")) throw new FileNotFoundException("Build FarmWorld before running the route");
            EditorSceneManager.OpenScene(Root + "Scenes/FarmWorld.unity", OpenSceneMode.Single);
            SessionState.SetBool(RouteRequest, true);
            EditorApplication.isPlaying = true;
        }

        static void RoutePlayModeChanged(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredPlayMode && SessionState.GetBool(RouteRequest, false))
            {
                SessionState.SetBool(RouteRequest, false);
                EditorApplication.delayCall += () =>
                {
                    if (!EditorApplication.isPlaying) return;
                    var runtime = Object.FindFirstObjectByType<FarmRuntimeBootstrap>();
                    if (runtime != null) FarmRoutePlayback.StartFor(runtime);
                    else Debug.LogError("Cannot run simulated-input route: FarmRuntimeBootstrap missing");
                };
            }
            if (state == PlayModeStateChange.EnteredEditMode) SessionState.SetBool(RouteRequest, false);
        }

        [MenuItem("Farm/08 Toggle actual-frame walkthrough recording (Play Mode)")]
        public static void ToggleWalkthroughRecording()
        {
            if (!EditorApplication.isPlaying) throw new InvalidOperationException("Enter visible Play Mode before recording actual frames");
            var runtime = Object.FindFirstObjectByType<FarmRuntimeBootstrap>();
            if (runtime == null || runtime.Recorder == null) throw new InvalidOperationException("Initialized Farm runtime is missing");
            runtime.Recorder.Toggle();
        }

        [Serializable] sealed class Registry { public Entry[] assets; }
        [Serializable] sealed class Entry { public string id, name, type, species, stage, path, source, sourceSHA256, importSHA256, version; public float worldHeight; }
        [Serializable] sealed class Comparison { public string id, beforePrefab, afterPrefab; }
        [Serializable] sealed class Comparisons { public Comparison[] pairs; }
        [Serializable] sealed class TextureInfo { public string name, assetPath; public int width, height; }
        [Serializable] sealed class LodInfo { public string group; public float[] screenRelativeHeights; public long[] trianglesByLevel; }
        [Serializable] sealed class AssetCheck
        {
            public string id, version, prefab, importedPath, sourceSHA256, importSHA256;
            public string technical = "not_checked", visual = "not_viewed", userArt = "pending", device = "not_tested";
            public long triangles;
            public int renderers, distinctMeshes, materials, colliders, missingScripts;
            public Vector3 boundsCenter, boundsSize;
            public string[] animationClips, errors, warnings;
            public TextureInfo[] textures;
            public LodInfo[] lodGroups;
        }
        [Serializable] sealed class SceneCheck
        {
            public string utc, unityVersion, scene, status;
            public string scope = "static_scene_and_asset_observations_only";
            public string visual = "pending_actual_image_review", input = "not_run", device = "not_tested";
            public AssetCheck[] assets;
            public int staticColliders, cameras, luluRoots, centralHouseRoots, registeredCropStages;
            public string[] sceneErrors, sceneWarnings, groups;
        }
        [Serializable] sealed class Shot
        {
            public string id, version, variant, mode, view, layout, path, sha256;
            public string visual = "not_viewed";
            public int width, height;
            public Vector3 cameraPosition, cameraEuler, target;
            public float orthographicSize, sampledRGBRange;
        }
        [Serializable] sealed class RenderIndex
        {
            public string utc, unityVersion, status = "rendered_pending_actual_viewing";
            public string userArt = "pending", device = "not_tested";
            public Shot[] shots;
            public string[] issues;
        }
        [Serializable] sealed class Settings
        {
            public string engine, colorSpace, pipeline, mode = "fixed_asset_diagnostic_only_no_overhead_gameplay";
            public string cameraRule = "Per-asset common bounding frame for all five views; comparison pair uses union bounds. No transform normalization.";
            public string comparisonRule = "Before/after share world transform, camera, lights, background, material mode and scale.";
            public string crossEngineNote = "Unity settings are separate from B01; no cross-engine identical-exposure claim.";
            public int singleViewWidth = 768, singleViewHeight = 768, farmWidth = 1280, farmHeight = 720;
            public float gridPitch = 1.2f, soilSurface = 0, directionalIntensity = 2.2f, farmOrthographicSize = 7.05f;
            public float farmAzimuth = 45, farmElevation = 50, nearOrthographicSize = 3.1f;
            public Color background = new Color(.84f, .89f, .93f), ambient = new Color(.66f, .71f, .76f), lightColor = new Color(1f, .96f, .89f);
            public Vector3 lightEuler = new Vector3(48, -35, 0);
            public string[] views = Views;
        }

        [MenuItem("Farm/04 Acceptance - static validation")]
        public static void ValidateSceneAndAssets()
        {
            EnsureOutput();
            var entries = LoadRegistry();
            var checks = CheckAssetsSequentially(entries);
            var errors = new List<string>(); var warnings = new List<string>();
            var report = new SceneCheck { utc = DateTime.UtcNow.ToString("o"), unityVersion = Application.unityVersion,
                scene = Root + "Scenes/FarmWorld.unity", assets = checks };
            if (!File.Exists(report.scene)) errors.Add("FarmWorld scene is missing");
            else
            {
                Scene active = SceneManager.GetActiveScene();
                Scene scene = SceneManager.GetSceneByPath(report.scene);
                bool openedHere = !scene.IsValid() || !scene.isLoaded;
                if (openedHere) scene = EditorSceneManager.OpenScene(report.scene, OpenSceneMode.Additive);
                try
                {
                    var roots = scene.GetRootGameObjects();
                    var transforms = roots.SelectMany(g => g.GetComponentsInChildren<Transform>(true)).ToArray();
                    var renderers = roots.SelectMany(g => g.GetComponentsInChildren<Renderer>(true)).ToArray();
                    report.staticColliders = roots.Sum(g => g.GetComponentsInChildren<Collider>(true).Length);
                    report.cameras = roots.Sum(g => g.GetComponentsInChildren<Camera>(true).Length);
                    report.luluRoots = transforms.Count(t => t.name=="Lulu" || t.name.StartsWith("Lulu —", StringComparison.Ordinal));
                    report.centralHouseRoots = transforms.Count(t => t.name=="S01" || t.name.StartsWith("S01 —", StringComparison.Ordinal));
                    report.groups = transforms.Where(t => t.parent != null && t.parent.name.StartsWith("FarmWorld", StringComparison.Ordinal)).Select(t => t.name).ToArray();
                    foreach (string required in new[] { "HouseAndProduce", "Fields", "Pasture", "Pond", "Landscape" })
                        if (!report.groups.Contains(required)) errors.Add("Missing overview region: " + required);
                    if (report.centralHouseRoots != 1) errors.Add("Expected one S01 central house, observed " + report.centralHouseRoots);
                    if (report.luluRoots != 1) errors.Add("Expected one Lulu root, observed " + report.luluRoots);
                    if (report.staticColliders == 0) errors.Add("No scene colliders found");
                    if (report.cameras == 0) errors.Add("No scene camera found");
                    if (renderers.Any(r => r.sharedMaterials.Any(m => m == null || m.shader == null || m.shader.name.Contains("InternalError")))) errors.Add("Scene has missing/error materials");
                    if (transforms.Sum(t => GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject)) > 0) errors.Add("Scene has missing MonoBehaviour scripts");
                    var runtime = roots.SelectMany(g => g.GetComponentsInChildren<FarmRuntimeBootstrap>(true)).FirstOrDefault();
                    if (runtime == null) errors.Add("FarmRuntimeBootstrap missing");
                    else
                    {
                        if (runtime.playerRoot == null || runtime.visualRoot == null || runtime.mainCamera == null) errors.Add("Runtime player/visual/camera reference missing");
                        var rig = runtime.mainCamera != null ? runtime.mainCamera.GetComponent<FarmThirdPersonCamera>() : null;
                        if (rig == null || rig.brain == null || rig.virtualCamera == null || rig.thirdPersonFollow == null || rig.orbitTarget == null)
                            errors.Add("Serialized Cinemachine Brain / Camera / ThirdPersonFollow / orbit target missing");
                        else
                        {
                            if (rig.brain.UpdateMethod != CinemachineBrain.UpdateMethods.ManualUpdate) errors.Add("Farm camera requires one manual Brain update per frame");
                            if (rig.virtualCamera.Follow != rig.orbitTarget) errors.Add("Cinemachine tracking target is not the independent orbit target");
                            if (rig.thirdPersonFollow.AvoidObstacles.Enabled) errors.Add("Two conflicting camera obstruction solvers enabled");
                            if (rig.orbitTarget.IsChildOf(runtime.mainCamera.transform)) errors.Add("Orbit target must not inherit output camera motion");
                            if (Mathf.Abs(rig.virtualCamera.Lens.FieldOfView - 52) > .01f) warnings.Add("Cinemachine lens differs from the FOV 52 calibration");
                        }
                        if (runtime.idleClip == null || runtime.walkClip == null || runtime.runClip == null) errors.Add("A real Idle/Walk/Run clip reference is missing");
                        else if (runtime.visualRoot != null) ValidateAnimationBinding(runtime, errors, warnings);
                        if (runtime.mobilePipeline == null || runtime.desktopPipeline == null) warnings.Add("Mobile/Desktop URP pipeline is not explicitly assigned to runtime");
                        if (runtime.uiFont == null) warnings.Add("Chinese font uses OS fallback; Android glyph availability is unverified");
                        if (runtime.wardrobe == null || !runtime.wardrobe.IsConfigured) warnings.Add("Wardrobe presets not configured");
                        if (runtime.routeMarkers == null || runtime.routeMarkers.Length < 9) warnings.Add("Full route marker sequence is not configured");
                    }
                    var stages = roots.SelectMany(g => g.GetComponentsInChildren<FarmCropStage>(true)).ToArray();
                    report.registeredCropStages = stages.Length;
                    foreach (var stage in stages)
                    {
                        if (stage.seedling == null || stage.mature == null) errors.Add("Crop stage pair missing: " + stage.name);
                        else if (stage.seedling.activeSelf == stage.mature.activeSelf) errors.Add("Both/neither crop stages active: " + stage.name);
                    }
                    var represented = stages.Select(s => s.species).Distinct().ToArray();
                    foreach (string species in entries.Where(a => a.type == "crop").Select(a => a.species).Where(s => !string.IsNullOrEmpty(s)).Distinct())
                        if (!represented.Contains(species)) warnings.Add("Crop species is registered but not placed: " + species);
                    foreach (var blocker in roots.SelectMany(g => g.GetComponentsInChildren<FarmCameraOccluder>(true)))
                    {
                        if (!blocker.HasSafeFadeMaterials) errors.Add("Incomplete camera fade bindings: " + blocker.name);
                        if (blocker.occlusionColliders == null || blocker.occlusionColliders.Length == 0)
                            warnings.Add("No explicit collider ownership on camera fade: " + blocker.name);
                        var crown = blocker.transform.Find("CameraOnlyCrown");
                        if (crown != null && (crown.gameObject.layer != 28 || crown.GetComponent<SphereCollider>() == null))
                            errors.Add("Tree crown proxy must be a layer-28 SphereCollider: " + blocker.name);
                    }
                    warnings.Add("Static collider existence does not validate walkability, shoreline gaps or camera occlusion; run the real route.");
                }
                finally
                {
                    if (openedHere) EditorSceneManager.CloseScene(scene, true);
                    if (active.IsValid() && active.isLoaded) SceneManager.SetActiveScene(active);
                }
            }
            report.sceneErrors = errors.ToArray(); report.sceneWarnings = warnings.ToArray();
            report.status = errors.Count == 0 && checks.All(c => c.errors.Length == 0) ? "static_checks_pass_runtime_and_visual_pending" : "static_checks_found_errors";
            Write("static-validation.json", report);
            Debug.Log("Farm static validation written: " + output + " (" + report.status + ")");
        }

        static AssetCheck CheckAsset(Entry entry)
        {
            var result = new AssetCheck { id = entry.id, version = entry.version, prefab = Root + "Prefabs/" + entry.id + ".prefab",
                importedPath = entry.path, sourceSHA256 = entry.sourceSHA256, importSHA256 = entry.importSHA256 };
            var errors = new List<string>(); var warnings = new List<string>();
            var prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(result.prefab);
            var prefab = prefabAsset != null ? Object.Instantiate(prefabAsset) : null;
            if (prefab != null) prefab.hideFlags = HideFlags.HideAndDontSave;
            var textures = new Dictionary<int, TextureInfo>();
            try
            {
              if (prefab == null) errors.Add("Prefab missing or not imported");
              else
              {
                var renderers = prefab.GetComponentsInChildren<Renderer>(true);
                result.renderers = renderers.Length;
                if (result.renderers == 0) errors.Add("No renderers");
                var meshes = prefab.GetComponentsInChildren<MeshFilter>(true).Select(m => m.sharedMesh)
                    .Concat(prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true).Select(r => r.sharedMesh)).ToArray();
                result.distinctMeshes = meshes.Where(m => m != null).Distinct().Count();
                foreach (var mesh in meshes)
                {
                    if (mesh == null) { errors.Add("Missing mesh"); continue; }
                    if (mesh.vertexCount == 0) errors.Add("Mesh has no vertices: " + mesh.name);
                    for (int sub = 0; sub < mesh.subMeshCount; sub++)
                        if (mesh.GetTopology(sub) == MeshTopology.Triangles) result.triangles += mesh.GetIndexCount(sub) / 3;
                    if (!mesh.HasVertexAttribute(VertexAttribute.Normal)) errors.Add("Mesh has no normal attribute: " + mesh.name);
                    if (!mesh.HasVertexAttribute(VertexAttribute.TexCoord0)) warnings.Add("Mesh has no UV0: " + mesh.name);
                    if (!Finite(mesh.bounds.size)) errors.Add("Non-finite mesh bounds: " + mesh.name);
                }
                foreach (var skin in prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                    if (skin.bones == null || skin.bones.Length == 0 || skin.bones.Any(b => b == null)) errors.Add("Missing skin bone: " + skin.name);
                var mats = renderers.SelectMany(r => r.sharedMaterials).Distinct().ToArray(); result.materials = mats.Length;
                foreach (var mat in mats)
                {
                    if (mat == null || mat.shader == null || mat.shader.name.Contains("InternalError")) { errors.Add("Missing/error shader material"); continue; }
                    foreach (string prop in mat.GetTexturePropertyNames())
                    {
                        var tex = mat.GetTexture(prop); if (tex == null) continue;
                        textures[tex.GetInstanceID()] = new TextureInfo { name = tex.name, assetPath = AssetDatabase.GetAssetPath(tex), width = tex.width, height = tex.height };
                    }
                }
                result.colliders = prefab.GetComponentsInChildren<Collider>(true).Length;
                result.missingScripts = prefab.GetComponentsInChildren<Transform>(true).Sum(t => GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject));
                if (result.missingScripts > 0) errors.Add("Missing component scripts");
                if (renderers.Length > 0)
                {
                    Bounds bounds = renderers[0].bounds; foreach (var renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
                    result.boundsCenter = bounds.center; result.boundsSize = bounds.size;
                }
                result.lodGroups = prefab.GetComponentsInChildren<LODGroup>(true).Select(group =>
                {
                    var levels = group.GetLODs();
                    for (int i = 0; i < levels.Length; i++)
                    {
                        if (levels[i].renderers == null || levels[i].renderers.Any(r => r == null)) errors.Add("Null renderer in LOD " + i + ": " + group.name);
                        if (levels[i].screenRelativeTransitionHeight < 0 || levels[i].screenRelativeTransitionHeight > 1)
                            errors.Add("LOD threshold outside 0..1: " + group.name);
                        if (i > 0 && levels[i].screenRelativeTransitionHeight >= levels[i - 1].screenRelativeTransitionHeight)
                            errors.Add("LOD thresholds are not descending: " + group.name);
                    }
                    return new LodInfo { group = group.name, screenRelativeHeights = levels.Select(l => l.screenRelativeTransitionHeight).ToArray(),
                        trianglesByLevel = levels.Select(l => l.renderers == null ? 0L : l.renderers.Where(r => r != null).Sum(RendererTriangles)).ToArray() };
                }).ToArray();
                if (result.lodGroups.Length == 0 && entry.type != "reused") warnings.Add("No LODGroup; quality lodBias alone does not reduce this asset's geometry");
              }
              result.animationClips = string.IsNullOrEmpty(entry.path) ? Array.Empty<string>() : AssetDatabase.LoadAllAssetsAtPath(entry.path)
                .OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__", StringComparison.Ordinal)).Select(c => c.name).ToArray();
              result.textures = textures.Values.ToArray(); result.errors = errors.ToArray(); result.warnings = warnings.ToArray();
              result.technical = errors.Count == 0 ? "static_import_attributes_pass_runtime_pending" : "static_import_errors";
              return result;
            }
            finally { if (prefab != null) Object.DestroyImmediate(prefab); }
        }

        static AssetCheck[] CheckAssetsSequentially(Entry[] entries)
        {
            var results = new List<AssetCheck>();
            for (int i = 0; i < entries.Length; i++)
            {
                // CheckAsset returns only serializable values and always destroys its transient instance.
                // Unload after leaving its frame so source meshes/textures are not retained by a batch of checks.
                try { results.Add(CheckAsset(entries[i])); }
                finally { if ((i + 1) % 4 == 0 || i == entries.Length - 1) EditorUtility.UnloadUnusedAssetsImmediate(); }
            }
            return results.ToArray();
        }

        [MenuItem("Farm/05 Acceptance - render fixed review")]
        public static void RenderFixedReview()
        {
            EnsureOutput(); shots.Clear(); renderIssues.Clear();
            var entries = LoadRegistry();
            var pairPath = Root + "Data/acceptance-comparisons.json";
            var pairs = File.Exists(pairPath) ? JsonUtility.FromJson<Comparisons>(File.ReadAllText(pairPath)).pairs ?? Array.Empty<Comparison>() : Array.Empty<Comparison>();
            var settings = new Settings { engine = Application.unityVersion, colorSpace = QualitySettings.activeColorSpace.ToString(),
                pipeline = GraphicsSettings.currentRenderPipeline != null ? GraphicsSettings.currentRenderPipeline.name : "none" };
            Write("review-settings.json", settings);
            Scene previousScene = SceneManager.GetActiveScene();
            var previousLights = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).Where(l => l.enabled).ToArray();
            foreach (var light in previousLights) light.enabled = false;
            Scene reviewScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            SceneManager.SetActiveScene(reviewScene);
            Material gray = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            // Gray is between assignments during per-asset cleanup; a C# stack local is not an asset root.
            gray.hideFlags = HideFlags.DontUnloadUnusedAsset;
            gray.SetColor("_BaseColor", new Color(.52f, .52f, .52f)); gray.SetFloat("_Smoothness", .08f); gray.SetFloat("_Metallic", 0);
            Material groundMaterial = new Material(gray); groundMaterial.SetColor("_BaseColor", new Color(.80f, .82f, .76f));
            try
            {
                RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = settings.ambient;
                RenderSettings.fog = false; RenderSettings.skybox = null;
                var sun = new GameObject("FixedReviewSun", typeof(Light)).GetComponent<Light>(); sun.type = LightType.Directional;
                sun.transform.eulerAngles = settings.lightEuler; sun.intensity = settings.directionalIntensity; sun.color = settings.lightColor;
                sun.shadows = LightShadows.Soft; sun.cullingMask = 1 << ReviewLayer;
                var camera = new GameObject("FixedReviewCamera", typeof(Camera)).GetComponent<Camera>();
                camera.enabled = false; camera.orthographic = true; camera.nearClipPlane = .03f; camera.farClipPlane = 120;
                camera.cullingMask = 1 << ReviewLayer; camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = settings.background;
                camera.allowHDR = false; camera.allowMSAA = false;
                var data = camera.GetUniversalAdditionalCameraData(); data.renderPostProcessing = false; data.antialiasing = AntialiasingMode.None;
                var ground = GameObject.CreatePrimitive(PrimitiveType.Plane); ground.name = "ReviewGround"; ground.layer = ReviewLayer;
                ground.transform.position = new Vector3(0, -.015f, 0); ground.transform.localScale = new Vector3(8, 1, 8);
                ground.GetComponent<Renderer>().sharedMaterial = groundMaterial; Object.DestroyImmediate(ground.GetComponent<Collider>());
                foreach (var entry in entries)
                {
                    var pair = pairs.FirstOrDefault(p => p.id == entry.id);
                    string candidatePath = pair != null && !string.IsNullOrEmpty(pair.afterPrefab) ? pair.afterPrefab : Root + "Prefabs/" + entry.id + ".prefab";
                    var candidate = InstantiateReview(candidatePath);
                    if (candidate == null) { renderIssues.Add(entry.id + ": candidate prefab missing"); EditorUtility.UnloadUnusedAssetsImmediate(); continue; }
                    try
                    {
                        Bounds sharedBounds = BoundsOf(candidate);
                        GameObject before = null;
                        if (pair != null && !string.IsNullOrEmpty(pair.beforePrefab))
                        {
                            before = InstantiateReview(pair.beforePrefab);
                            if (before != null) { sharedBounds.Encapsulate(BoundsOf(before)); before.SetActive(false); }
                            else renderIssues.Add(entry.id + ": configured before prefab missing");
                        }
                        else renderIssues.Add(entry.id + ": before/after comparison missing; candidate-only views are not a comparison");
                        try
                        {
                            RenderLodVariants(camera, candidate, entry, "candidate", sharedBounds, gray);
                            if (before != null)
                            {
                                candidate.SetActive(false); before.SetActive(true);
                                RenderLodVariants(camera, before, entry, "before", sharedBounds, gray);
                            }
                        }
                        finally { if (before != null) Object.DestroyImmediate(before); }
                    }
                    catch (Exception error) { renderIssues.Add(entry.id + ": render error: " + error); }
                    finally
                    {
                        Object.DestroyImmediate(candidate); candidate = null;
                        // Both before/candidate instances and every readback image are disposed at this point.
                        EditorUtility.UnloadUnusedAssetsImmediate();
                    }
                }
                foreach (var entry in entries.Where(e => e.type == "crop" && (e.stage == "mature" || e.stage == "seedling")))
                {
                    RenderPlanting(camera, entry, false);
                    RenderPlanting(camera, entry, true);
                    EditorUtility.UnloadUnusedAssetsImmediate();
                }
                // Save an inspectable calibration rig and a representative subject, never replacing FarmWorld.
                var representative = entries.FirstOrDefault(e => e.id == "cabbage-mature") ?? entries.FirstOrDefault();
                if (representative != null)
                {
                    var sample = InstantiateReview(Root + "Prefabs/" + representative.id + ".prefab");
                    if (sample != null) SetCamera(camera, BoundsOf(sample), Directions[3]);
                }
                string groundPath = Root + "Materials/AcceptanceGround.mat";
                var persistedGround = AssetDatabase.LoadAssetAtPath<Material>(groundPath);
                if (persistedGround == null) { persistedGround = new Material(groundMaterial); AssetDatabase.CreateAsset(persistedGround, groundPath); }
                ground.GetComponent<Renderer>().sharedMaterial = persistedGround;
                camera.enabled = true;
                EditorSceneManager.SaveScene(reviewScene, Root + "Scenes/AssetCalibration.unity");
            }
            finally
            {
                EditorSceneManager.CloseScene(reviewScene, true);
                if (previousScene.IsValid() && previousScene.isLoaded) SceneManager.SetActiveScene(previousScene);
                foreach (var light in previousLights) if (light != null) light.enabled = true;
                Object.DestroyImmediate(gray); Object.DestroyImmediate(groundMaterial);
                Write("screenshot-index.json", new RenderIndex { utc = DateTime.UtcNow.ToString("o"), unityVersion = Application.unityVersion,
                    shots = shots.ToArray(), issues = renderIssues.ToArray(), status = shots.Count > 0 ? "images_written_actual_viewing_and_missing_evidence_pending" : "no_images_rendered" });
                Write("metrics.json", new Metrics { utc = DateTime.UtcNow.ToString("o"), assets = CheckAssetsSequentially(entries) });
                AssetDatabase.SaveAssets();
            }
            Debug.Log("Farm fixed review evidence: " + output + "; images " + shots.Count + "; issues " + renderIssues.Count);
        }

        [Serializable] sealed class Metrics { public string utc; public AssetCheck[] assets; }
        [MenuItem("Farm/06 Acceptance - run static and fixed review")]
        public static void RunAll() { output = null; ValidateSceneAndAssets(); RenderFixedReview(); }

        static void RenderFive(Camera camera, GameObject subject, Entry entry, string variant, Bounds bounds, Material gray)
        {
            var renderers = subject.GetComponentsInChildren<Renderer>(true);
            var originals = renderers.Select(r => r.sharedMaterials).ToArray();
            try
            {
                foreach (string mode in new[] { "material", "clay" })
                {
                    for (int i = 0; i < renderers.Length; i++)
                        renderers[i].sharedMaterials = mode == "clay" ? originals[i].Select(_ => gray).ToArray() : originals[i];
                    for (int view = 0; view < Views.Length; view++)
                    {
                        SetCamera(camera, bounds, Directions[view]);
                        Capture(camera, entry, variant, mode, Views[view], "single", 768, 768, bounds.center);
                    }
                }
            }
            finally { for (int i = 0; i < renderers.Length; i++) if (renderers[i] != null) renderers[i].sharedMaterials = originals[i]; }
        }

        static void RenderLodVariants(Camera camera, GameObject subject, Entry entry, string variant, Bounds bounds, Material gray)
        {
            var groups = subject.GetComponentsInChildren<LODGroup>(true);
            int levels = groups.Length == 0 ? 1 : groups.Max(g => g.lodCount);
            try
            {
                for (int level = 0; level < levels; level++)
                {
                    foreach (var group in groups) group.ForceLOD(Mathf.Min(level, group.lodCount - 1));
                    RenderFive(camera, subject, entry, levels == 1 ? variant : variant + "-lod" + level, bounds, gray);
                }
            }
            finally { foreach (var group in groups) group.ForceLOD(-1); }
        }

        static long RendererTriangles(Renderer renderer)
        {
            Mesh mesh = renderer is SkinnedMeshRenderer skin ? skin.sharedMesh : renderer.GetComponent<MeshFilter>()?.sharedMesh;
            if (mesh == null) return 0;
            long count = 0;
            for (int i = 0; i < mesh.subMeshCount; i++) if (mesh.GetTopology(i) == MeshTopology.Triangles) count += mesh.GetIndexCount(i) / 3;
            return count;
        }

        static void ValidateAnimationBinding(FarmRuntimeBootstrap runtime, List<string> errors, List<string> warnings)
        {
            var animator = runtime.visualRoot.GetComponentInChildren<Animator>(true);
            var legacy = runtime.visualRoot.GetComponentInChildren<Animation>(true);
            Transform bindingRoot = animator != null ? animator.transform : legacy != null ? legacy.transform : null;
            if (bindingRoot == null) { errors.Add("Imported Lulu has no Animator/Animation binding root; adding one at PlayerOrientation would break clip paths"); return; }
            var clips = new[] { runtime.idleClip, runtime.walkClip, runtime.runClip };
            if (clips.Any(c => c.legacy) && clips.Any(c => !c.legacy)) errors.Add("Mixed Legacy/Generic locomotion clips");
            foreach (var clip in clips)
            {
                var bindings = AnimationUtility.GetCurveBindings(clip);
                if (bindings.Length == 0) errors.Add("Locomotion clip has no imported curves: " + clip.name);
                foreach (string path in bindings.Select(b => b.path).Distinct())
                    if (!string.IsNullOrEmpty(path) && bindingRoot.Find(path) == null) errors.Add("Animation binding path missing (" + clip.name + "): " + path);
                if (clip.length <= 0) errors.Add("Zero-length locomotion clip: " + clip.name);
            }
            warnings.Add("Animation curve paths checked; shoulder/hip deformation, stride and transitions still require actual playback.");
        }

        static void RenderPlanting(Camera camera, Entry entry, bool farm)
        {
            var container = new GameObject(entry.id + (farm ? "_farm" : "_3x3"));
            try
            {
                int cols = farm ? 12 : 3, rows = farm ? 8 : 3;
                for (int x = 0; x < cols; x++) for (int z = 0; z < rows; z++)
                {
                    var soil = InstantiateReview(Root + "Prefabs/E01.prefab");
                    if (soil == null) throw new Exception("E01 soil prefab missing");
                    soil.transform.SetParent(container.transform); soil.transform.position = new Vector3((x - (cols - 1) * .5f) * 1.2f, 0, (z - (rows - 1) * .5f) * 1.2f);
                }
                // Identical 3x3 crop population at two fixed observation distances, without height normalization.
                for (int x = 0; x < 3; x++) for (int z = 0; z < 3; z++)
                {
                    var crop = InstantiateReview(Root + "Prefabs/" + entry.id + ".prefab");
                    if (crop == null) throw new Exception("Crop prefab missing");
                    float centerOffset = farm ? .6f : 0f;
                    crop.transform.SetParent(container.transform); crop.transform.position = new Vector3((x - 1) * 1.2f + centerOffset, 0, (z - 1) * 1.2f + centerOffset);
                }
                var lulu = InstantiateReview(Root + "Prefabs/Lulu.prefab");
                if (lulu == null) throw new Exception("Read-only Lulu scale instance missing");
                lulu.transform.SetParent(container.transform); lulu.transform.position = new Vector3(2.5f, 0, 0);
                Vector3 target = farm ? Vector3.zero : new Vector3(.45f, .5f, 0);
                float elevation = 50 * Mathf.Deg2Rad;
                Vector3 direction = farm
                    ? new Vector3(-Mathf.Cos(elevation) / Mathf.Sqrt(2), Mathf.Sin(elevation), Mathf.Cos(elevation) / Mathf.Sqrt(2))
                    : new Vector3(-1.35f, 2.25f, 4).normalized;
                camera.transform.position = target + direction * 30; camera.transform.LookAt(target, Vector3.up);
                camera.orthographicSize = farm ? 7.05f : 3.1f;
                Capture(camera, entry, "candidate", "material", "quarter", farm ? "farm_12x8_with_3x3_planting" : "planting_3x3", farm ? 1280 : 768, farm ? 720 : 768, target);
            }
            catch (Exception error) { renderIssues.Add(entry.id + ": planting evidence missing: " + error.Message); }
            finally { Object.DestroyImmediate(container); }
        }

        static void Capture(Camera camera, Entry entry, string variant, string mode, string view, string layout, int width, int height, Vector3 target)
        {
            string relative = Path.Combine(entry.id, variant + "-" + mode + "-" + layout + "-" + view + ".png");
            string destination = Path.Combine(output, relative); Directory.CreateDirectory(Path.GetDirectoryName(destination));
            var texture = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var previous = RenderTexture.active;
            Texture2D image = null;
            try
            {
                camera.aspect = (float)width / height;
                var request = new UniversalRenderPipeline.SingleCameraRequest { destination = texture };
                if (!RenderPipeline.SupportsRenderRequest(camera, request)) throw new InvalidOperationException("Current pipeline does not support the URP single-camera render request");
                RenderPipeline.SubmitRenderRequest(camera, request);
                RenderTexture.active = texture;
                image = new Texture2D(width, height, TextureFormat.RGB24, false, false);
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply(false, false);
                byte[] png = image.EncodeToPNG(); File.WriteAllBytes(destination, png);
                var pixels = image.GetPixels32(); byte low = 255, high = 0;
                for (int i = 0; i < pixels.Length; i += 101)
                { low = Math.Min(low, Math.Min(pixels[i].r, Math.Min(pixels[i].g, pixels[i].b))); high = Math.Max(high, Math.Max(pixels[i].r, Math.Max(pixels[i].g, pixels[i].b))); }
                if (high - low < 3) renderIssues.Add(relative + ": near-uniform image; actual viewing required");
                string hash; using (var sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(png)).Replace("-", "").ToLowerInvariant();
                shots.Add(new Shot { id = entry.id, version = entry.version, variant = variant, mode = mode, view = view, layout = layout,
                    path = destination, sha256 = hash, width = width, height = height, cameraPosition = camera.transform.position,
                    cameraEuler = camera.transform.eulerAngles, target = target, orthographicSize = camera.orthographicSize, sampledRGBRange = (high - low) / 255f });
            }
            finally { RenderTexture.active = previous; RenderTexture.ReleaseTemporary(texture); if (image != null) Object.DestroyImmediate(image); }
        }

        static void SetCamera(Camera camera, Bounds bounds, Vector3 direction)
        {
            float extent = Mathf.Max(.15f, Mathf.Max(bounds.size.x, Mathf.Max(bounds.size.y, bounds.size.z)));
            camera.orthographicSize = extent * .76f;
            camera.transform.position = bounds.center + direction * Mathf.Max(8, extent * 3);
            camera.transform.LookAt(bounds.center, direction == Vector3.up ? Vector3.forward : Vector3.up);
        }
        static GameObject InstantiateReview(string path)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path); if (prefab == null) return null;
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            instance.transform.position = Vector3.zero; instance.transform.rotation = Quaternion.identity;
            foreach (var t in instance.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = ReviewLayer;
            foreach (var a in instance.GetComponentsInChildren<Animator>(true)) a.enabled = false;
            foreach (var a in instance.GetComponentsInChildren<Animation>(true)) a.enabled = false;
            return instance;
        }
        static Bounds BoundsOf(GameObject instance)
        {
            var renderers = instance.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0) return new Bounds(instance.transform.position, Vector3.one);
            Bounds bounds = renderers[0].bounds; foreach (var renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds); return bounds;
        }
        static bool Finite(Vector3 value) => !float.IsNaN(value.x) && !float.IsInfinity(value.x) && !float.IsNaN(value.y) && !float.IsInfinity(value.y) && !float.IsNaN(value.z) && !float.IsInfinity(value.z);
        static Entry[] LoadRegistry()
        {
            string location = Root + "Data/asset-registry.json";
            if (!File.Exists(location)) throw new FileNotFoundException("Generate the asset registry first", location);
            return JsonUtility.FromJson<Registry>(File.ReadAllText(location)).assets ?? Array.Empty<Entry>();
        }
        static void EnsureOutput()
        {
            if (string.IsNullOrEmpty(output)) output = Path.GetFullPath(Path.Combine("Evidence", "acceptance", DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff")));
            Directory.CreateDirectory(output);
        }
        static void Write(string name, object data) { File.WriteAllText(Path.Combine(output, name), JsonUtility.ToJson(data, true)); }
    }
}
