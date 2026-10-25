using System;
using System.Collections;
using System.IO;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
#endif

namespace LuluFarm
{
    [Serializable]
    public sealed class FarmRouteWaypoint
    {
        public string name;
        public Vector3 position;
        public bool screenshot;
        public bool orbit;
    }

    // Reproducible simulation of real input events. This is never recorded as human UI/phone acceptance.
    [DefaultExecutionOrder(-150)]
    public sealed class FarmRoutePlayback : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public FarmRouteWaypoint[] waypoints = Array.Empty<FarmRouteWaypoint>();
        public bool runBetweenStops = true;
        public bool exerciseStageWardrobeAndQuality = true;
        public float arrivalRadius = .35f;
        public float blockedSeconds = 6;
        public bool Running { get; private set; }
        public string Status { get; private set; } = "not_started";
        public int WaypointIndex { get; private set; }
        public bool PerformanceMode { get; private set; }
        public int CompletedLaps { get; private set; }
        Coroutine routine;
        bool restoreState, initialMature, initialMixed, automatedPausePending;
        int initialQuality, initialWardrobe;
#if ENABLE_INPUT_SYSTEM
        Gamepad virtualGamepad;
#endif

        [Serializable] sealed class Result
        {
            public string utc, status, mode = "automated_input_events_not_manual_ui_or_device_acceptance", revision;
            public int reachedWaypoints, plannedWaypoints;
            public int completedLaps;
            public bool performanceMode, loopingWithoutTeleport, screenshotsSuppressed;
            public bool applicationFocused, virtualGamepadPresent, virtualGamepadEnabled, virtualGamepadCanRunInBackground;
            public Vector3 finalPosition;
            public FarmRouteWaypoint[] waypoints;
        }

        public static FarmRoutePlayback StartFor(FarmRuntimeBootstrap bootstrap, bool performance = false)
        {
            var playback = bootstrap.GetComponent<FarmRoutePlayback>();
            if (playback == null) playback = bootstrap.gameObject.AddComponent<FarmRoutePlayback>();
            if (playback.Running) return playback;
            playback.runtime = bootstrap;
            playback.PerformanceMode = performance;
            playback.Begin();
            return playback;
        }

        [ContextMenu("Begin simulated-input route")]
        public void Begin()
        {
            if (Running || !Application.isPlaying) return;
            if (runtime == null) runtime = GetComponent<FarmRuntimeBootstrap>();
            if (runtime == null) { Status = "missing_runtime"; return; }
#if ENABLE_INPUT_SYSTEM
            Running = true; WaypointIndex = 0; CompletedLaps = 0; Status = "waiting_for_runtime";
            routine = StartCoroutine(Play());
#else
            Status = "Input_System_required";
#endif
        }

#if ENABLE_INPUT_SYSTEM
        IEnumerator Play()
        {
            while (!runtime.Initialized) yield return null;
            if (runtime.Input.Paused) { Stop("refused_start_while_paused"); yield break; }
            if (waypoints == null || waypoints.Length == 0) waypoints = OverviewR01Route(runtime.routeMarkers);
            if (waypoints.Length == 0) { Stop("missing_authored_route_markers"); yield break; }
            // Only this explicitly requested automated test device runs while the
            // app loses focus. Normal keyboard/mouse focus policy remains unchanged.
            InputSystem.RegisterLayout("{\"name\":\"FarmValidationGamepadLayout\",\"extend\":\"Gamepad\",\"runInBackground\":\"enabled\"}");
            virtualGamepad = (Gamepad)InputSystem.AddDevice("FarmValidationGamepadLayout", "FarmValidationGamepad");
            virtualGamepad.MakeCurrent();
            Status = PerformanceMode ? "running_performance_route" : "running_simulated_input";
            runtime.Diagnostics.RecordEvent(PerformanceMode ? "performance_route_started_no_capture_no_state_exercise" : "automated_route_started_simulated_input_not_human_ui");
            CaptureRouteScreenshot("auto-route-start");
            if (!PerformanceMode && exerciseStageWardrobeAndQuality) yield return ExerciseStateChanges();
            do
            {
              for (int i = 0; i < waypoints.Length && Running; i++)
              {
                WaypointIndex = i;
                var waypoint = waypoints[i];
                float bestDistance = float.PositiveInfinity;
                float lastProgress = Time.unscaledTime;
                while (Running)
                {
                    if (PhysicalUserInput()) { Stop("stopped_by_human_input"); yield break; }
                    if (runtime.Input.Paused) { Stop("unexpected_pause_during_route"); yield break; }
                    Vector3 direction = waypoint.position - runtime.playerRoot.transform.position;
                    direction.y = 0;
                    float distance = direction.magnitude;
                    if (distance <= arrivalRadius) break;
                    if (distance < bestDistance - .025f) { bestDistance = distance; lastProgress = Time.unscaledTime; }
                    if (Time.unscaledTime - lastProgress > blockedSeconds)
                    {
                        CaptureRouteScreenshot("auto-route-blocked-" + i);
                        Stop("blocked_at_" + waypoint.name); yield break;
                    }
                    Vector3 local = Quaternion.Euler(0, -runtime.CameraRig.Yaw, 0) * direction.normalized;
                    Queue(new Vector2(local.x, local.z), Vector2.zero, runBetweenStops, false);
                    yield return null;
                }
                Queue(Vector2.zero, Vector2.zero, false, false);
                yield return new WaitForSecondsRealtime(.3f);
                runtime.Diagnostics.RecordEvent("automated_input_waypoint_" + waypoint.name);
                if (waypoint.screenshot) CaptureRouteScreenshot("auto-" + i + "-" + waypoint.name);
                if (waypoint.orbit) yield return OrbitOnce(waypoint.name);
                WaypointIndex = i + 1;
                SaveResult(Status);
              }
              if (!Running) yield break;
              CompletedLaps++;
              if (PerformanceMode)
              {
                  runtime.Diagnostics.RecordEvent("performance_route_lap_completed_" + CompletedLaps);
                  SaveResult("lap_completed_continuing_without_teleport");
                  // The authored route ends at the start area. Traverse that same route again;
                  // the small remaining distance to its first waypoint is also real input.
                  WaypointIndex = 0;
                  yield return null;
              }
              else
              {
                  CaptureRouteScreenshot("auto-route-complete");
                  yield return new WaitForSecondsRealtime(.2f);
                  Complete("completed_input_route_visual_and_manual_ui_pending");
              }
            } while (PerformanceMode && Running);
        }

        IEnumerator ExerciseStateChanges()
        {
            initialMature = runtime.MatureStage;
            initialMixed = runtime.MixedStage;
            initialQuality = runtime.QualityLabel == "手机" ? 0 : 1;
            initialWardrobe = runtime.wardrobe != null ? runtime.wardrobe.CurrentIndex : 0;
            restoreState = true;
            // Pause/resume goes through the same real Input System action as a gamepad Start press.
            automatedPausePending = true;
            Queue(Vector2.zero, Vector2.zero, false, true);
            yield return null; yield return null;
            Queue(Vector2.zero, Vector2.zero, false, false);
            yield return new WaitForSecondsRealtime(.3f);
            if (!runtime.Input.Paused || Time.timeScale != 0)
            { Stop("pause_input_check_failed"); yield break; }
            runtime.Diagnostics.RecordEvent("automated_start_button_pause_observed");
            Queue(Vector2.zero, Vector2.zero, false, true);
            yield return null; yield return null;
            Queue(Vector2.zero, Vector2.zero, false, false);
            yield return new WaitForSecondsRealtime(.3f);
            if (runtime.Input.Paused || Time.timeScale == 0)
            { Stop("resume_input_check_failed"); yield break; }
            automatedPausePending = false;
            foreach (bool mature in new[] { false, true })
            {
                runtime.SetMature(mature);
                yield return new WaitForSecondsRealtime(.35f);
                foreach (var crop in runtime.crops)
                    if (crop == null || crop.seedling == null || crop.mature == null || crop.seedling.activeSelf == mature || crop.mature.activeSelf != mature)
                    { Stop("stage_active_state_check_failed"); yield break; }
                CaptureRouteScreenshot(mature ? "auto-api-stage-mature" : "auto-api-stage-seedling");
            }
            if (runtime.wardrobe != null && runtime.wardrobe.IsConfigured)
            {
                for (int index = 0; index < 3; index++)
                {
                    if (!runtime.wardrobe.SetPreset(index)) { Stop("wardrobe_binding_check_failed"); yield break; }
                    yield return new WaitForSecondsRealtime(.3f);
                    if (!runtime.wardrobe.CurrentPresetIsApplied()) { Stop("wardrobe_LOD_material_application_failed"); yield break; }
                    runtime.Diagnostics.RecordEvent("automated_api_wardrobe_" + index + "_not_human_UI");
                    CaptureRouteScreenshot("auto-api-wardrobe-" + index);
                }
            }
            for (int quality = 0; quality < 2; quality++)
            {
                runtime.SetQuality(quality);
                yield return new WaitForSecondsRealtime(.3f);
                CaptureRouteScreenshot("auto-api-quality-" + quality);
            }
            RestoreState();
            runtime.Diagnostics.RecordEvent("automated_API_state_checks_finished_manual_UI_and_appearance_pending");
            yield return new WaitForSecondsRealtime(.3f);
        }

        IEnumerator OrbitOnce(string marker)
        {
            float total = 0, previous = runtime.CameraRig.Yaw, start = Time.unscaledTime;
            int capture = 1;
            while (Running && total < 360 && Time.unscaledTime - start < 10)
            {
                if (PhysicalUserInput()) { Stop("stopped_by_human_input"); yield break; }
                Queue(Vector2.zero, new Vector2(.75f, 0), false, false);
                yield return null;
                float yaw = runtime.CameraRig.Yaw;
                total += Mathf.Abs(Mathf.DeltaAngle(previous, yaw)); previous = yaw;
                if (total >= capture * 90)
                { CaptureRouteScreenshot("auto-orbit-" + marker + "-" + capture * 90); capture++; }
            }
            Queue(Vector2.zero, Vector2.zero, false, false);
            if (total < 355) { Stop("orbit_input_did_not_complete"); yield break; }
            runtime.Diagnostics.RecordEvent("automated_360_orbit_observed_" + marker);
        }

        void Queue(Vector2 move, Vector2 look, bool run, bool pause)
        {
            if (virtualGamepad == null || !virtualGamepad.added) return;
            uint buttons = (run ? 1u << (int)GamepadButton.LeftStick : 0u) | (pause ? 1u << (int)GamepadButton.Start : 0u);
            InputSystem.QueueStateEvent(virtualGamepad, new GamepadState { leftStick = move, rightStick = look, buttons = buttons });
        }
        static bool PhysicalUserInput()
        {
            var keyboard = Keyboard.current;
            if (keyboard != null && (keyboard.wKey.isPressed || keyboard.aKey.isPressed || keyboard.sKey.isPressed || keyboard.dKey.isPressed ||
                keyboard.upArrowKey.isPressed || keyboard.downArrowKey.isPressed || keyboard.leftArrowKey.isPressed || keyboard.rightArrowKey.isPressed || keyboard.escapeKey.wasPressedThisFrame)) return true;
            if (Mouse.current != null && (Mouse.current.leftButton.isPressed || Mouse.current.rightButton.isPressed)) return true;
            return Touchscreen.current != null && Touchscreen.current.primaryTouch.press.isPressed;
        }
#endif

        void CaptureRouteScreenshot(string label)
        {
            if (!PerformanceMode) runtime.Diagnostics.CaptureScreenshot(label);
        }

        [ContextMenu("Stop simulated-input route")]
        public void Stop() { Stop("stopped_explicitly"); }
        public void Stop(string reason)
        {
            if (!Running) return;
            Running = false; Status = reason;
            if (routine != null) StopCoroutine(routine);
            routine = null;
            // Save device focus/enabled state before removing the synthetic device.
            SaveResult(reason); ReleaseDevice(); RestoreState();
            if (runtime != null && runtime.Diagnostics != null) runtime.Diagnostics.RecordEvent("automated_route_" + reason);
        }
        void Complete(string reason)
        {
            Running = false; Status = reason; routine = null;
            SaveResult(reason); ReleaseDevice(); RestoreState();
            runtime.Diagnostics.SaveSnapshot(); runtime.Diagnostics.RecordEvent("automated_route_" + reason);
        }
        void ReleaseDevice()
        {
#if ENABLE_INPUT_SYSTEM
            if (virtualGamepad != null && virtualGamepad.added) InputSystem.RemoveDevice(virtualGamepad);
            virtualGamepad = null;
#endif
        }
        void RestoreState()
        {
            if (runtime == null || !runtime.Initialized) return;
            if (automatedPausePending && runtime.Input.Paused) runtime.TogglePause();
            automatedPausePending = false;
            if (!restoreState) return;
            restoreState = false;
            if(initialMixed)runtime.SetMixedStages();else runtime.SetMature(initialMature); runtime.SetQuality(initialQuality);
            if (runtime.wardrobe != null) runtime.wardrobe.SetPreset(initialWardrobe);
        }
        void SaveResult(string status)
        {
            if (runtime == null || runtime.Diagnostics == null || string.IsNullOrEmpty(runtime.Diagnostics.OutputDirectory)) return;
            var result = new Result { utc = DateTime.UtcNow.ToString("o"), status = status, revision = runtime.sceneRevision,
                mode = PerformanceMode ? "performance_simulated_input_loop_not_manual_acceptance" : "automated_input_events_not_manual_ui_or_device_acceptance",
                reachedWaypoints = WaypointIndex, plannedWaypoints = waypoints != null ? waypoints.Length : 0, completedLaps = CompletedLaps,
                performanceMode = PerformanceMode, loopingWithoutTeleport = PerformanceMode, screenshotsSuppressed = PerformanceMode,
                applicationFocused = Application.isFocused,
                // At application quit (O7 attempt-01: route stopped by focus loss) the player can be destroyed first.
                waypoints = waypoints, finalPosition = runtime.playerRoot != null ? runtime.playerRoot.transform.position : Vector3.zero };
#if ENABLE_INPUT_SYSTEM
            result.virtualGamepadPresent = virtualGamepad != null && virtualGamepad.added;
            if (result.virtualGamepadPresent)
            {
                result.virtualGamepadEnabled = virtualGamepad.enabled;
                result.virtualGamepadCanRunInBackground = virtualGamepad.canRunInBackground;
            }
#endif
            File.WriteAllText(Path.Combine(runtime.Diagnostics.OutputDirectory, PerformanceMode ? "performance-route.json" : "automated-route.json"), JsonUtility.ToJson(result, true));
        }
        void OnDisable() { Stop("component_disabled"); ReleaseDevice(); }
        void OnDestroy() { ReleaseDevice(); }

        static FarmRouteWaypoint Point(string name, float x, float z, bool screenshot = false, bool orbit = false)
            => new FarmRouteWaypoint { name = name, position = new Vector3(x, 0, z), screenshot = screenshot, orbit = orbit };
        public static FarmRouteWaypoint[] OverviewR01Route(FarmRouteMarker[] markers)
        {
            // Key locations always come from the authored scene, including the actual dock elevation in plan space.
            // Intermediate detours are specific to overview r01 and still require collision-driven verification.
            if (markers == null || markers.Length < 9) return Array.Empty<FarmRouteWaypoint>();
            for (int i = 0; i < 9; i++) if (markers[i] == null) return Array.Empty<FarmRouteWaypoint>();
            var house = markers[0].position; var field = markers[1].position; var gate = markers[2].position;
            var trough = markers[3].position; var shore = markers[4].position; var dock = markers[5].position;
            var fish = markers[6].position; var back = markers[7].position; var end = markers[8].position;
            return new[]
            {
                Point("house-front",house.x,house.z,true), Point("field-approach",-5.5f,house.z), Point("fields",field.x,field.z,true),
                Point("field-lane",-5.2f,field.z), Point("south-west-path",-5.2f,gate.z-1), Point("gate-approach",gate.x,gate.z-1),
                Point("pasture-gate",gate.x,gate.z,true), Point("inside-gate",gate.x,gate.z+1.8f), Point("trough",trough.x,trough.z,true),
                // Clear the outward-swinging gate leaf before turning east.
                Point("exit-pasture",gate.x,gate.z+1.8f), Point("outside-gate",gate.x,gate.z-1f), Point("east-path",6.5f,gate.z-1f),
                Point("shore-approach",6.5f,-3.8f), Point("shore",shore.x,shore.z,true), Point("dock",dock.x,dock.z,true,true),
                Point("leave-dock",shore.x,shore.z), Point("fish-path",6.5f,-4.3f), Point("fish-front-approach",6.5f,fish.z),
                Point("fish-stall",fish.x,fish.z,true), Point("fish-front-exit",12,fish.z),
                Point("pond-east-approach",16.1f,-4.5f), Point("pond-east-path",16.1f,7.2f),
                Point("north-landscape",11,8.2f), Point("north-house-approach",4.5f,8.4f), Point("house-back-approach",back.x,8.4f),
                Point("house-back",back.x,back.z,true,true), Point("house-back-exit",back.x,8.4f),
                Point("house-west-back",-5.5f,8.4f), Point("house-west-path",-5.5f,5.4f),
                Point("house-front-return",-3.6f,end.z), Point("returned",end.x,end.z,true)
            };
        }
    }
}
