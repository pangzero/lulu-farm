using System;
using System.Collections;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace LuluFarm
{
    /// <summary>Records real, completed player frames. It never advances simulation time or generates replacement frames.</summary>
    public sealed class FarmFrameRecorder : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        [Range(1, 30)] public int requestedFramesPerSecond = 10;
        public float maximumSeconds = 600;
        public long maximumBytes = 1073741824;
        public bool IsRecording { get; private set; }
        public int WrittenFrames { get; private set; }
        public string OutputDirectory { get; private set; }
        public string Status { get; private set; } = "not_started";
        StreamWriter frameIndex, concat;
        float startedAt, previousTime;
        string previousFile;
        long writtenBytes;
        int captureWidth, captureHeight;

        [Serializable] sealed class Frame
        {
            public int index, unityFrame, width, height;
            public float elapsedSeconds;
            public string file, sha256, motion, inputSource, inputAutomation, quality;
            public Vector3 playerPosition, cameraPosition;
            public float yaw, pitch, distance;
        }
        [Serializable] sealed class Summary
        {
            public string utc, status, engine, platform, sceneRevision, assetRegistryRevision;
            public string source = "actual_Unity_ScreenCapture_framebuffer_after_WaitForEndOfFrame";
            public string timing = "wall_clock_variable_frame_durations_no_Time_captureFramerate_no_synthetic_interpolation";
            public string performance = "capture_overhead_present_not_a_device_performance_run";
            public string manualReview = "not_automatically_verified";
            public int frames, requestedFramesPerSecond, width, height;
            public float elapsedSeconds;
            public long pngBytes;
        }

        void Update()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && Keyboard.current.f9Key.wasPressedThisFrame) Toggle();
#elif ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKeyDown(KeyCode.F9)) Toggle();
#endif
        }

        public void Toggle() { if (IsRecording) StopRecording("stopped_by_operator"); else BeginRecording(); }

        public void BeginRecording()
        {
            if (IsRecording || runtime == null || !runtime.Initialized || runtime.Diagnostics == null) return;
            if (Application.isBatchMode)
            { Status = "unavailable_in_batchmode_requires_visible_playmode_or_player"; Debug.LogWarning(Status); return; }
            string session = runtime.Diagnostics.OutputDirectory;
            if (string.IsNullOrEmpty(session)) { Status = "evidence_directory_unavailable"; return; }
            try
            {
                OutputDirectory = Path.Combine(session, "walkthrough-" + DateTime.UtcNow.ToString("HHmmss-fff"));
                Directory.CreateDirectory(OutputDirectory);
                frameIndex = new StreamWriter(Path.Combine(OutputDirectory, "frames.jsonl"), false);
                concat = new StreamWriter(Path.Combine(OutputDirectory, "frames.ffconcat"), false, new UTF8Encoding(false));
                concat.WriteLine("ffconcat version 1.0");
                File.WriteAllText(Path.Combine(OutputDirectory, "ENCODE.txt"),
                    "Run from this directory after recording stops:\n" +
                    "ffmpeg -f concat -safe 0 -i frames.ffconcat -fps_mode vfr -c:v libx264 -pix_fmt yuv420p walkthrough.mp4\n\n" +
                    "The PNGs are actual Unity framebuffer captures. Variable frame durations preserve observed wall-clock timing.\n" +
                    "No fixed simulation clock, interpolated frames, or generated scenery is used.\n" +
                    "Capture and PNG encoding distort timing. Start a separate player session without frame/screenshot capture for device performance.\n" +
                    "frames.jsonl records whether route input was automated. Video alone does not prove manual UI review.\n");
                WrittenFrames = 0; writtenBytes = 0; previousFile = null;
                captureWidth = Screen.width; captureHeight = Screen.height;
                startedAt = Time.realtimeSinceStartup;
                Status = "recording_actual_frames";
                IsRecording = true;
                runtime.Diagnostics.NotifyCaptureOverhead("frame_sequence_started");
                runtime.Diagnostics.RecordEvent("frame_sequence_started_" + Path.GetFileName(OutputDirectory));
                WriteSummary();
                StartCoroutine(CaptureLoop());
            }
            catch (Exception error) { StopRecording("capture_error_" + error.Message); }
        }

        IEnumerator CaptureLoop()
        {
            var frameEnd = new WaitForEndOfFrame();
            float nextFrame = Time.realtimeSinceStartup;
            while (IsRecording)
            {
                while (IsRecording && Time.realtimeSinceStartup < nextFrame) yield return null;
                if (!IsRecording) yield break;
                yield return frameEnd;
                if (!IsRecording) yield break;
                if (Screen.width != captureWidth || Screen.height != captureHeight)
                { StopRecording("stopped_on_resolution_change_start_new_sequence"); yield break; }
                runtime.Diagnostics.NotifyCaptureOverhead("frame_sequence_capture");
                Texture2D image = null;
                try
                {
                    float elapsed = Time.realtimeSinceStartup - startedAt;
                    image = ScreenCapture.CaptureScreenshotAsTexture();
                    byte[] png = image.EncodeToPNG();
                    string filename = string.Format("frame-{0:D6}.png", WrittenFrames);
                    File.WriteAllBytes(Path.Combine(OutputDirectory, filename), png);
                    if (previousFile != null)
                    {
                        concat.WriteLine("file '" + previousFile + "'");
                        concat.WriteLine("duration " + Mathf.Max(.001f, elapsed - previousTime).ToString("F6", System.Globalization.CultureInfo.InvariantCulture));
                    }
                    var route = runtime.GetComponent<FarmRoutePlayback>();
                    string hash;
                    using (var sha = SHA256.Create()) hash = BitConverter.ToString(sha.ComputeHash(png)).Replace("-", "").ToLowerInvariant();
                    frameIndex.WriteLine(JsonUtility.ToJson(new Frame
                    {
                        index = WrittenFrames, unityFrame = Time.frameCount, width = image.width, height = image.height,
                        elapsedSeconds = elapsed, file = filename, sha256 = hash,
                        playerPosition = runtime.playerRoot.transform.position, cameraPosition = runtime.mainCamera.transform.position,
                        yaw = runtime.CameraRig.Yaw, pitch = runtime.CameraRig.Pitch, distance = runtime.CameraRig.ActualDistance,
                        motion = runtime.Player.animationBridge.CurrentMotion, inputSource = runtime.Input.ActiveInputSource,
                        inputAutomation = route != null ? route.Status : "none", quality = runtime.QualityLabel
                    }));
                    previousFile = filename; previousTime = elapsed;
                    WrittenFrames++; writtenBytes += png.LongLength;
                    if (WrittenFrames % 10 == 0) { frameIndex.Flush(); concat.Flush(); WriteSummary(); }
                    if (elapsed >= maximumSeconds || writtenBytes >= maximumBytes) StopRecording("stopped_at_recording_limit");
                }
                catch (Exception error) { StopRecording("capture_error_" + error.Message); }
                finally { if (image != null) Destroy(image); }
                // Never synthesize catch-up frames if rendering/PNG compression cannot meet the requested rate.
                nextFrame = Time.realtimeSinceStartup + 1f / Mathf.Max(1, requestedFramesPerSecond);
            }
        }

        public void StopRecording(string reason = "stopped_by_operator")
        {
            bool wasRecording = IsRecording;
            IsRecording = false; Status = reason;
            try
            {
                if (concat != null && previousFile != null)
                {
                    concat.WriteLine("file '" + previousFile + "'");
                    concat.WriteLine("duration " + (1f / Mathf.Max(1, requestedFramesPerSecond)).ToString("F6", System.Globalization.CultureInfo.InvariantCulture));
                    // ffmpeg's concat demuxer needs the terminal file repeated to honor its duration.
                    concat.WriteLine("file '" + previousFile + "'");
                    previousFile = null;
                }
                frameIndex?.Dispose(); frameIndex = null;
                concat?.Dispose(); concat = null;
                if (!string.IsNullOrEmpty(OutputDirectory)) WriteSummary();
                if (wasRecording)
                {
                    runtime.Diagnostics.NotifyCaptureOverhead("frame_sequence_stopped");
                    runtime.Diagnostics.RecordEvent("frame_sequence_" + reason);
                    runtime.Diagnostics.SaveSnapshot();
                }
            }
            catch (Exception error) { Status = "recording_finalize_error_" + error.Message; Debug.LogWarning(Status); }
        }

        void WriteSummary()
        {
            var summary = new Summary
            {
                utc = DateTime.UtcNow.ToString("o"), status = Status, engine = Application.unityVersion,
                platform = Application.platform.ToString(), sceneRevision = runtime.sceneRevision,
                assetRegistryRevision = runtime.assetRegistryRevision, frames = WrittenFrames,
                requestedFramesPerSecond = requestedFramesPerSecond, width = captureWidth, height = captureHeight,
                elapsedSeconds = Time.realtimeSinceStartup - startedAt, pngBytes = writtenBytes
            };
            File.WriteAllText(Path.Combine(OutputDirectory, "recording.json"), JsonUtility.ToJson(summary, true));
        }
        void OnApplicationQuit() { if (IsRecording) StopRecording("application_quit"); }
        void OnDisable() { if (IsRecording) StopRecording("component_disabled"); }
    }
}
