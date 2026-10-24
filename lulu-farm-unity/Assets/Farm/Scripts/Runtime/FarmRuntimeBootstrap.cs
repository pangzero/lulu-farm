using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif

namespace LuluFarm
{
    [Serializable]
    public sealed class FarmRouteMarker
    {
        public string name;
        public Vector3 position;
        public float radius = 1.2f;
    }

    [DefaultExecutionOrder(-200)]
    public sealed class FarmRuntimeBootstrap : MonoBehaviour
    {
        public GameObject playerRoot;
        public Transform visualRoot;
        public Camera mainCamera;
        public Bounds worldBounds = new Bounds(Vector3.zero, new Vector3(60, 30, 50));
        public FarmCropStage[] crops = Array.Empty<FarmCropStage>();
        public FarmWardrobe wardrobe;
        public FarmRouteMarker[] routeMarkers = Array.Empty<FarmRouteMarker>();
        public string sceneRevision = "integration-r06";
        public string assetRegistryRevision = "unassigned";
        public Font uiFont;
        public RenderPipelineAsset mobilePipeline, desktopPipeline;
        public bool showTouchControlsOnDesktop;
        public AnimationClip idleClip, walkClip, runClip;
        public FarmInputRouter Input { get; private set; }
        public FarmPlayerController Player { get; private set; }
        public FarmThirdPersonCamera CameraRig { get; private set; }
        public FarmRuntimeDiagnostics Diagnostics { get; private set; }
        public FarmFrameRecorder Recorder { get; private set; }
        public FarmHUD HUD { get; private set; }
        public string QualityLabel { get; private set; } = "电脑";
        public bool MatureStage { get; private set; } = true;
        public bool MixedStage { get; private set; }
        float commandLineQuitAfter;
        public bool Initialized { get; private set; }
        float priorTimescale = 1f;

        public static FarmRuntimeBootstrap Attach(GameObject player, Transform visual, Camera camera, Bounds bounds)
        {
            var host = new GameObject("FarmRuntime");
            var bootstrap = host.AddComponent<FarmRuntimeBootstrap>();
            bootstrap.playerRoot = player;
            bootstrap.visualRoot = visual;
            bootstrap.mainCamera = camera;
            bootstrap.worldBounds = bounds;
            EnsureCharacterCapsule(player);
            var rig = camera.GetComponent<FarmThirdPersonCamera>();
            if (rig == null) rig = camera.gameObject.AddComponent<FarmThirdPersonCamera>();
            rig.target = player.transform;
            rig.headingTarget = visual;
            rig.outputCamera = camera;
            rig.ConfigureCinemachine(host.transform);
            // Start() binds after the scene builder has assigned clips, stages and wardrobe.
            return bootstrap;
        }

        public static CharacterController EnsureCharacterCapsule(GameObject player)
        {
            if (player == null) throw new ArgumentNullException(nameof(player));
            var capsule = player.GetComponent<CharacterController>();
            if (capsule != null) return capsule;
            capsule = player.AddComponent<CharacterController>();
            capsule.height = 1.14f; capsule.radius = .28f;
            capsule.center = new Vector3(0, .57f, 0);
            capsule.stepOffset = .17f; capsule.slopeLimit = 42f;
            capsule.skinWidth = .025f; capsule.minMoveDistance = 0;
            return capsule;
        }

        void Start() { Initialize(); }
        public void Initialize()
        {
            if (Initialized || playerRoot == null || mainCamera == null) return;
            Initialized = true;
            if (visualRoot == null) visualRoot = playerRoot.transform;
            if (EventSystem.current == null)
            {
                var system = new GameObject("FarmEventSystem", typeof(EventSystem));
#if ENABLE_INPUT_SYSTEM
                var module = system.AddComponent<InputSystemUIInputModule>();
                module.AssignDefaultActions();
#else
                system.AddComponent<StandaloneInputModule>();
#endif
                system.transform.SetParent(transform);
            }
            Input = GetComponent<FarmInputRouter>();
            if (Input == null) Input = gameObject.AddComponent<FarmInputRouter>();
            Input.forceTouchControls = showTouchControlsOnDesktop;
            EnsureCharacterCapsule(playerRoot);
            var animation = visualRoot.GetComponent<FarmAnimationBridge>();
            if (animation == null) animation = visualRoot.gameObject.AddComponent<FarmAnimationBridge>();
            if (idleClip != null) animation.idleClip = idleClip;
            if (walkClip != null) animation.walkClip = walkClip;
            if (runClip != null) animation.runClip = runClip;
            Player = playerRoot.GetComponent<FarmPlayerController>();
            if (Player == null) Player = playerRoot.AddComponent<FarmPlayerController>();
            CameraRig = mainCamera.GetComponent<FarmThirdPersonCamera>();
            if (CameraRig == null) CameraRig = mainCamera.gameObject.AddComponent<FarmThirdPersonCamera>();
            CameraRig.target = playerRoot.transform;
            CameraRig.headingTarget = visualRoot;
            CameraRig.outputCamera = mainCamera;
            CameraRig.input = Input;
            CameraRig.ConfigureCinemachine(transform);
            // Layer 28 is reserved for camera-only tree crowns; the capsule passes beneath them.
            Physics.IgnoreLayerCollision(0, 28, true);
            if (playerRoot.layer != 0) Physics.IgnoreLayerCollision(playerRoot.layer, 28, true);
            CameraRig.obstructionLayers = CameraRig.obstructionLayers.value | (1 << 28);
            Player.input = Input; Player.cameraRig = CameraRig;
            Player.visualRoot = visualRoot; Player.animationBridge = animation; Player.worldBounds = worldBounds;
            if (wardrobe == null) wardrobe = playerRoot.GetComponentInChildren<FarmWardrobe>(true);
            if (crops == null || crops.Length == 0) crops = FindObjectsByType<FarmCropStage>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            Diagnostics = GetComponent<FarmRuntimeDiagnostics>();
            if (Diagnostics == null) Diagnostics = gameObject.AddComponent<FarmRuntimeDiagnostics>();
            Diagnostics.runtime = this;
            Recorder = GetComponent<FarmFrameRecorder>();
            if (Recorder == null) Recorder = gameObject.AddComponent<FarmFrameRecorder>();
            Recorder.runtime = this;
            HUD = GetComponent<FarmHUD>();
            if (HUD == null) HUD = gameObject.AddComponent<FarmHUD>();
            HUD.Build(this);
            SetQuality(Application.isMobilePlatform ? 0 : 1);
            if(sceneRevision.StartsWith("integration"))SetMixedStages();else SetMature(true);
            CameraRig.SnapToTarget();
            Diagnostics.BeginSession();
            var args=Environment.GetCommandLineArgs();
            for(int i=0;i<args.Length-1;i++)if(args[i]=="--farm-quit-after")float.TryParse(args[i+1],System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out commandLineQuitAfter);
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--farm-record-frames") >= 0) Recorder.BeginRecording();
            if (Array.IndexOf(args,"--farm-performance-route") >= 0) FarmPerformanceSession.StartFor(this);
            else if (Array.IndexOf(args, "--farm-route") >= 0) FarmRoutePlayback.StartFor(this);
        }

        void Update()
        {
            if (Input != null && Input.PauseRequested) TogglePause();
            if(commandLineQuitAfter>0&&Time.realtimeSinceStartup>=commandLineQuitAfter)
            {
                commandLineQuitAfter=0; Recorder?.StopRecording("command_line_session_finished");Diagnostics?.SaveSnapshot();Application.Quit();
            }
        }

        public void TogglePause()
        {
            if (Input == null) return;
            bool paused = !Input.Paused;
            if (paused) { priorTimescale = Time.timeScale; Time.timeScale = 0; }
            else Time.timeScale = priorTimescale;
            Input.SetPaused(paused);
            Diagnostics?.RecordEvent(paused ? "pause" : "resume");
        }

        public void SetMature(bool mature)
        {
            MixedStage=false;
            MatureStage = mature;
            if (crops != null) foreach (var crop in crops) if (crop != null) crop.SetMature(mature);
            Diagnostics?.RecordEvent(mature ? "crop_stage_mature" : "crop_stage_seedling");
        }

        public void SetMixedStages()
        {
            MixedStage=true;MatureStage=true;
            if(crops!=null)for(int i=0;i<crops.Length;i++)if(crops[i]!=null)crops[i].SetMature(i%4!=1&&i%5!=3);
            Diagnostics?.RecordEvent("crop_stage_reference_mixed_planting");
        }

        public void SetQuality(int index)
        {
            bool mobile = index == 0;
            string desired = mobile ? "Mobile" : "Desktop";
            int found = Array.FindIndex(QualitySettings.names, name => name.IndexOf(desired, StringComparison.OrdinalIgnoreCase) >= 0);
            if (found >= 0) QualitySettings.SetQualityLevel(found, true);
            RenderPipelineAsset pipeline = mobile ? mobilePipeline : desktopPipeline;
            if (pipeline != null) QualitySettings.renderPipeline = pipeline;
            QualitySettings.vSyncCount = mobile ? 0 : 1;
            Application.targetFrameRate = mobile ? 30 : 60;
            QualitySettings.lodBias = mobile ? .75f : 1.4f;
            QualitySettings.maximumLODLevel = 0;
            // Preserve the reviewed skin influences and platform texture caps.
            // Unity's default Low presets otherwise reduce these independently.
            QualitySettings.skinWeights = SkinWeights.FourBones;
            QualitySettings.globalTextureMipmapLimit = 0;
            QualitySettings.shadowDistance = mobile ? 22 : 38;
            QualitySettings.anisotropicFiltering = mobile ? AnisotropicFiltering.Disable : AnisotropicFiltering.Enable;
            QualityLabel = mobile ? "手机" : "电脑";
            Diagnostics?.RecordEvent("quality_" + desired);
        }

        void OnDestroy() { if (Input != null && Input.Paused) Time.timeScale = priorTimescale; }
    }
}
