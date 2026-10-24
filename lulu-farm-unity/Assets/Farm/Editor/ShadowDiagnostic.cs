// Review-only source. Root may copy this file to Assets/Farm/Editor/ShadowDiagnostic.cs.
// The three variants share one frozen camera, scene, exposure, light direction and LOD policy.
// Imported materials are never edited; the normal-off variant uses temporary material clones.
// No scene or asset is saved. Every temporary change is restored even after a render failure.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace LuluFarm.Editor
{
    public static class ShadowDiagnostic
    {
        public static void RunBatch()
        {
            UnityEditor.SceneManagement.EditorSceneManager.OpenScene(Calibration);
            var camera=Camera.main;
            camera.transform.position=new Vector3(10,4.5f,.5f);
            camera.transform.LookAt(new Vector3(3.1f,1.6f,4.8f));
            camera.aspect=16f/9f;
            bool previous=EditorSettings.asyncShaderCompilation;
            EditorSettings.asyncShaderCompilation=false;
            try { Capture(camera,"fixed-side-batch"); }
            finally { EditorSettings.asyncShaderCompilation=previous; }
        }
        const string Calibration = "Assets/Farm/Scenes/FarmCalibration.unity";
        static readonly string[] ScaleProperties = { "normalTexture_scale", "_NormalScale", "_BumpScale" };

        [Serializable] sealed class MaterialRecord
        {
            public string renderer, sourcePath, name, shader, scaleProperty, texturePath;
            public float originalScale;
        }
        [Serializable] sealed class Shot
        {
            public string variant, file, sha256, shadows;
            public bool targetNormalScaleZero;
            public float shadowBias, shadowNormalBias, shadowStrength;
        }
        [Serializable] sealed class Report
        {
            public string utc, editor, scene, cameraSource, output, pipeline, quality, result, error;
            public string visual = "not_reviewed_images_must_be_opened";
            public string method = "URP SingleCameraRequest; current camera projection and pose are frozen synchronously; no exposure/light direction/geometry/LOD policy changes";
            public int width, height, frame;
            public float aspect, fieldOfView, orthographicSize, near, far, renderScale, sunIntensity;
            public bool orthographic, wasPlaying, wasPaused, originalSceneDirty, finalSceneDirty, restored;
            public Vector3 cameraPosition, cameraEuler, sunEuler;
            public Color sunColor, backgroundColor;
            public float[] projection;
            public string shadowCascades, skybox, ambientMode;
            public MaterialRecord[] targetMaterials;
            public Shot[] shots;
            public string[] limitations = {
                "Diagnostic rendering is not manual gameplay acceptance or user art approval.",
                "The normal-off variant changes S01/E08 temporary scene materials only, not the rest of the farm.",
                "The scene-view option captures its current camera pose without editor gizmos; it does not replace the runtime gameplay camera.",
                "No universal fix is selected by this script. Inspect all outputs before choosing a correction."
            };
        }
        sealed class Binding
        {
            public Renderer renderer;
            public Material[] originals, normalOff;
        }

        [MenuItem("Farm/Diagnostics/Shadow A-B — current Game camera")]
        public static void Run() { Capture(Camera.main, "current-game-camera"); }

        [MenuItem("Farm/Diagnostics/Shadow A-B — current Scene view camera")]
        public static void RunSceneView()
        {
            var view = SceneView.lastActiveSceneView;
            if (view == null) throw new InvalidOperationException("Open and frame the current calibration Scene view first.");
            Capture(view.camera, "current-scene-view-camera");
        }

        static bool TargetMaterial(Material material)
        {
            string path = AssetDatabase.GetAssetPath(material).Replace('\\', '/');
            return path.StartsWith("Assets/Farm/Art/S01/", StringComparison.Ordinal) ||
                path.StartsWith("Assets/Farm/Art/E08/", StringComparison.Ordinal);
        }

        static void Capture(Camera camera, string cameraSource)
        {
            var scene = SceneManager.GetActiveScene();
            if (scene.path != Calibration) throw new InvalidOperationException("Open the existing FarmCalibration scene; this helper never replaces a scene.");
            if (camera == null) throw new InvalidOperationException("The chosen camera is unavailable.");
            var sun = RenderSettings.sun;
            if (sun == null || sun.type != LightType.Directional) throw new InvalidOperationException("Expected the existing calibration directional sun.");
            var pipeline = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (pipeline == null) throw new InvalidOperationException("The current renderer must be URP.");
            if (sun.shadows == LightShadows.None) throw new InvalidOperationException("Baseline sun already has no shadows; restore its intended baseline first.");

            string directory = Path.Combine("Evidence", "m1-shadow-diagnostic-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + cameraSource);
            Directory.CreateDirectory(directory);
            float aspect = camera.aspect;
            int height = Math.Max(768, Mathf.CeilToInt(1536f / aspect));
            int width = Mathf.RoundToInt(height * aspect);
            var report = new Report {
                utc = DateTime.UtcNow.ToString("o"), editor = Application.unityVersion, scene = scene.path,
                cameraSource = cameraSource, output = directory, pipeline = pipeline.name,
                quality = QualitySettings.names[QualitySettings.GetQualityLevel()],
                width = width, height = height, frame = Time.frameCount, aspect = aspect,
                fieldOfView = camera.fieldOfView, orthographic = camera.orthographic, orthographicSize = camera.orthographicSize,
                near = camera.nearClipPlane, far = camera.farClipPlane, backgroundColor = camera.backgroundColor,
                cameraPosition = camera.transform.position, cameraEuler = camera.transform.eulerAngles,
                projection = Enumerable.Range(0, 16).Select(i => camera.projectionMatrix[i]).ToArray(),
                renderScale = pipeline.renderScale, sunIntensity = sun.intensity, sunColor = sun.color, sunEuler = sun.transform.eulerAngles,
                shadowCascades = pipeline.shadowCascadeCount.ToString(), ambientMode = RenderSettings.ambientMode.ToString(),
                skybox = RenderSettings.skybox != null ? AssetDatabase.GetAssetPath(RenderSettings.skybox) : "none",
                wasPlaying = Application.isPlaying, wasPaused = EditorApplication.isPaused, originalSceneDirty = scene.isDirty,
                result = "started"
            };
            var shadows = sun.shadows;
            var bindings = new List<Binding>();
            var copies = new Dictionary<Material, Material>();
            var records = new List<MaterialRecord>();
            var shots = new List<Shot>();
            try
            {
                if (Application.isPlaying) EditorApplication.isPaused = true;
                foreach (var renderer in scene.GetRootGameObjects().SelectMany(g => g.GetComponentsInChildren<Renderer>(true)))
                {
                    var originals = renderer.sharedMaterials;
                    if (!originals.Any(m => m != null && TargetMaterial(m))) continue;
                    var variants = (Material[])originals.Clone();
                    for (int i = 0; i < originals.Length; i++)
                    {
                        var source = originals[i];
                        if (source == null || !TargetMaterial(source)) continue;
                        string property = ScaleProperties.FirstOrDefault(source.HasProperty);
                        if (property == null) throw new InvalidOperationException("No supported normal strength property on " + source.name + " / " + source.shader.name);
                        if (!copies.TryGetValue(source, out var copy))
                        {
                            copy = new Material(source) { name = source.name + " [temporary normal=0 diagnostic]", hideFlags = HideFlags.HideAndDontSave };
                            copy.SetFloat(property, 0);
                            copies.Add(source, copy);
                        }
                        variants[i] = copy;
                        string textureProperty = new[] { "normalTexture", "_BumpMap", "_NormalMap" }.FirstOrDefault(source.HasProperty);
                        var texture = textureProperty != null ? source.GetTexture(textureProperty) : null;
                        records.Add(new MaterialRecord { renderer = HierarchyPath(renderer.transform), sourcePath = AssetDatabase.GetAssetPath(source),
                            name = source.name, shader = source.shader.name, scaleProperty = property, originalScale = source.GetFloat(property),
                            texturePath = texture != null ? AssetDatabase.GetAssetPath(texture) : "none" });
                    }
                    bindings.Add(new Binding { renderer = renderer, originals = originals, normalOff = variants });
                }
                if (bindings.Count == 0) throw new InvalidOperationException("No original S01/E08 scene materials found. A camera fade may be active; frame them unobstructed and retry.");
                report.targetMaterials = records.ToArray();

                shots.Add(Render(camera, sun, directory, "01-baseline", false, width, height));
                sun.shadows = LightShadows.None;
                shots.Add(Render(camera, sun, directory, "02-no-main-light-shadows", false, width, height));
                sun.shadows = shadows;
                foreach (var binding in bindings) binding.renderer.sharedMaterials = binding.normalOff;
                shots.Add(Render(camera, sun, directory, "03-shadows-normal-scale-zero", true, width, height));
                foreach (var binding in bindings) binding.renderer.sharedMaterials = binding.originals;
                shots.Add(Render(camera, sun, directory, "04-restored-baseline", false, width, height));
                report.result = "rendered_pending_actual_visual_comparison";
            }
            catch (Exception error)
            {
                report.result = "failed"; report.error = error.ToString();
                throw;
            }
            finally
            {
                sun.shadows = shadows;
                foreach (var binding in bindings) if (binding.renderer != null) binding.renderer.sharedMaterials = binding.originals;
                foreach (var copy in copies.Values) Object.DestroyImmediate(copy);
                if (Application.isPlaying) EditorApplication.isPaused = report.wasPaused;
                report.restored = sun.shadows == shadows && bindings.All(b => b.renderer != null && b.renderer.sharedMaterials.SequenceEqual(b.originals));
                report.finalSceneDirty = scene.isDirty;
                report.shots = shots.ToArray();
                File.WriteAllText(Path.Combine(directory, "settings-and-result.json"), JsonUtility.ToJson(report, true));
            }
            Debug.Log("Shadow diagnostic rendered, scene/materials restored: " + Path.GetFullPath(directory) + ". Open all four images; no visual pass was assigned.");
        }

        static Shot Render(Camera camera, Light sun, string directory, string variant, bool normalZero, int width, int height)
        {
            var target = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var active = RenderTexture.active;
            Texture2D image = null;
            try
            {
                var request = new UniversalRenderPipeline.SingleCameraRequest { destination = target };
                if (!RenderPipeline.SupportsRenderRequest(camera, request)) throw new InvalidOperationException("URP SingleCameraRequest unsupported for selected camera.");
                RenderPipeline.SubmitRenderRequest(camera, request);
                RenderTexture.active = target;
                image = new Texture2D(width, height, TextureFormat.RGB24, false, false);
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0); image.Apply(false, false);
                byte[] png = image.EncodeToPNG();
                string file = Path.Combine(directory, variant + ".png"); File.WriteAllBytes(file, png);
                string hash; using (var sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(png)).Replace("-", "").ToLowerInvariant();
                return new Shot { variant = variant, file = file, sha256 = hash, shadows = sun.shadows.ToString(),
                    targetNormalScaleZero = normalZero, shadowBias = sun.shadowBias, shadowNormalBias = sun.shadowNormalBias, shadowStrength = sun.shadowStrength };
            }
            finally
            {
                RenderTexture.active = active;
                if (image != null) Object.DestroyImmediate(image);
                RenderTexture.ReleaseTemporary(target);
            }
        }

        static string HierarchyPath(Transform transform)
        {
            string path = transform.name;
            while (transform.parent != null) { transform = transform.parent; path = transform.name + "/" + path; }
            return path;
        }
    }
}
