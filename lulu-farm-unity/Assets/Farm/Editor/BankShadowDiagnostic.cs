// Root may copy this into Assets/Farm/Editor when Unity is idle, then execute
// LuluFarm.Editor.BankShadowDiagnostic.RunBatch. Opens the saved FarmWorld scene.
// No source, material, prefab or scene is saved. Every temporary state is restored.
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
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    public static class BankShadowDiagnostic
    {
        const string World = "Assets/Farm/Scenes/FarmWorld.unity";
        [Serializable] sealed class RendererRecord
        {
            public string path, mesh, materials;
            public bool enabled, active, receiveShadows;
            public string castShadows;
            public Bounds bounds;
            public int vertices;
        }
        [Serializable] sealed class GroupRecord
        {
            public string path, fadeMode;
            public bool enabled, animateCrossFading;
            public float[] screenRelativeTransitions;
            public int[] rendererCounts;
        }
        [Serializable] sealed class LightRecord
        {
            public string path, type, shadows;
            public bool enabled;
            public float intensity, shadowBias, shadowNormalBias, shadowStrength;
            public Vector3 euler;
        }
        [Serializable] sealed class Shot
        {
            public string variant, file, sha256, bankReceiveShadows, lightShadows;
            public int forcedBankLOD;
            public string visual = "not_reviewed";
        }
        [Serializable] sealed class Report
        {
            public string utc, engine, scene, pipeline, quality, error, output;
            public string result = "started", visual = "not_reviewed_images_must_be_opened";
            public bool sceneStateRestored, previousSceneSetupRestored;
            public string cameraSource = "FarmWorldReview pond; same pose, projection, background, size and URP SingleCameraRequest";
            public Vector3 cameraPosition = new Vector3(6.2f, 4, -5.1f), target = new Vector3(11, .1f, 1.7f);
            public float fov = 52, near = .08f, far = 160, renderScale;
            public int width = 1600, height = 900, shadowCascades;
            public RendererRecord[] bankRenderers;
            public GroupRecord[] bankLODGroups;
            public LightRecord[] lights;
            public Shot[] shots;
            public string[] limitations = {
                "This is a controlled diagnostic, not actual gameplay or art approval.",
                "The freshly opened saved scene starts at automatic LOD. ForceLOD(-1) restores that baseline; Unity has no public forced-LOD getter.",
                "receiveShadows may be ignored by some custom shaders. All light shadows=None is the stronger realtime-shadow isolation.",
                "Lights-off does not erase baked lightmaps or baked ambient occlusion; the scene and source textures are unchanged.",
                "A saved image is not a visual check. Open every image and compare shoreline stripes before choosing a fix."
            };
        }

        [MenuItem("Farm/Diagnostics/Bank shadow and LOD comparison")]
        public static void RunBatch()
        {
            if (EditorApplication.isPlaying || EditorApplication.isCompiling)
                throw new InvalidOperationException("Run bank diagnostics in idle Edit Mode.");
            for (int i = 0; i < SceneManager.sceneCount; i++)
                if (SceneManager.GetSceneAt(i).isDirty)
                    throw new InvalidOperationException("Save or discard current scene changes before this diagnostic; it will not discard them.");
            var previousSetup = EditorSceneManager.GetSceneManagerSetup();
            var report = new Report { utc = DateTime.UtcNow.ToString("o"), engine = Application.unityVersion, scene = World };
            string folder = "Evidence/bank-shadow-diagnostic-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff");
            report.output = folder;
            Directory.CreateDirectory(folder);
            var shots = new List<Shot>();
            try
            {
                var scene = EditorSceneManager.OpenScene(World, OpenSceneMode.Single);
                Capture(scene, folder, report, shots);
                report.result = "rendered_pending_actual_visual_comparison";
            }
            catch (Exception error)
            {
                report.result = "failed"; report.error = error.ToString();
                throw;
            }
            finally
            {
                try
                {
                    EditorSceneManager.RestoreSceneManagerSetup(previousSetup);
                    report.previousSceneSetupRestored = true;
                }
                finally
                {
                    report.shots = shots.ToArray();
                    File.WriteAllText(Path.Combine(folder, "settings-and-result.json"), JsonUtility.ToJson(report, true));
                }
            }
            Debug.Log("Bank shadow diagnostic rendered; open all six images: " + Path.GetFullPath(folder));
        }

        static void Capture(Scene scene, string folder, Report report, List<Shot> shots)
        {
            var roots = scene.GetRootGameObjects();
            var groups = roots.SelectMany(r => r.GetComponentsInChildren<LODGroup>(true))
                .Where(g => g.name == "E05" || g.name == "E05-corner").ToArray();
            if (groups.Length == 0) throw new InvalidOperationException("No E05 or E05-corner LOD groups found in saved FarmWorld.");
            if (groups.Any(g => g.GetLODs().Length < 2))
                throw new InvalidOperationException("Every bank group needs LOD0 and LOD1 for this comparison.");
            var renderers = groups.SelectMany(g => g.GetComponentsInChildren<Renderer>(true)).Distinct().ToArray();
            var lights = roots.SelectMany(r => r.GetComponentsInChildren<Light>(true)).ToArray();
            var receives = renderers.ToDictionary(r => r, r => r.receiveShadows);
            var lightShadows = lights.ToDictionary(l => l, l => l.shadows);
            var pipeline = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (pipeline == null) throw new InvalidOperationException("Expected active URP asset.");
            report.pipeline = AssetDatabase.GetAssetPath(pipeline);
            report.quality = QualitySettings.names[QualitySettings.GetQualityLevel()];
            report.renderScale = pipeline.renderScale; report.shadowCascades = pipeline.shadowCascadeCount;
            report.bankRenderers = renderers.Select(r => {
                var mf = r.GetComponent<MeshFilter>(); var mesh = mf != null ? mf.sharedMesh : null;
                return new RendererRecord { path = PathOf(r.transform), mesh = mesh != null ? mesh.name : "none",
                    materials = string.Join(";", r.sharedMaterials.Select(m => m != null ? AssetDatabase.GetAssetPath(m) + ":" + m.name + "/" + m.shader.name : "missing")),
                    enabled = r.enabled, active = r.gameObject.activeInHierarchy, receiveShadows = r.receiveShadows,
                    castShadows = r.shadowCastingMode.ToString(), bounds = r.bounds, vertices = mesh != null ? mesh.vertexCount : 0 };
            }).ToArray();
            report.bankLODGroups = groups.Select(g => new GroupRecord { path = PathOf(g.transform), enabled = g.enabled,
                fadeMode = g.fadeMode.ToString(), animateCrossFading = g.animateCrossFading,
                screenRelativeTransitions = g.GetLODs().Select(l => l.screenRelativeTransitionHeight).ToArray(),
                rendererCounts = g.GetLODs().Select(l => l.renderers.Length).ToArray() }).ToArray();
            report.lights = lights.Select(l => new LightRecord { path = PathOf(l.transform), enabled = l.enabled,
                type = l.type.ToString(), shadows = l.shadows.ToString(), intensity = l.intensity,
                shadowBias = l.shadowBias, shadowNormalBias = l.shadowNormalBias, shadowStrength = l.shadowStrength,
                euler = l.transform.eulerAngles }).ToArray();

            bool async = EditorSettings.asyncShaderCompilation;
            var cameraGO = new GameObject("TemporaryBankShadowDiagnosticCamera") { hideFlags = HideFlags.HideAndDontSave };
            var camera = cameraGO.AddComponent<Camera>();
            camera.enabled = false; camera.clearFlags = CameraClearFlags.Skybox;
            camera.backgroundColor = new Color(.58f, .80f, .91f);
            camera.fieldOfView = report.fov; camera.nearClipPlane = report.near; camera.farClipPlane = report.far;
            camera.aspect = (float)report.width / report.height;
            camera.transform.position = report.cameraPosition; camera.transform.LookAt(report.target);
            Action restore = () => {
                foreach (var p in receives) if (p.Key != null) p.Key.receiveShadows = p.Value;
                foreach (var p in lightShadows) if (p.Key != null) p.Key.shadows = p.Value;
                foreach (var group in groups) if (group != null) group.ForceLOD(-1);
            };
            try
            {
                EditorSettings.asyncShaderCompilation = false;
                foreach (string variant in new[] { "01-baseline", "02-bank-receive-shadows-off", "03-bank-force-LOD0", "04-bank-force-LOD1", "05-all-light-shadows-off", "06-restored-baseline" })
                {
                    restore();
                    int forcedLOD = -1;
                    if (variant == "02-bank-receive-shadows-off") foreach (var r in renderers) r.receiveShadows = false;
                    if (variant == "03-bank-force-LOD0" || variant == "04-bank-force-LOD1")
                    {
                        forcedLOD = variant == "03-bank-force-LOD0" ? 0 : 1;
                        foreach (var group in groups) group.ForceLOD(forcedLOD);
                    }
                    if (variant == "05-all-light-shadows-off") foreach (var light in lights) light.shadows = LightShadows.None;
                    shots.Add(Render(camera, folder, variant, report.width, report.height, forcedLOD,
                        string.Join(";", renderers.Select(r => r.receiveShadows.ToString()).Distinct()),
                        string.Join(";", lights.Select(l => l.name + "=" + l.shadows))));
                }
            }
            finally
            {
                restore(); EditorSettings.asyncShaderCompilation = async;
                Object.DestroyImmediate(cameraGO);
                report.sceneStateRestored = receives.All(p => p.Key != null && p.Key.receiveShadows == p.Value)
                    && lightShadows.All(p => p.Key != null && p.Key.shadows == p.Value)
                    && EditorSettings.asyncShaderCompilation == async;
            }
        }

        static Shot Render(Camera camera, string folder, string variant, int width, int height, int forcedLOD, string receives, string shadows)
        {
            // Match FarmWorldReview RT/default colour space. Render twice so the captured frame
            // follows one camera cull/shadow update with the new LOD/shadow state.
            var rt = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32);
            var previous = RenderTexture.active; Texture2D image = null;
            try
            {
                var request = new UniversalRenderPipeline.SingleCameraRequest { destination = rt };
                if (!RenderPipeline.SupportsRenderRequest(camera, request)) throw new InvalidOperationException("URP SingleCameraRequest unsupported.");
                RenderPipeline.SubmitRenderRequest(camera, request);
                RenderPipeline.SubmitRenderRequest(camera, request);
                RenderTexture.active = rt; image = new Texture2D(width, height, TextureFormat.RGB24, false);
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply(false, false);
                byte[] bytes = image.EncodeToPNG(); string file = Path.Combine(folder, variant + ".png");
                File.WriteAllBytes(file, bytes);
                string hash; using (var sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
                return new Shot { variant = variant, file = file, sha256 = hash, forcedBankLOD = forcedLOD,
                    bankReceiveShadows = receives, lightShadows = shadows };
            }
            finally { RenderTexture.active = previous; if (image != null) Object.DestroyImmediate(image); RenderTexture.ReleaseTemporary(rt); }
        }
        static string PathOf(Transform t) => t.parent == null ? t.name : PathOf(t.parent) + "/" + t.name;
    }
}
