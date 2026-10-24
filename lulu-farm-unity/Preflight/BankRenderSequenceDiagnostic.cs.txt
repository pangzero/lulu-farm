// Copy into Assets/Farm/Editor only when Unity is idle.
// Execute LuluFarm.Editor.BankRenderSequenceDiagnostic.RunBatch.
// No ForceLOD, shadow, material, geometry or exposure change; no warm-up at the pond pose.
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
    public static class BankRenderSequenceDiagnostic
    {
        const string World = "Assets/Farm/Scenes/FarmWorld.unity";
        [Serializable] sealed class Shot
        {
            public string sequence, name, file, sha256, utc;
            public Vector3 position, target;
            public int globalSubmitInSequence, submitAtPose, engineFrameBefore, engineFrameAfter;
            public double editorTime;
        }
        [Serializable] sealed class Report
        {
            public string utc, engine, scene = World, sceneSHA256, pipeline, quality, error, folder;
            public string result = "started", visual = "not_reviewed_open_images";
            public string method = "Fresh scene each sequence. SingleCameraRequest exactly once per image, no ForceLOD calls. Three pond captures without changing pose or any scene state. Historical sequence first reproduces four preceding FarmWorldReview views, one submit each.";
            public int width = 1600, height = 900;
            public float fov = 52, near = .08f, far = 160;
            public bool asyncShaderCompilationRestored, previousSceneSetupRestored, sceneSetupRestorationApplicable;
            public string sceneSetupRestoration = "pending";
            public bool cameraEnabled = true;
            public Shot[] shots;
            public string[] limitations = {
                "This synchronous diagnostic does not advance the normal Unity player loop; engine frame counters are recorded.",
                "Image differences alone do not prove that both LOD levels were submitted. A frame debugger would be needed to confirm draw submission.",
                "Water shader time may change between calls; inspect the fixed shore turf, not whole-image hashes alone.",
                "No models or assets are changed. Fresh and historical sequences preserve exactly the same lights and automatic LOD settings."
            };
        }
        [MenuItem("Farm/Diagnostics/Bank first-versus-repeat render")]
        public static void RunBatch()
        {
            if (EditorApplication.isPlaying || EditorApplication.isCompiling)
                throw new InvalidOperationException("Run this diagnostic in idle Edit Mode.");
            for (int i = 0; i < SceneManager.sceneCount; i++)
                if (SceneManager.GetSceneAt(i).isDirty) throw new InvalidOperationException("Save or discard unsaved scene changes first.");
            var setup = EditorSceneManager.GetSceneManagerSetup();
            // Batch startup may have no loaded saved scene (or one unnamed empty placeholder).
            // RestoreSceneManagerSetup rejects that state; never pass it an invalid setup.
            bool hasSavedLoadedScene = setup.Any(s => s.isLoaded && !string.IsNullOrEmpty(s.path));
            bool canRestore = hasSavedLoadedScene && setup.Count(s => s.isActive && s.isLoaded) == 1
                && setup.All(s => !string.IsNullOrEmpty(s.path) && File.Exists(s.path));
            if (hasSavedLoadedScene && !canRestore)
                throw new InvalidOperationException("Current loaded scene setup is not safely restorable; diagnostic not started.");
            bool async = EditorSettings.asyncShaderCompilation;
            var report = new Report { utc = DateTime.UtcNow.ToString("o"), engine = Application.unityVersion,
                sceneSHA256 = Hash(File.ReadAllBytes(World)),
                pipeline = AssetDatabase.GetAssetPath(GraphicsSettings.currentRenderPipeline),
                quality = QualitySettings.names[QualitySettings.GetQualityLevel()],
                sceneSetupRestorationApplicable = canRestore,
                folder = "Evidence/bank-render-sequence-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") };
            Directory.CreateDirectory(report.folder);
            var shots = new List<Shot>();
            try
            {
                EditorSettings.asyncShaderCompilation = false;
                Sequence("fresh-pond", false, report, shots);
                Sequence("historical-camera-sequence", true, report, shots);
                report.result = "rendered_pending_actual_visual_comparison";
            }
            catch (Exception error) { report.result = "failed"; report.error = error.ToString(); throw; }
            finally
            {
                EditorSettings.asyncShaderCompilation = async;
                report.asyncShaderCompilationRestored = EditorSettings.asyncShaderCompilation == async;
                try
                {
                    if (canRestore)
                    {
                        EditorSceneManager.RestoreSceneManagerSetup(setup);
                        report.previousSceneSetupRestored = true;
                        report.sceneSetupRestoration = "restored_saved_loaded_scene_setup";
                    }
                    else
                    {
                        // Unity requires an editor scene placeholder. Discard only our diagnostic
                        // scene and return to no saved scene loaded, without saving anything.
                        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                        report.sceneSetupRestoration = "not_applicable_no_saved_loaded_scene; diagnostic_scene_closed_into_empty_unsaved_scene";
                    }
                }
                catch (Exception cleanupError)
                {
                    report.result = report.result == "failed" ? "failed_with_cleanup_error" : "rendered_but_cleanup_failed";
                    report.sceneSetupRestoration = "failed";
                    report.error += "\nScene cleanup: " + cleanupError;
                    throw;
                }
                finally { report.shots = shots.ToArray(); File.WriteAllText(Path.Combine(report.folder, "settings-and-result.json"), JsonUtility.ToJson(report, true)); }
            }
            Debug.Log("Bank render sequence: " + Path.GetFullPath(report.folder) + "; open the six pond images before reaching a conclusion.");
        }
        static void Sequence(string name, bool historical, Report report, List<Shot> shots)
        {
            EditorSceneManager.OpenScene(World, OpenSceneMode.Single);
            var go = new GameObject("TemporaryBankRenderSequenceCamera") { hideFlags = HideFlags.HideAndDontSave };
            var camera = go.AddComponent<Camera>();
            // FarmWorldReview creates an enabled camera; keep that setting too.
            camera.enabled = true; camera.clearFlags = CameraClearFlags.Skybox;
            camera.backgroundColor = new Color(.58f, .80f, .91f);
            camera.fieldOfView = report.fov; camera.nearClipPlane = report.near; camera.farClipPlane = report.far;
            camera.aspect = (float)report.width / report.height;
            int submitted = 0;
            try
            {
                if (historical)
                {
                    // Identical predecessor poses and ordering from FarmWorldReview.Render.
                    var positions = new[] { new Vector3(24,24,-30), new Vector3(0,3.65f,-1.03f), new Vector3(-5,4,-6), new Vector3(2.4f,3.65f,-10.8f) };
                    var targets = new[] { new Vector3(0,0,1), new Vector3(0,.745f,3.15f), new Vector3(-8,.5f,1.7f), new Vector3(1.2f,.7f,-2.5f) };
                    var labels = new[] { "overview", "spawn", "fields", "pasture" };
                    for (int i = 0; i < positions.Length; i++)
                        shots.Add(Submit(camera, name, "predecessor-" + labels[i], positions[i], targets[i], ++submitted, 1, report, false));
                }
                var pondPosition = new Vector3(6.2f,4,-5.1f); var pondTarget = new Vector3(11,.1f,1.7f);
                for (int i = 1; i <= 3; i++)
                    shots.Add(Submit(camera, name, "pond-" + i, pondPosition, pondTarget, ++submitted, i, report, true));
            }
            finally { Object.DestroyImmediate(go); }
        }
        static Shot Submit(Camera camera, string sequence, string name, Vector3 position, Vector3 target, int submitted, int atPose, Report report, bool save)
        {
            camera.transform.position = position; camera.transform.LookAt(target);
            var shot = new Shot { sequence = sequence, name = name, position = position, target = target,
                globalSubmitInSequence = submitted, submitAtPose = atPose, engineFrameBefore = Time.frameCount,
                utc = DateTime.UtcNow.ToString("o"), editorTime = EditorApplication.timeSinceStartup };
            var rt = RenderTexture.GetTemporary(report.width, report.height, 24, RenderTextureFormat.ARGB32);
            var old = RenderTexture.active; Texture2D image = null;
            try
            {
                var request = new UniversalRenderPipeline.SingleCameraRequest { destination = rt };
                if (!RenderPipeline.SupportsRenderRequest(camera, request)) throw new InvalidOperationException("URP SingleCameraRequest unsupported.");
                RenderPipeline.SubmitRenderRequest(camera, request); // Exactly one submission, including pond-1.
                shot.engineFrameAfter = Time.frameCount;
                if (save)
                {
                    RenderTexture.active = rt;
                    image = new Texture2D(report.width, report.height, TextureFormat.RGB24, false);
                    image.ReadPixels(new Rect(0, 0, report.width, report.height), 0, 0); image.Apply(false, false);
                    byte[] bytes = image.EncodeToPNG(); shot.file = Path.Combine(report.folder, sequence + "-" + name + ".png");
                    shot.sha256 = Hash(bytes); File.WriteAllBytes(shot.file, bytes);
                }
                return shot;
            }
            finally { RenderTexture.active = old; if (image != null) Object.DestroyImmediate(image); RenderTexture.ReleaseTemporary(rt); }
        }
        static string Hash(byte[] bytes) { using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant(); }
    }
}
