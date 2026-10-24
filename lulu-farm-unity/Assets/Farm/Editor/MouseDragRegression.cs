// Copy to Assets/Farm/Editor/MouseDragRegression.cs while Unity is idle.
// Fresh batch CLI: -batchmode -executeMethod LuluFarm.Editor.MouseDragRegression.RunBatch
// Do not add -quit: the asynchronous test writes evidence then exits 0/1 itself.
// Existing Play Mode: Farm/Diagnostics/Run mouse drag input regression or Run().
// Real queued InputSystem MouseState events + a real Canvas/GraphicRaycaster, no screenshots.
// Automated regression is not human CUA/native mouse acceptance or a performance measurement.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.UI;

namespace LuluFarm.Editor
{
    public static class MouseDragRegression
    {
        const string BatchKey = "LuluFarm.MouseDragRegression.BatchPending";
        [MenuItem("Farm/Diagnostics/Run mouse drag input regression")]
        public static void RunMenu() { Debug.Log(Run()); }
        public static string Run() => Start(false);
        static string Start(bool exitAfter)
        {
            if (!EditorApplication.isPlaying || EditorApplication.isCompiling)
                throw new InvalidOperationException("Run after compilation, in Play Mode.");
            if (UnityEngine.Object.FindFirstObjectByType<MouseDragRegressionRunner>() != null)
                throw new InvalidOperationException("Mouse regression already running.");
            foreach (var active in UnityEngine.Object.FindObjectsByType<FarmRoutePlayback>(FindObjectsSortMode.None))
                if (active.Running) throw new InvalidOperationException("Stop automated routes before this regression.");
            foreach (var active in UnityEngine.Object.FindObjectsByType<FarmPerformanceSession>(FindObjectsSortMode.None))
                if (active.Running) throw new InvalidOperationException("Do not disturb a performance session.");
            foreach (var active in UnityEngine.Object.FindObjectsByType<FarmFrameRecorder>(FindObjectsSortMode.None))
                if (active.IsRecording) throw new InvalidOperationException("Stop recording before this regression.");
            var owner = new GameObject("TemporaryMouseDragRegression");
            var runner = owner.AddComponent<MouseDragRegressionRunner>();
            runner.exitAfter = exitAfter;
            return "Started real input regression; output: " + runner.DirectoryPath;
        }
        public static void RunBatch()
        {
            if (!Application.isBatchMode) throw new InvalidOperationException("RunBatch requires a fresh batch editor process.");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            SessionState.SetBool(BatchKey, true);
            ResumePendingBatch();
            EditorApplication.EnterPlaymode();
        }
        [InitializeOnLoadMethod]
        static void ResumePendingBatch()
        {
            if (!SessionState.GetBool(BatchKey, false)) return;
            EditorApplication.playModeStateChanged -= OnBatchPlayState;
            EditorApplication.playModeStateChanged += OnBatchPlayState;
        }
        static void OnBatchPlayState(PlayModeStateChange state)
        {
            if (state != PlayModeStateChange.EnteredPlayMode || !SessionState.GetBool(BatchKey, false)) return;
            SessionState.SetBool(BatchKey, false);
            EditorApplication.playModeStateChanged -= OnBatchPlayState;
            EditorApplication.delayCall += () =>
            {
                try { Debug.Log(Start(true)); }
                catch (Exception error) { Debug.LogException(error); EditorApplication.Exit(1); }
            };
        }
    }

    public sealed class MouseDragRegressionRunner : MonoBehaviour
    {
        [Serializable] sealed class CheckRecord
        {
            public string name, eventDelivery, observedInputUpdateType;
            public Vector2 expectedLookDegrees, observedLookDegrees;
            public bool passed, uiBlocked;
        }
        [Serializable] sealed class Report
        {
            public string utc, unityVersion, inputSystemPackageVersion, status, exception;
            public string scope = "Executed virtual Mouse InputSystem events plus actual GraphicRaycaster; not manual mouse/GUI acceptance";
            public string manualNativeDrag = "separate_native_app_evidence_required", performance = "invalid_regression_input_and_allocations";
            public string inputDispatch = "explicit InputSystem.Update(InputUpdateType.Dynamic) via installed internal overload; no global focus/update-mode changes";
            public string priorZeroResultInterpretation = "r06d 20261023-014812-029 used no-argument InputSystem.Update in an unfocused batch Editor. InputManager.defaultUpdateType selected Editor; InputActionState suppresses gameplay action notifications in Editor updates. Device position/UI polling could change while gameplay Look stayed zero. Those rows do not verify production drag behavior; earlier fixture failures had no checks. Historical files are retained.";
            public bool cleanupComplete, eventMergingDisabledBefore, eventMergingDisabledDuring, eventMergingDisabledAfter, runtimeSettingRestored;
            public bool multipleRouterLeasePreserved, lastRouterLeaseRestored;
            public int screenWidth, screenHeight, imageDepth, settlingFrames;
            public Rect canvasPixels;
            public Vector2 uiCentre, dragStart, dragEnd;
            public bool imageCulled, uiCentreHits, dragStartHits, dragEndHits, virtualMouseEnabled;
            public string virtualMouseType;
            public bool virtualMouseRequiredExplicitEnable;
            public CheckRecord[] checks;
        }
        public bool exitAfter;
        public string DirectoryPath { get; private set; }
        readonly List<CheckRecord> checks = new List<CheckRecord>();
        readonly List<FarmInputRouter> routers = new List<FarmInputRouter>();
        readonly List<GraphicRaycaster> raycasters = new List<GraphicRaycaster>();
        Report report;
        Mouse previousMouse, mouse;
        GameObject inputOwner, canvasOwner, eventOwner, cameraOwner;
        FarmInputRouter input;
        Canvas canvas;
        Image image;
        RectTransform rect;
        MethodInfo update, focus, dynamicInputUpdate;
        bool cleaned, testLayoutRegistered;
        const string TestMouseLayout = "FarmMouseRegressionBackgroundLayout";

        void Awake() { DirectoryPath = Path.Combine("Evidence", "mouse-drag-regression-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff")); }
        IEnumerator Start()
        {
            var package = UnityEditor.PackageManager.PackageInfo.FindForAssembly(typeof(InputAction).Assembly);
            report = new Report { utc = DateTime.UtcNow.ToString("o"), unityVersion = Application.unityVersion,
                inputSystemPackageVersion = package != null ? package.version : "unavailable",
                eventMergingDisabledBefore = InputSystem.settings.disableRedundantEventsMerging };
            bool setup = false;
            try { Setup(); setup = true; }
            catch (Exception error) { Fail(error); }
            if (setup)
            {
                // GraphicRaycaster rejects graphic.depth == -1; allow actual Canvas frame processing.
                // EndOfFrame is intentionally not used because batch Editor can omit that yield phase.
                for (int i = 0; i < 30; i++)
                {
                    yield return null;
                    Canvas.ForceUpdateCanvases();
                    report.settlingFrames = i + 1;
                    if (i >= 2 && image.depth >= 0 && Screen.width > 32 && Screen.height > 32) break;
                }
                try { Exercise(); }
                catch (Exception error) { Fail(error); }
            }
            Cleanup();
            report.checks = checks.ToArray();
            Directory.CreateDirectory(DirectoryPath);
            File.WriteAllText(Path.Combine(DirectoryPath, "review.json"), JsonUtility.ToJson(report, true));
            Debug.Log("Mouse drag regression " + report.status + ": " + DirectoryPath);
            bool passed = report.status != null && report.status.StartsWith("passed_") && report.runtimeSettingRestored;
            if (exitAfter) EditorApplication.Exit(passed ? 0 : 1);
            else Destroy(gameObject);
        }
        void Fail(Exception error) { report.status = "failed"; report.exception = error.ToString(); }
        void Setup()
        {
            if (Gamepad.current != null && Gamepad.current.rightStick.ReadValue().sqrMagnitude > .01f)
                throw new InvalidOperationException("Release gamepad look stick before this regression.");
            update = typeof(FarmInputRouter).GetMethod("Update", BindingFlags.NonPublic | BindingFlags.Instance);
            focus = typeof(FarmInputRouter).GetMethod("OnApplicationFocus", BindingFlags.NonPublic | BindingFlags.Instance);
            dynamicInputUpdate = typeof(InputSystem).GetMethod("Update", BindingFlags.NonPublic | BindingFlags.Static,
                null, new[] { typeof(InputUpdateType) }, null);
            if (dynamicInputUpdate == null)
                throw new NotSupportedException("Installed Input System has no internal Update(InputUpdateType) overload; no fallback to Editor dispatch.");
            previousMouse = Mouse.current;
            foreach (var diagnostics in FindObjectsByType<FarmRuntimeDiagnostics>(FindObjectsSortMode.None))
                diagnostics.NotifyCaptureOverhead("virtual_mouse_regression_not_performance");
            foreach (var existing in FindObjectsByType<FarmInputRouter>(FindObjectsSortMode.None))
                if (existing.enabled) { routers.Add(existing); existing.enabled = false; }
            bool mergingBeforeFixture = InputSystem.settings.disableRedundantEventsMerging;
            foreach (var existing in FindObjectsByType<GraphicRaycaster>(FindObjectsSortMode.None))
                if (existing.enabled) { raycasters.Add(existing); existing.enabled = false; }
            if (EventSystem.current == null) eventOwner = new GameObject("TemporaryMouseRegressionEventSystem", typeof(EventSystem));
            if (Camera.allCamerasCount == 0)
            {
                cameraOwner = new GameObject("TemporaryMouseRegressionCamera", typeof(Camera));
                cameraOwner.GetComponent<Camera>().clearFlags = CameraClearFlags.SolidColor;
            }
            canvasOwner = new GameObject("TemporaryMouseRegressionUI", typeof(RectTransform), typeof(Canvas), typeof(GraphicRaycaster));
            canvas = canvasOwner.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = short.MaxValue;
            var panel = new GameObject("UIOwnsGesture", typeof(RectTransform), typeof(Image));
            panel.transform.SetParent(canvasOwner.transform, false);
            rect = panel.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(.42f, .40f); rect.anchorMax = new Vector2(.58f, .60f);
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            image = panel.GetComponent<Image>(); image.raycastTarget = true;
            inputOwner = new GameObject("TemporaryMouseDragInputRouter");
            input = inputOwner.AddComponent<FarmInputRouter>(); input.mouseSensitivity = .18f;
            report.eventMergingDisabledDuring = InputSystem.settings.disableRedundantEventsMerging;
            if (!report.eventMergingDisabledDuring) throw new InvalidOperationException("Mouse event preservation was not enabled.");
            var leaseOwner = new GameObject("SecondMouseEventLease"); leaseOwner.transform.SetParent(inputOwner.transform);
            var secondRouter = leaseOwner.AddComponent<FarmInputRouter>();
            input.enabled = false;
            report.multipleRouterLeasePreserved = InputSystem.settings.disableRedundantEventsMerging;
            secondRouter.enabled = false;
            report.lastRouterLeaseRestored = InputSystem.settings.disableRedundantEventsMerging == mergingBeforeFixture;
            input.enabled = true;
            if (!report.multipleRouterLeasePreserved || !report.lastRouterLeaseRestored)
                throw new InvalidOperationException("Runtime event merging lease did not preserve/restore correctly.");
            // Only this explicit test device runs without a focused batch Game View.
            // Native mouse/keyboard focus rules and global InputSettings stay unchanged.
            InputSystem.RegisterLayout("{\"name\":\"" + TestMouseLayout + "\",\"extend\":\"Mouse\",\"runInBackground\":\"enabled\"}");
            testLayoutRegistered = true;
            mouse = (Mouse)InputSystem.AddDevice(TestMouseLayout, "FarmMouseRegression"); mouse.MakeCurrent();
        }
        MouseState State(Vector2 position, bool held, MouseButton button = MouseButton.Left)
        {
            var state = new MouseState { position = position };
            return held ? state.WithButton(button) : state;
        }
        Vector2 Feed(params MouseState[] states)
        {
            foreach (var state in states) InputSystem.QueueStateEvent(mouse, state);
            // No-argument Update chooses Editor when batch Game View lacks focus. That
            // buffer does not notify gameplay actions, so request only this explicit test update.
            dynamicInputUpdate.Invoke(null, new object[] { InputUpdateType.Dynamic });
            update.Invoke(input, null);
            return input.LookDegrees;
        }
        void Check(string name, Vector2 expected, string delivery, params MouseState[] states)
        {
            Vector2 observed = Feed(states);
            checks.Add(new CheckRecord { name = name, eventDelivery = delivery, expectedLookDegrees = expected,
                observedLookDegrees = observed, observedInputUpdateType = InputState.currentUpdateType.ToString(), passed = (observed - expected).sqrMagnitude < .0001f, uiBlocked = input.UIBlocked });
        }
        void Exercise()
        {
            report.screenWidth = Screen.width; report.screenHeight = Screen.height;
            report.canvasPixels = canvas.pixelRect; report.imageDepth = image.depth; report.imageCulled = image.canvasRenderer.cull;
            Vector2 centre = RectTransformUtility.WorldToScreenPoint(null, rect.position);
            Vector2 a = new Vector2(Screen.width * .20f, Screen.height * .75f);
            Vector2 b = new Vector2(Screen.width * .35f, Screen.height * .80f);
            report.uiCentre = centre; report.dragStart = a; report.dragEnd = b;
            report.uiCentreHits = input.IsOverUI(centre); report.dragStartHits = input.IsOverUI(a); report.dragEndHits = input.IsOverUI(b);
            // Editor Game View pointer policy can override even a background-capable layout.
            // Enable only our synthetic device for explicit test injection, never a real device.
            report.virtualMouseRequiredExplicitEnable = !mouse.enabled;
            if (!mouse.enabled) InputSystem.EnableDevice(mouse);
            report.virtualMouseEnabled = mouse.enabled; report.virtualMouseType = mouse.GetType().FullName;
            if (!report.uiCentreHits || report.dragStartHits || report.dragEndHits)
                throw new InvalidOperationException("Actual Canvas fixture must hit centre only; inspect recorded Screen/Canvas/depth/point values.");
            if (!mouse.enabled) throw new InvalidOperationException("Virtual mouse disabled by current Editor focus policy; input checks were not run.");
            Feed(State(a * .5f, false));
            Check("press_origin_does_not_rotate", Vector2.zero, "position and press share one state event", State(a, true));
            Check("normal_drag_across_updates", (b-a)*.18f, "held movement next input update", State(b, true));
            Check("normal_release_no_extra_rotation", Vector2.zero, "release next update", State(b, false));
            Check("complete_fast_drag_in_one_update", (b-a)*.18f, "press + move + release before one InputSystem.Update", State(a, true), State(b, true), State(b, false));
            Check("release_event_carries_final_movement", (b-a)*.18f, "press then changed position and release", State(a, true), State(b, false));
            Check("right_button_same_frame_drag", (b-a)*.18f, "right press + move + release in one update", State(a, true, MouseButton.Right), State(b, true, MouseButton.Right), State(b, false));
            Check("warp_to_click_origin_is_not_drag", Vector2.zero, "unpressed move then distant press/release", State(b, false), State(a, true), State(a, false));
            Check("ui_origin_never_takes_camera_ownership", Vector2.zero, "actual Image press, move out, release in one update", State(centre, true), State(a, true), State(b, false));
            Feed(State(a, true));
            Check("entering_ui_does_not_rotate", Vector2.zero, "owned drag reaches Image", State(centre, true));
            Check("leaving_ui_has_no_jump", Vector2.zero, "owned drag leaves Image", State(a, true));
            Check("outside_ui_drag_resumes_from_new_point", (b-a)*.18f, "next fully outside segment", State(b, true));
            Feed(State(b, false));
            input.SetPaused(true);
            Check("paused_drag_does_not_rotate", Vector2.zero, "press + move + release while paused", State(a, true), State(b, true), State(b, false));
            input.SetPaused(false);
            Check("fresh_drag_after_resume", (b-a)*.18f, "fresh press after resume", State(a, true), State(b, true), State(b, false));
            Feed(State(a, true)); focus.Invoke(input, new object[] { false });
            Check("focus_loss_requires_new_press", Vector2.zero, "held move after clearing focus", State(b, true), State(b, false));
            focus.Invoke(input, new object[] { true });
            Check("fresh_drag_after_focus_return", (b-a)*.18f, "fresh press after focus return", State(a, true), State(b, true), State(b, false));
            report.status = "passed_automated_input_regression_manual_native_drag_pending";
            foreach (var check in checks) if (!check.passed) report.status = "failed";
        }
        void Cleanup()
        {
            if (cleaned) return; cleaned = true;
            if (inputOwner != null) DestroyImmediate(inputOwner);
            if (canvasOwner != null) DestroyImmediate(canvasOwner);
            if (eventOwner != null) DestroyImmediate(eventOwner);
            if (cameraOwner != null) DestroyImmediate(cameraOwner);
            if (mouse != null && mouse.added) InputSystem.RemoveDevice(mouse);
            if (testLayoutRegistered) InputSystem.RemoveLayout(TestMouseLayout);
            if (previousMouse != null && previousMouse.added) previousMouse.MakeCurrent();
            foreach (var raycaster in raycasters) if (raycaster != null) raycaster.enabled = true;
            foreach (var router in routers) if (router != null) router.enabled = true;
            if (report == null) return;
            report.cleanupComplete = true;
            report.eventMergingDisabledAfter = InputSystem.settings.disableRedundantEventsMerging;
            report.runtimeSettingRestored = report.eventMergingDisabledAfter == report.eventMergingDisabledBefore;
            if (!report.runtimeSettingRestored) report.status = "failed_runtime_setting_not_restored";
        }
        void OnDestroy() { Cleanup(); }
    }
}
