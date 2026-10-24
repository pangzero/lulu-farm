using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Profiling;

namespace LuluFarm
{
    public sealed class FarmRuntimeDiagnostics : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public string OutputDirectory { get; private set; }
        public float sessionSeconds;
        public float samplePeriod = .5f;
        public int routeProgress;
        public string LastError { get; private set; } = "";
        readonly List<float> frameTimes = new List<float>(60000);
        readonly FrameTiming[] timings = new FrameTiming[1];
        StreamWriter samples;
        float nextSample, nextSave;
        int screenshotSequence;
        readonly HashSet<string> visited = new HashSet<string>();
        bool recording;
        float startedAt;
        bool capturing;
        float performanceExclusionUntil;
        bool captureOverheadObserved;
        int performanceFramesExcluded;
        readonly List<PerformanceConfiguration> performanceConfigurations = new List<PerformanceConfiguration>();

        [Serializable]
        public sealed class PerformanceConfiguration
        {
            public string utc, quality;
            public int width, height;
            public float sessionSeconds;
        }

        [Serializable]
        public sealed class Snapshot
        {
            public string timestampUtc, revision, assetRegistryRevision, platform, operatingSystem, deviceModel, cpu, gpu, graphicsAPI;
            public string runtimeEvidence = "observed_runtime_state_not_art_or_device_acceptance";
            public string inputAutomation;
            public string performanceRunClassification;
            public string currentQuality;
            public string performanceStatisticsScope = "whole_session_samples; a mixed-settings session is invalid for per-quality performance claims";
            public bool performanceSettingsStable;
            public PerformanceConfiguration[] performanceConfigurations;
            public string unityVersion, quality, animationStatus, motion, inputSource, currentStage, wardrobe, obstruction;
            public int width, height, systemMemoryMB, graphicsMemoryMB, sampledFrames, routeProgress, routeTotal, cameraCollisionBufferOverflows;
            public int performanceFramesExcluded;
            public float durationSeconds, medianFrameMs, p95FrameMs, meanFrameMs, actualSpeed, cameraYaw, cameraPitch, cameraRequestedDistance, cameraActualDistance;
            public double cpuFrameMs, gpuFrameMs;
            public bool frameTimingAvailable, cpuTimingAvailable, gpuTimingAvailable, paused, grounded, targetInsideViewport, cinemachineLive;
            public long totalAllocatedBytes, totalReservedBytes, monoUsedBytes;
            public Vector3 playerPosition, cameraPosition;
            public Vector2 inputMove;
            public string collisionFlags;
            public bool uiBlocked,applicationFocused;
            public string[] visitedRouteMarkers;
        }

        public void BeginSession()
        {
            if (recording) return;
            string baseDirectory = Path.Combine(Application.persistentDataPath, "FarmEvidence");
            string[] args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == "--farm-evidence") baseDirectory = args[i + 1];
            OutputDirectory = Path.Combine(baseDirectory, DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
            try
            {
                Directory.CreateDirectory(OutputDirectory);
                samples = new StreamWriter(Path.Combine(OutputDirectory, "route-samples.jsonl"), false);
                startedAt = Time.realtimeSinceStartup;
                recording = true;
                RecordEvent("session_started");
                SaveSnapshot();
            }
            catch (Exception error) { LastError = error.Message; Debug.LogWarning("Farm evidence writer: " + error.Message); }
        }

        void Update()
        {
            if (!recording || runtime == null || !runtime.Initialized) return;
            sessionSeconds = Time.realtimeSinceStartup - startedAt;
            ObservePerformanceConfiguration();
            bool captureActive = runtime.Recorder != null && runtime.Recorder.IsRecording;
            if (captureActive || Time.realtimeSinceStartup < performanceExclusionUntil) performanceFramesExcluded++;
            else if (!runtime.Input.Paused && frameTimes.Count < 120000)
                frameTimes.Add(Time.unscaledDeltaTime * 1000f);
            FrameTimingManager.CaptureFrameTimings();
            if (Time.unscaledTime < nextSample) return;
            nextSample = Time.unscaledTime + samplePeriod;
            CheckRoute();
            try
            {
                samples.WriteLine(JsonUtility.ToJson(GetSnapshot(false)));
                if (Time.unscaledTime >= nextSave)
                { nextSave = Time.unscaledTime + 10; SaveSnapshot(); samples.Flush(); }
            }
            catch (Exception error) { LastError = error.Message; }
        }

        void CheckRoute()
        {
            var markers = runtime.routeMarkers;
            if (markers == null) return;
            for (int i = 0; i < markers.Length; i++)
            {
                var marker = markers[i];
                if (Vector3.Distance(runtime.playerRoot.transform.position, marker.position) > marker.radius) continue;
                if (visited.Add(marker.name)) RecordEvent("route_proximity_" + marker.name);
                if (i == routeProgress) { routeProgress++; RecordEvent("ordered_route_marker_" + marker.name); }
            }
        }

        public Snapshot GetSnapshot(bool aggregate)
        {
            ObservePerformanceConfiguration();
            bool mixedSettings = performanceConfigurations.Count > 1;
            var snap = new Snapshot
            {
                timestampUtc = DateTime.UtcNow.ToString("o"), revision = runtime.sceneRevision,
                assetRegistryRevision = runtime.assetRegistryRevision,
                platform = Application.platform.ToString(), unityVersion = Application.unityVersion,
                operatingSystem = SystemInfo.operatingSystem, deviceModel = SystemInfo.deviceModel,
                cpu = SystemInfo.processorType, gpu = SystemInfo.graphicsDeviceName,
                graphicsAPI = SystemInfo.graphicsDeviceType.ToString(), systemMemoryMB = SystemInfo.systemMemorySize,
                graphicsMemoryMB = SystemInfo.graphicsMemorySize, width = Screen.width, height = Screen.height,
                quality = mixedSettings ? "mixed_settings" : runtime.QualityLabel,
                currentQuality = runtime.QualityLabel, performanceSettingsStable = !mixedSettings,
                performanceConfigurations = performanceConfigurations.ToArray(),
                durationSeconds = sessionSeconds, sampledFrames = frameTimes.Count,
                paused = runtime.Input.Paused, grounded = runtime.Player.IsGrounded,
                playerPosition = runtime.playerRoot.transform.position, cameraPosition = runtime.mainCamera.transform.position,
                actualSpeed = runtime.Player.ActualSpeed, cameraYaw = runtime.CameraRig.Yaw,
                inputMove=runtime.Input.Move,collisionFlags=runtime.Player.LastCollision.ToString(),uiBlocked=runtime.Input.UIBlocked,applicationFocused=Application.isFocused,
                cameraPitch = runtime.CameraRig.Pitch, cameraRequestedDistance = runtime.CameraRig.RequestedDistance,
                cameraActualDistance = runtime.CameraRig.ActualDistance, obstruction = runtime.CameraRig.ObstructionName,
                cameraCollisionBufferOverflows = runtime.CameraRig.CollisionBufferOverflows,
                targetInsideViewport = runtime.CameraRig.TargetVisible,
                cinemachineLive = runtime.CameraRig.CinemachineIsLive,
                animationStatus = runtime.Player.animationBridge.Status, motion = runtime.Player.animationBridge.CurrentMotion,
                inputSource = runtime.Input.ActiveInputSource, currentStage = runtime.MixedStage ? "mixed" : runtime.MatureStage ? "mature" : "seedling",
                wardrobe = runtime.wardrobe != null ? runtime.wardrobe.CurrentName : "unconfigured",
                totalAllocatedBytes = Profiler.GetTotalAllocatedMemoryLong(), totalReservedBytes = Profiler.GetTotalReservedMemoryLong(),
                monoUsedBytes = Profiler.GetMonoUsedSizeLong(), routeProgress = routeProgress,
                routeTotal = runtime.routeMarkers != null ? runtime.routeMarkers.Length : 0,
                visitedRouteMarkers = new List<string>(visited).ToArray()
            };
            snap.performanceFramesExcluded = performanceFramesExcluded;
            snap.performanceRunClassification = mixedSettings ?
                "mixed_quality_or_resolution_not_a_valid_per_quality_device_performance_run" : captureOverheadObserved ?
                "capture_operations_present_not_a_clean_device_performance_run" :
                "no_capture_operations_observed_still_requires_device_and_route_review";
            var automation = runtime.GetComponent<FarmRoutePlayback>();
            snap.inputAutomation = automation != null ? automation.Status : "none";
            uint available = FrameTimingManager.GetLatestTimings(1, timings);
            if (Time.realtimeSinceStartup < performanceExclusionUntil || (runtime.Recorder != null && runtime.Recorder.IsRecording)) available = 0;
            snap.cpuTimingAvailable = available > 0 && timings[0].cpuFrameTime > 0;
            snap.gpuTimingAvailable = available > 0 && timings[0].gpuFrameTime > 0;
            snap.frameTimingAvailable = snap.cpuTimingAvailable || snap.gpuTimingAvailable;
            if (snap.cpuTimingAvailable) snap.cpuFrameMs = timings[0].cpuFrameTime;
            if (snap.gpuTimingAvailable) snap.gpuFrameMs = timings[0].gpuFrameTime;
            if (aggregate && frameTimes.Count > 0)
            {
                var sorted = frameTimes.ToArray(); Array.Sort(sorted);
                double sum = 0; foreach (float value in sorted) sum += value;
                snap.meanFrameMs = (float)(sum / sorted.Length);
                snap.medianFrameMs = sorted[(sorted.Length - 1) / 2];
                snap.p95FrameMs = sorted[Mathf.Clamp(Mathf.CeilToInt(sorted.Length * .95f) - 1, 0, sorted.Length - 1)];
            }
            return snap;
        }

        void ObservePerformanceConfiguration()
        {
            if (!recording || runtime == null) return;
            var prior = performanceConfigurations.Count > 0 ? performanceConfigurations[performanceConfigurations.Count - 1] : null;
            if (prior != null && prior.quality == runtime.QualityLabel && prior.width == Screen.width && prior.height == Screen.height) return;
            var current = new PerformanceConfiguration { utc = DateTime.UtcNow.ToString("o"), quality = runtime.QualityLabel,
                width = Screen.width, height = Screen.height, sessionSeconds = Time.realtimeSinceStartup - startedAt };
            performanceConfigurations.Add(current);
            // Preserve all prior frame samples and configurations. Never relabel their aggregate as the new quality.
            try { File.AppendAllText(Path.Combine(OutputDirectory, "performance-configurations.jsonl"), JsonUtility.ToJson(current) + "\n"); }
            catch (Exception error) { LastError = error.Message; }
            if (prior != null) RecordEvent("performance_run_invalidated_by_quality_or_resolution_change");
        }

        public void SaveSnapshot()
        {
            if (!recording || runtime == null || runtime.Player == null) return;
            try { File.WriteAllText(Path.Combine(OutputDirectory, "runtime-latest.json"), JsonUtility.ToJson(GetSnapshot(true), true)); samples?.Flush(); }
            catch (Exception error) { LastError = error.Message; }
        }

        [Serializable] sealed class EventRecord { public string utc, action; public float sessionSeconds; public Vector3 position; }
        public void RecordEvent(string action)
        {
            if (!recording) return;
            try
            {
                var record = new EventRecord { utc = DateTime.UtcNow.ToString("o"), action = action,
                    sessionSeconds = sessionSeconds, position = runtime.playerRoot.transform.position };
                File.AppendAllText(Path.Combine(OutputDirectory, "events.jsonl"), JsonUtility.ToJson(record) + "\n");
            }
            catch (Exception error) { LastError = error.Message; }
        }

        public void CaptureScreenshot(string label)
        {
            if (!recording || capturing) return;
            var performance=runtime.GetComponent<FarmPerformanceSession>();
            if(performance!=null&&performance.Running){RecordEvent("screenshot_refused_during_clean_performance_run");return;}
            StartCoroutine(CaptureAtFrameEnd(label));
        }
        IEnumerator CaptureAtFrameEnd(string label)
        {
            capturing = true;
            NotifyCaptureOverhead("single_screenshot");
            yield return new WaitForEndOfFrame();
            Texture2D image = null;
            try
            {
                image = ScreenCapture.CaptureScreenshotAsTexture();
                string clean = string.Concat(Array.FindAll(label.ToCharArray(), c => char.IsLetterOrDigit(c) || c == '-' || c == '_'));
                string file = string.Format("{0:D3}-{1}.png", ++screenshotSequence, clean);
                File.WriteAllBytes(Path.Combine(OutputDirectory, file), image.EncodeToPNG());
                File.WriteAllText(Path.Combine(OutputDirectory, Path.GetFileNameWithoutExtension(file) + ".json"), JsonUtility.ToJson(GetSnapshot(true), true));
                RecordEvent("screenshot_written_" + file);
            }
            catch (Exception error) { LastError = error.Message; }
            finally { if (image != null) Destroy(image); capturing = false; NotifyCaptureOverhead("single_screenshot_finished"); }
        }
        public void NotifyCaptureOverhead(string reason)
        {
            // Readback, PNG compression and disk writes perturb timings, including following frames.
            performanceExclusionUntil = Mathf.Max(performanceExclusionUntil, Time.realtimeSinceStartup + 1f);
            if (!captureOverheadObserved) RecordEvent("performance_run_invalidated_by_" + reason);
            captureOverheadObserved = true;
        }
        void OnApplicationPause(bool pause) { if (pause) SaveSnapshot(); }
        void OnApplicationQuit() { SaveSnapshot(); samples?.Dispose(); recording = false; }
        void OnDestroy() { samples?.Dispose(); samples = null; recording = false; }
    }
}
