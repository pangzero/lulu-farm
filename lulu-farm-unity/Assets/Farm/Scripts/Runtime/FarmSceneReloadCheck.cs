using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Profiling;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace LuluFarm
{
    // Opt-in diagnostic only. A normal game launch creates no object or coroutine.
    public sealed class FarmSceneReloadCheck : MonoBehaviour
    {
        const int Reloads = 3;
        const float SettleSeconds = 3f;
        const double InitializeTimeout = 45;
        static FarmSceneReloadCheck instance;

        [Serializable] sealed class Check
        {
            public string id, expected, observed;
            public bool passed;
        }
        [Serializable] sealed class Sample
        {
            public int reloadIndex, frame, activeSceneBuildIndex, loadedSceneCount;
            public string utc, activeSceneName, activeScenePath;
            public double realtimeSeconds, secondsAfterInitialized;
            public int sceneRoots, sceneRenderers, globalSceneRenderers, runtimeInstances, initializedRuntimes;
            public int playerControllers, inputRouters, hudInstances, eventSystems, diagnosticInstances, reloadCheckInstances;
            public int sceneEnabledOccluders, staticOccluderEntries, staticOccluderLive, staticOccluderDead, staticOccluderWrongScene;
            public int[] runtimeInstanceIds;
            public long managedUsedBytes, managedReservedBytes, managedGCBytes;
            public long unityAllocatedBytes, unityReservedBytes, unityUnusedReservedBytes;
            public long processWorkingSetBytes;
            public string processWorkingSetAvailability;
            public Check[] checks;
        }
        [Serializable] sealed class Report
        {
            public string startedUTC, finishedUTC, engine, platform, output, targetScene, error;
            public string status = "running";
            public string scope = "Three normal LoadSceneAsync(Single) re-entries; object/static registry lifecycle check, not a performance or visual test";
            public string memoryConclusion = "measurements_only_not_a_leak_clearance_or_performance_benchmark";
            public string memoryCounters = "Mono used/reserved and GC managed bytes; Unity allocator totals (not an isolated native-only total); optional process working set includes managed/native/graphics mappings";
            public string visual = "not_reviewed_by_this_check", userArt = "not_approved_by_this_check";
            public int requestedReloads = Reloads, completedReloads;
            public float minimumSettleSeconds = SettleSeconds;
            public bool quitAfterRequested, allObjectChecksPassed;
            public Sample[] samples;
            public string[] limitations = {
                "UnloadUnusedAssets and forced GC deliberately perturb frame timing; never use this session as a warm performance run.",
                "Three cycles can detect duplicated live scene objects and stale static occluders, but do not prove all native/managed resources are leak-free.",
                "Runtime diagnostics create a new ordinary session on every scene initialization; this checker stores its own aggregate separately.",
                "No screenshot, camera movement, material modification, transform teleport or source-model edit is performed."
            };
        }

        readonly List<Sample> samples = new List<Sample>();
        Report report;
        string directory, scenePath;
        int sceneIndex;
        bool finished, quitWhenComplete;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void InstallIfRequested()
        {
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--farm-reload-check") < 0 || instance != null) return;
            var host = new GameObject("FarmSceneReloadCheck — explicit diagnostic");
            DontDestroyOnLoad(host);
            instance = host.AddComponent<FarmSceneReloadCheck>();
        }

        IEnumerator Start()
        {
            var args = Environment.GetCommandLineArgs();
            quitWhenComplete = Array.IndexOf(args, "--farm-quit-after") >= 0;
            string baseDirectory = Path.Combine(Application.persistentDataPath, "FarmEvidence");
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == "--farm-evidence") baseDirectory = args[i + 1];
            directory = Path.Combine(baseDirectory, "reload-check-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
            report = new Report { startedUTC = DateTime.UtcNow.ToString("o"), engine = Application.unityVersion,
                platform = Application.platform.ToString(), output = directory, quitAfterRequested = quitWhenComplete };
            try
            {
                Directory.CreateDirectory(directory);
                if (new[] { "--farm-route", "--farm-performance-route", "--farm-record-frames" }.Any(a => Array.IndexOf(args, a) >= 0))
                    throw new InvalidOperationException("Reload lifecycle checks must run separately from movement, performance and frame-recording sessions.");
                Save();
            }
            catch (Exception error) { FinishFailure(error); yield break; }

            // Catch exceptions in the sequence while allowing Unity to wait for the yielded
            // AsyncOperation/WaitForSecondsRealtime values. No nested test coroutines are used.
            var sequence = Sequence();
            while (!finished)
            {
                object next = null; bool more = false; Exception failure = null;
                try { more = sequence.MoveNext(); if (more) next = sequence.Current; }
                catch (Exception error) { failure = error; }
                if (failure != null) { FinishFailure(failure); yield break; }
                if (!more) break;
                yield return next;
            }
        }

        IEnumerator Sequence()
        {
            // Bootstrap.Start must have executed in the authored first scene.
            yield return null;
            var initial = SceneManager.GetActiveScene();
            if (initial.name != "FarmWorld" || initial.buildIndex < 0)
                throw new InvalidOperationException("Start the checker in the built FarmWorld scene.");
            scenePath = initial.path; sceneIndex = initial.buildIndex; report.targetScene = scenePath;
            for (int cycle = 0; cycle <= Reloads; cycle++)
            {
                double waitingSince = Time.realtimeSinceStartupAsDouble;
                while (!RuntimeReady())
                {
                    if (Time.realtimeSinceStartupAsDouble - waitingSince > InitializeTimeout)
                        throw new TimeoutException("Farm runtime did not finish initialization after reload " + cycle);
                    yield return null;
                }
                double initializedAt = Time.realtimeSinceStartupAsDouble;
                yield return new WaitForSecondsRealtime(SettleSeconds);
                yield return Resources.UnloadUnusedAssets();
                GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
                yield return null;
                var sample = Capture(cycle, Time.realtimeSinceStartupAsDouble - initializedAt);
                samples.Add(sample); report.completedReloads = cycle; Save();
                if (cycle == Reloads) break;

                // Use the actual build scene and its normal lifecycle; the observer alone persists.
                var operation = SceneManager.LoadSceneAsync(sceneIndex, LoadSceneMode.Single);
                if (operation == null) throw new InvalidOperationException("LoadSceneAsync returned null.");
                yield return operation;
                yield return null;
            }
            report.allObjectChecksPassed = samples.Count == Reloads + 1 && samples.All(s => s.checks.All(c => c.passed));
            report.status = report.allObjectChecksPassed ? "object_lifecycle_checks_pass_memory_recorded" : "object_lifecycle_check_failures";
            report.finishedUTC = DateTime.UtcNow.ToString("o");
            finished = true; Save();
            Debug.Log("Farm reload lifecycle check: " + report.status + "; " + directory);
            if (quitWhenComplete) Application.Quit(report.allObjectChecksPassed ? 0 : 1);
        }

        bool RuntimeReady()
        {
            var scene = SceneManager.GetActiveScene();
            if (!scene.IsValid() || !scene.isLoaded || scene.path != scenePath) return false;
            return Object.FindObjectsByType<FarmRuntimeBootstrap>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .Any(r => r.gameObject.scene == scene && r.Initialized && r.Player != null && r.CameraRig != null && r.Diagnostics != null && r.HUD != null);
        }

        Sample Capture(int cycle, double settled)
        {
            var scene = SceneManager.GetActiveScene();
            var roots = scene.GetRootGameObjects();
            var renderers = roots.SelectMany(r => r.GetComponentsInChildren<Renderer>(true)).ToArray();
            var runtimes = Object.FindObjectsByType<FarmRuntimeBootstrap>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            var occluders = roots.SelectMany(r => r.GetComponentsInChildren<FarmCameraOccluder>(true)).Where(o => o.isActiveAndEnabled).ToArray();
            var registered = FarmCameraOccluder.Active.ToArray();
            var s = new Sample { reloadIndex = cycle, utc = DateTime.UtcNow.ToString("o"), frame = Time.frameCount,
                realtimeSeconds = Time.realtimeSinceStartupAsDouble, secondsAfterInitialized = settled,
                activeSceneName = scene.name, activeScenePath = scene.path, activeSceneBuildIndex = scene.buildIndex,
                loadedSceneCount = SceneManager.sceneCount, sceneRoots = roots.Length, sceneRenderers = renderers.Length,
                globalSceneRenderers = Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None).Length,
                runtimeInstances = runtimes.Length, initializedRuntimes = runtimes.Count(r => r.Initialized && r.gameObject.scene == scene),
                runtimeInstanceIds = runtimes.Select(r => r.GetInstanceID()).ToArray(),
                playerControllers = Count<FarmPlayerController>(), inputRouters = Count<FarmInputRouter>(), hudInstances = Count<FarmHUD>(),
                eventSystems = Count<EventSystem>(), diagnosticInstances = Count<FarmRuntimeDiagnostics>(), reloadCheckInstances = Count<FarmSceneReloadCheck>(),
                sceneEnabledOccluders = occluders.Length, staticOccluderEntries = registered.Length,
                staticOccluderLive = registered.Count(o => o != null && o.isActiveAndEnabled),
                staticOccluderDead = registered.Count(o => o == null),
                staticOccluderWrongScene = registered.Count(o => o != null && o.gameObject.scene != scene),
                managedUsedBytes = Profiler.GetMonoUsedSizeLong(), managedReservedBytes = Profiler.GetMonoHeapSizeLong(),
                managedGCBytes = GC.GetTotalMemory(false), unityAllocatedBytes = Profiler.GetTotalAllocatedMemoryLong(),
                unityReservedBytes = Profiler.GetTotalReservedMemoryLong(), unityUnusedReservedBytes = Profiler.GetTotalUnusedReservedMemoryLong(),
                processWorkingSetBytes = -1, processWorkingSetAvailability = "not_available" };
            try
            {
                using (var process = System.Diagnostics.Process.GetCurrentProcess())
                { process.Refresh(); s.processWorkingSetBytes = process.WorkingSet64; s.processWorkingSetAvailability = "reported_by_process_api"; }
            }
            catch (Exception error) { s.processWorkingSetAvailability = error.GetType().Name; }

            var checks = new List<Check>();
            Add(checks, "same_FarmWorld", scene.path == scenePath && scene.buildIndex == sceneIndex, scenePath, scene.path);
            Add(checks, "one_loaded_game_scene", s.loadedSceneCount == 1, "1", s.loadedSceneCount.ToString());
            Add(checks, "one_initialized_runtime", s.runtimeInstances == 1 && s.initializedRuntimes == 1, "1/1", s.runtimeInstances + "/" + s.initializedRuntimes);
            Add(checks, "one_player_and_input", s.playerControllers == 1 && s.inputRouters == 1, "1/1", s.playerControllers + "/" + s.inputRouters);
            Add(checks, "one_HUD_eventSystem_diagnostics_observer", s.hudInstances == 1 && s.eventSystems == 1 && s.diagnosticInstances == 1 && s.reloadCheckInstances == 1,
                "1/1/1/1", s.hudInstances + "/" + s.eventSystems + "/" + s.diagnosticInstances + "/" + s.reloadCheckInstances);
            Add(checks, "minimum_settle", settled >= SettleSeconds, ">=3s after initialization", settled.ToString("F3", System.Globalization.CultureInfo.InvariantCulture));
            Add(checks, "scene_renderers_present", s.sceneRenderers > 0, ">0", s.sceneRenderers.ToString());
            Add(checks, "no_extra_persistent_renderers", s.globalSceneRenderers == s.sceneRenderers, s.sceneRenderers.ToString(), s.globalSceneRenderers.ToString());
            Add(checks, "static_occluder_registry_matches_scene", s.sceneEnabledOccluders > 0 && s.staticOccluderEntries == s.sceneEnabledOccluders
                && s.staticOccluderLive == s.sceneEnabledOccluders && s.staticOccluderDead == 0 && s.staticOccluderWrongScene == 0,
                s.sceneEnabledOccluders + " live scene entries; 0 dead/other-scene", s.staticOccluderEntries + " entries; " + s.staticOccluderDead + " dead; " + s.staticOccluderWrongScene + " other-scene");
            if (samples.Count > 0)
            {
                var baseline = samples[0];
                Add(checks, "renderer_count_matches_initial_scene", s.sceneRenderers == baseline.sceneRenderers, baseline.sceneRenderers.ToString(), s.sceneRenderers.ToString());
                Add(checks, "root_count_matches_initial_scene", s.sceneRoots == baseline.sceneRoots, baseline.sceneRoots.ToString(), s.sceneRoots.ToString());
                Add(checks, "static_occluder_count_restored", s.staticOccluderEntries == baseline.staticOccluderEntries,
                    baseline.staticOccluderEntries.ToString(), s.staticOccluderEntries.ToString());
            }
            s.checks = checks.ToArray();
            return s;
        }
        static int Count<T>() where T : Object => Object.FindObjectsByType<T>(FindObjectsInactive.Include, FindObjectsSortMode.None).Length;
        static void Add(List<Check> list, string id, bool passed, string expected, string observed)
            => list.Add(new Check { id = id, passed = passed, expected = expected, observed = observed });
        void Save()
        {
            report.samples = samples.ToArray();
            File.WriteAllText(Path.Combine(directory, "reload-check.json"), JsonUtility.ToJson(report, true));
        }
        void FinishFailure(Exception error)
        {
            finished = true;
            if (report != null)
            {
                report.status = "failed_or_incomplete"; report.error = error.ToString(); report.finishedUTC = DateTime.UtcNow.ToString("o");
                try { Save(); } catch (Exception writeError) { Debug.LogError("Reload report could not be saved: " + writeError); }
            }
            Debug.LogError("Farm reload lifecycle check failed: " + error);
            if (quitWhenComplete) Application.Quit(1);
        }
        void OnApplicationQuit()
        {
            if (!finished && report != null) FinishFailure(new InvalidOperationException("Application exited before all three reloads completed."));
        }
        void OnDestroy()
        {
            if (instance == this) instance = null;
            if (!finished && report != null) FinishFailure(new InvalidOperationException("Persistent reload observer was destroyed before completion."));
        }
    }
}
