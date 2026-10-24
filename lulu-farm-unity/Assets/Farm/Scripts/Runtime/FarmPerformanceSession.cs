using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.Rendering;

namespace LuluFarm
{
    // A separate capture-free measurement session, never an art/manual-input acceptance.
    // Bootstrap opts in with --farm-performance-route and StartFor(runtime).
    [DefaultExecutionOrder(300)]
    public sealed class FarmPerformanceSession : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public string Status { get; private set; } = "not_started";
        public bool Running { get; private set; }
        const int MaximumFrameSamples = 250000;
        FarmRoutePlayback route;
        StreamWriter samples;
        string output, configuredStage, configuredQuality, configuredWardrobe;
        int configuredWidth, configuredHeight;
        float startedAt, nextSampleAt, nextFlushAt, warmupSeconds = 5;
        bool started, finished;
        readonly List<Counter> counters = new List<Counter>();
        readonly Series frameTimes = new Series();
        // O2: r07 sessions showed Time.unscaledDeltaTime values (up to 19.8 s) longer than the wall-clock
        // window that contained them and absent from the continuous Profiler capture. Keep the original
        // series for comparability and add the real interval between consecutive LateUpdates.
        readonly Series wallFrameTimes = new Series();
        double lastWallTime = -1;
        int deltaAnomalyFrames, windowDeltaAnomalyFrames;

        [Serializable] public sealed class Stats
        {
            public string name, category, unit, status, unavailableReason;
            public bool available;
            public int sampleCount, unavailableFrames;
            public double mean, p95, maximum;
        }
        [Serializable] sealed class CounterConfiguration
        {
            public string name, category, nativeUnit, outputUnit, unavailableReason;
            public bool recorderValid;
        }
        [Serializable] sealed class Configuration
        {
            public string utc, sceneRevision, registryRevision, platform, unity, os, device, cpu, gpu, graphicsAPI;
            public string stage, quality, renderPipeline, wardrobe;
            public int width, height, cropPlots, activeMaturePlots, activeSeedlingPlots, vSyncCount, targetFrameRate;
            public float warmupSeconds;
            public bool screenshots = false, frameRecording = false, stateExercise = false, loopingRoute = true;
            public string thermal = "unavailable_not_measured_no_portable_temperature_API";
            public string sampling = "one ProfilerRecorder completed-frame sample per LateUpdate; one JSONL aggregate per second; no video or screenshot capture";
            public string limitations = "Automated route, not manual UI acceptance. Logging/recorders have overhead. Counters may be unavailable; no inferred zeros. No thermal or performance pass is asserted.";
            public CounterConfiguration[] counters;
        }
        [Serializable] sealed class Sample
        {
            public string utc, phase, routeStatus, thermal = "unavailable_not_measured";
            public float elapsedSeconds;
            public bool applicationFocused;
            public int completedLaps, waypoint;
            public Vector3 position;
            public Stats frameTimeMs, wallFrameTimeMs;
            public int unscaledDeltaExceedsWallFrames;
            public Stats[] counters;
        }
        [Serializable] sealed class Summary
        {
            public string utc, stoppedBecause, routeStatus, acceptance = "measured_data_only_requires_review";
            public string thermal = "unavailable_not_measured_no_portable_temperature_API";
            public string statistics = "per-frame samples after configured warmup; mean and nearest-rank p95; not 1Hz spot samples";
            public float elapsedSeconds, warmupSeconds, measurementSeconds;
            public int completedLaps, lastWaypoint;
            public bool routeLoopRunningAtStop, configurationUnchanged;
            public Stats frameTimeMs, wallFrameTimeMs;
            public int unscaledDeltaExceedsWallFrames;
            public Stats[] counters;
        }

        sealed class Series
        {
            public readonly List<double> all = new List<double>(65536);
            public readonly List<double> window = new List<double>(256);
            public int missing, windowMissing;
            public void Add(double value) { all.Add(value); window.Add(value); }
            public void Missing() { missing++; windowMissing++; }
            public Stats Describe(string name, string category, string unit, string reason, bool whole)
            {
                var data = whole ? all : window;
                var result = new Stats { name = name, category = category, unit = unit,
                    sampleCount = data.Count, unavailableFrames = whole ? missing : windowMissing,
                    available = data.Count > 0, status = data.Count > 0 ? "available_measured" : "unavailable",
                    unavailableReason = data.Count > 0 ? "" : reason };
                if (data.Count > 0)
                {
                    double sum = 0, maximum = double.MinValue;
                    for (int i = 0; i < data.Count; i++) { sum += data[i]; maximum = Math.Max(maximum, data[i]); }
                    var sorted = data.ToArray(); Array.Sort(sorted);
                    result.mean = sum / data.Count; result.maximum = maximum;
                    result.p95 = sorted[Math.Max(0, (int)Math.Ceiling(sorted.Length * .95) - 1)];
                }
                return result;
            }
            public void ClearWindow() { window.Clear(); windowMissing = 0; }
        }
        sealed class Counter
        {
            public string name, category = "unavailable", nativeUnit = "unavailable", outputUnit, reason = "counter_not_available_on_this_player";
            public ProfilerRecorder recorder;
            public readonly Series values = new Series();
            public double multiplier = 1;
            public bool timer;
            public void Read()
            {
                if (!recorder.Valid || recorder.Count == 0)
                { values.Missing(); if (recorder.Valid) reason = "recorder_has_no_completed_sample"; return; }
                long raw = recorder.LastValue;
                if (raw < 0 || (timer && raw == 0))
                { values.Missing(); reason = "no_valid_positive_timer_sample"; return; }
                // Zero is valid for count/byte counters (especially GC), once a real sample exists.
                values.Add(raw * multiplier);
            }
            public Stats Describe(bool whole) => values.Describe(name, category, outputUnit, reason, whole);
        }

        public static FarmPerformanceSession StartFor(FarmRuntimeBootstrap bootstrap)
        {
            var session = bootstrap.GetComponent<FarmPerformanceSession>();
            if (session == null) session = bootstrap.gameObject.AddComponent<FarmPerformanceSession>();
            if (session.started) return session;
            session.runtime = bootstrap; session.started = true;
            session.StartCoroutine(session.Begin());
            return session;
        }

        IEnumerator Begin()
        {
            while (runtime != null && !runtime.Initialized) yield return null;
            if (runtime == null || runtime.Diagnostics == null || string.IsNullOrEmpty(runtime.Diagnostics.OutputDirectory))
            { Status = "refused_missing_runtime_evidence_directory"; yield break; }
            output = Path.Combine(runtime.Diagnostics.OutputDirectory, "performance");
            string[] args = Environment.GetCommandLineArgs();
            configuredStage = Option(args, "--farm-performance-stage", "mature");
            string quality = Option(args, "--farm-performance-quality", "current");
            string warmup = Option(args, "--farm-performance-warmup", "5");
            if (Array.IndexOf(args, "--farm-record-frames") >= 0 || runtime.Recorder.IsRecording)
            { Finish("refused_frame_recording_conflict"); yield break; }
            var existing = runtime.GetComponent<FarmRoutePlayback>();
            if (existing != null && existing.Running)
            { Finish("refused_another_route_already_running"); yield break; }
            if ((configuredStage != "mature" && configuredStage != "mixed") ||
                (quality != "current" && quality != "desktop" && quality != "mobile") ||
                !float.TryParse(warmup, NumberStyles.Float, CultureInfo.InvariantCulture, out warmupSeconds) ||
                float.IsNaN(warmupSeconds) || float.IsInfinity(warmupSeconds) || warmupSeconds < 0 || warmupSeconds > 120)
            { Finish("refused_invalid_performance_options"); yield break; }
            if (configuredStage == "mixed") runtime.SetMixedStages(); else runtime.SetMature(true);
            if (quality != "current") runtime.SetQuality(quality == "mobile" ? 0 : 1);
            // Apply requested configuration before starting recorders or the measured route.
            yield return null; yield return null;
            configuredQuality = runtime.QualityLabel; configuredWidth = Screen.width; configuredHeight = Screen.height;
            configuredWardrobe = runtime.wardrobe != null ? runtime.wardrobe.CurrentName : "unconfigured";
            try
            {
                Directory.CreateDirectory(output);
                var handles = new List<ProfilerRecorderHandle>(); ProfilerRecorderHandle.GetAvailable(handles);
                AddCounter(handles, "Main Thread", "Nanoseconds", "ms", true);
                AddCounter(handles, "Render Thread", "Nanoseconds", "ms", true);
                AddCounter(handles, "Draw Calls Count", "Count", "count", false);
                AddCounter(handles, "Triangles Count", "Count", "count", false);
                AddCounter(handles, "SetPass Calls Count", "Count", "count", false);
                AddCounter(handles, "GC Allocated In Frame", "Bytes", "bytes", false);
                AddCounter(handles, "GC Used Memory", "Bytes", "bytes", false);
                WriteConfiguration();
                samples = new StreamWriter(new FileStream(Path.Combine(output, "samples.jsonl"), FileMode.CreateNew, FileAccess.Write, FileShare.Read), System.Text.Encoding.UTF8, 65536);
                startedAt = Time.realtimeSinceStartup; nextSampleAt = startedAt + 1; nextFlushAt = startedAt + 5;
                Running = true; Status = "measuring_capture_free_route";
                route = FarmRoutePlayback.StartFor(runtime, performance: true);
                runtime.Diagnostics.RecordEvent("performance_session_started_" + configuredStage + "_no_capture");
            }
            catch (Exception error) { Finish("initialization_failed_" + error.Message); }
        }

        static string Option(string[] args, string key, string fallback)
        {
            int index = Array.IndexOf(args, key);
            return index < 0 ? fallback : index + 1 < args.Length ? args[index + 1].ToLowerInvariant() : "invalid_missing_value";
        }
        void AddCounter(List<ProfilerRecorderHandle> handles, string name, string expectedUnit, string outputUnit, bool timer)
        {
            var counter = new Counter { name = name, outputUnit = outputUnit, timer = timer, multiplier = timer ? .000001 : 1 };
            counters.Add(counter);
            foreach (var handle in handles)
            {
                var description = ProfilerRecorderHandle.GetDescription(handle);
                if (description.Name != name) continue;
                counter.category = description.Category.ToString(); counter.nativeUnit = description.UnitType.ToString();
                if (counter.nativeUnit != expectedUnit) { counter.reason = "unexpected_native_unit_" + counter.nativeUnit; return; }
                try
                {
                    counter.recorder = ProfilerRecorder.StartNew(description.Category, name, 1,
                        ProfilerRecorderOptions.StartImmediately | ProfilerRecorderOptions.WrapAroundWhenCapacityReached | ProfilerRecorderOptions.SumAllSamplesInFrame);
                    counter.reason = counter.recorder.Valid ? "waiting_for_completed_sample" : "recorder_invalid_on_this_player";
                }
                catch (Exception error) { counter.reason = "recorder_unavailable_" + error.Message; }
                return;
            }
        }

        bool ConfigurationMatches()
        {
            string stage = runtime.MixedStage ? "mixed" : runtime.MatureStage ? "mature" : "seedling";
            string wardrobe = runtime.wardrobe != null ? runtime.wardrobe.CurrentName : "unconfigured";
            return stage == configuredStage && runtime.QualityLabel == configuredQuality &&
                Screen.width == configuredWidth && Screen.height == configuredHeight && wardrobe == configuredWardrobe;
        }
        void LateUpdate()
        {
            if (!Running || finished) return;
            if (runtime.Recorder.IsRecording) { Finish("invalidated_by_frame_recording"); return; }
            if (!ConfigurationMatches()) { Finish("invalidated_by_stage_quality_resolution_or_wardrobe_change"); return; }
            if (runtime.Input.Paused) { Finish("interrupted_by_pause"); return; }
            if (route == null || !route.Running) { Finish("route_stopped_" + (route != null ? route.Status : "missing")); return; }
            float now = Time.realtimeSinceStartup;
            double wallNow = Time.realtimeSinceStartupAsDouble, wallMs = lastWallTime >= 0 ? (wallNow - lastWallTime) * 1000.0 : -1;
            lastWallTime = wallNow;
            if (now - startedAt >= warmupSeconds)
            {
                if (frameTimes.all.Count >= MaximumFrameSamples) { Finish("sample_capacity_reached_incomplete_measurement"); return; }
                if (Time.unscaledDeltaTime > 0) frameTimes.Add(Time.unscaledDeltaTime * 1000.0);
                if (wallMs > 0)
                {
                    wallFrameTimes.Add(wallMs);
                    if (Time.unscaledDeltaTime * 1000.0 > wallMs + 50) { deltaAnomalyFrames++; windowDeltaAnomalyFrames++; }
                }
                foreach (var counter in counters) counter.Read();
            }
            if (now < nextSampleAt) return;
            try
            {
                WriteSample(now);
                if (now >= nextFlushAt) { samples.Flush(); nextFlushAt = now + 5; }
                nextSampleAt = now + 1;
            }
            catch (Exception error) { Finish("logging_failed_" + error.Message); }
        }
        Stats[] CounterStats(bool whole)
        {
            var result = new Stats[counters.Count];
            for (int i = 0; i < counters.Count; i++) result[i] = counters[i].Describe(whole);
            return result;
        }
        void WriteSample(float now)
        {
            var row = new Sample { utc = DateTime.UtcNow.ToString("o"), elapsedSeconds = now - startedAt,
                phase = now - startedAt < warmupSeconds ? "warmup_excluded" : "measuring",
                routeStatus = route != null ? route.Status : "not_started", completedLaps = route != null ? route.CompletedLaps : 0,
                waypoint = route != null ? route.WaypointIndex : 0, applicationFocused = Application.isFocused,
                position = runtime.playerRoot.transform.position, counters = CounterStats(false),
                frameTimeMs = frameTimes.Describe("Unity frame interval", "Time.unscaledDeltaTime", "ms", "warmup_or_no_frames", false),
                wallFrameTimeMs = wallFrameTimes.Describe("Wall-clock LateUpdate interval", "Time.realtimeSinceStartupAsDouble", "ms", "warmup_or_no_frames", false),
                unscaledDeltaExceedsWallFrames = windowDeltaAnomalyFrames };
            samples.WriteLine(JsonUtility.ToJson(row));
            frameTimes.ClearWindow(); wallFrameTimes.ClearWindow(); windowDeltaAnomalyFrames = 0; foreach (var counter in counters) counter.values.ClearWindow();
        }
        void WriteConfiguration()
        {
            var config = new Configuration { utc = DateTime.UtcNow.ToString("o"), sceneRevision = runtime.sceneRevision,
                registryRevision = runtime.assetRegistryRevision, platform = Application.platform.ToString(), unity = Application.unityVersion,
                os = SystemInfo.operatingSystem, device = SystemInfo.deviceModel, cpu = SystemInfo.processorType,
                gpu = SystemInfo.graphicsDeviceName, graphicsAPI = SystemInfo.graphicsDeviceType.ToString(),
                stage = configuredStage, quality = configuredQuality, width = configuredWidth, height = configuredHeight,
                renderPipeline = GraphicsSettings.currentRenderPipeline != null ? GraphicsSettings.currentRenderPipeline.name : "none",
                wardrobe = configuredWardrobe, warmupSeconds = warmupSeconds, vSyncCount = QualitySettings.vSyncCount,
                targetFrameRate = Application.targetFrameRate, counters = new CounterConfiguration[counters.Count] };
            if (runtime.crops != null) foreach (var crop in runtime.crops)
            {
                if (crop == null) continue; config.cropPlots++;
                if (crop.mature != null && crop.mature.activeInHierarchy) config.activeMaturePlots++;
                if (crop.seedling != null && crop.seedling.activeInHierarchy) config.activeSeedlingPlots++;
            }
            for (int i = 0; i < counters.Count; i++)
            {
                var c = counters[i]; config.counters[i] = new CounterConfiguration { name = c.name, category = c.category,
                    nativeUnit = c.nativeUnit, outputUnit = c.outputUnit, recorderValid = c.recorder.Valid, unavailableReason = c.reason };
            }
            File.WriteAllText(Path.Combine(output, "configuration.json"), JsonUtility.ToJson(config, true));
        }
        void Finish(string reason)
        {
            if (finished) return;
            finished = true; bool wasRunning = Running; Running = false; Status = reason;
            try
            {
                if (!string.IsNullOrEmpty(output))
                {
                    Directory.CreateDirectory(output);
                    float elapsed = wasRunning ? Time.realtimeSinceStartup - startedAt : 0;
                    if (samples != null && wasRunning) WriteSample(Time.realtimeSinceStartup);
                    samples?.Flush();
                    var summary = new Summary { utc = DateTime.UtcNow.ToString("o"), stoppedBecause = reason,
                        elapsedSeconds = elapsed, warmupSeconds = warmupSeconds, measurementSeconds = Mathf.Max(0, elapsed - warmupSeconds),
                        completedLaps = route != null ? route.CompletedLaps : 0, lastWaypoint = route != null ? route.WaypointIndex : 0,
                        routeStatus = route != null ? route.Status : "not_started", routeLoopRunningAtStop = route != null && route.Running,
                        configurationUnchanged = wasRunning && ConfigurationMatches(), counters = CounterStats(true),
                        frameTimeMs = frameTimes.Describe("Unity frame interval", "Time.unscaledDeltaTime", "ms", "no_measured_frames", true),
                        wallFrameTimeMs = wallFrameTimes.Describe("Wall-clock LateUpdate interval", "Time.realtimeSinceStartupAsDouble", "ms", "no_measured_frames", true),
                        unscaledDeltaExceedsWallFrames = deltaAnomalyFrames };
                    File.WriteAllText(Path.Combine(output, "summary.json"), JsonUtility.ToJson(summary, true));
                }
            }
            catch (Exception error) { Debug.LogWarning("Performance session could not finish log: " + error.Message); }
            finally
            {
                samples?.Dispose(); samples = null;
                foreach (var counter in counters) if (counter.recorder.Valid) counter.recorder.Dispose();
                if (route != null && route.Running) route.Stop("performance_session_" + reason);
            }
        }
        void OnApplicationQuit() { Finish("application_quit"); }
        void OnDisable() { if (started) Finish("performance_component_disabled"); }
        void OnDestroy() { if (started) Finish("performance_component_destroyed"); }
    }
}
