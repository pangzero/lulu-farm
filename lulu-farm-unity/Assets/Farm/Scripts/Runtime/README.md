# Lulu Farm runtime integration

Status as of 2026-10-23: Personal activation, actual Unity compilation/import, FarmWorld generation and macOS development builds have executed. The built player is under actual operation and delivery review. Final route, visual and clean performance conclusions belong to their recorded sessions; Android hardware is deferred by the user, and Windows/iOS remain unverified. Historical pre-activation logs do not describe the current editor state.

## Scene builder API

```csharp
using LuluFarm;

var runtime = FarmRuntimeBootstrap.Attach(playerRoot, visualRoot, mainCamera, worldBounds);
runtime.idleClip = realIdle;
runtime.walkClip = realWalk;
runtime.runClip = realRun;
runtime.crops = cropStageComponents;
runtime.wardrobe = wardrobeComponent;
runtime.routeMarkers = markers;
runtime.mobilePipeline = mobileURPAsset;
runtime.desktopPipeline = desktopURPAsset;
runtime.uiFont = bundledChineseFont;
runtime.sceneRevision = "integration-r01";
runtime.assetRegistryRevision = "<actual registry hash or version>";
```

`Attach` is safe for an Editor scene builder: it creates a serialized bootstrap object and the Cinemachine rig. Play-mode `Start` configures input, CharacterController, animation bridge, camera, UI and evidence recording after the builder has assigned references. Do not call `Initialize` during scene authoring. Do not place another active controller or camera driver on these objects.

- `playerRoot`: unscaled (+Y up, scale 1) collision/controller root, placed at feet on walkable ground. No mesh collider on Lulu.
- `visualRoot`: Lulu visual orientation container under `playerRoot`; its forward must be +Z. Animation skeleton and renderers are descendants. It may hold the world-scale conversion, while `playerRoot` remains scale 1.
- Camera: perspective, FOV 52; default pitch 35, distance 5.1. The independent yaw/pitch camera supports 15–55 pitch, 2.5–8.6 user-requested distance, 360 yaw and spherecast obstacle retraction. Collision can temporarily reduce actual distance below the requested range. No overhead gameplay mode exists.
- Use a capsule 1.14 high, radius .28, center .57 above feet as the initial height-1.2 Lulu envelope. Inspector customization is supported; play-mode contact must be checked.
- Supplied locomotion derivative stride rates are matched with walk speed `.5471864` and run `1.2777705` units/s. These are declared clip-derived initial values, not a claim that sliding is visually accepted.
- The camera uses the locked Cinemachine 3.1.5 package: a `CinemachineCamera` with `CinemachineThirdPersonFollow` tracks a separate `LuluCameraOrbitTarget`; `CinemachineBrain` alone applies MainCamera transforms. `FarmThirdPersonCamera.ConfigureCinemachine(owner)` is called by `Attach` and is safe to repeat. Input updates the independent target, while the explicit per-collider solver supplies `CameraDistance`. Brain uses ManualUpdate exactly once in LateUpdate. The ThirdPersonFollow body has zero shoulder/arm offset and zero additional damping because target movement/recovery is already smoothed; its built-in generic collision solver is disabled to avoid conflicting with selective tree/house fades. Actual Unity compilation and player movement have now been exercised; static configuration and live `cinemachineLive` observations remain distinct from full-route and visual acceptance.

## Package / project requirements

- Locked editor: Unity 6000.3.16f1. Manifest, lock file and resolved `Library/PackageCache/*/package.json` were checked on 2026-10-23: URP 17.3.0, Cinemachine 3.1.5, Input System 1.14.2, glTFast 6.20.0, Unity UI 2.0.0 and Test Framework 1.6.0 agree; all ten directly declared built-in modules are 1.0.0. Set Active Input Handling to Input System or Both so `ENABLE_INPUT_SYSTEM` is defined. A legacy keyboard/mouse fallback exists, but Android multi-touch requires Input System.
- URP mobile/desktop pipeline assets should be assigned to the bootstrap. Setting a display quality name alone does not supply pipeline settings. The runtime switches the shared pipeline reference and sets target fps / LOD bias / shadow distance, without duplicating materials or pipelines.
- Bundle a Chinese-capable font and assign `uiFont`, or place it at `Resources/FarmChinese`. System font fallbacks are provided for development and are unverified on the target Android device.
- Game view and built player need visible camera rendering. Diagnostics do not invent frame timing when the platform cannot report it.

## Input and UI

- WASD / arrow keys: camera-relative movement; Shift: run; either mouse button held over scene: orbit; scroll: zoom; R: recenter; Escape: pause.
- Gamepad: left stick move, press left stick run, right stick orbit, Start pause.
- Android: left joystick, right scene area drag, pinch with two eligible right-area fingers, walk/run toggle and near/far buttons. Touch ownership is captured on finger down. A touch beginning on UI never becomes a camera drag later.
- UI raycasting excludes scene movement/look from buttons; the joystick intentionally controls movement. Pause also freezes animation and world time, while retaining UI input.
- Main HUD: recenter, pause, inspection toggle. Inspection contains quality, global seedling/mature stage, same-cut shorts preset, screenshot, runtime evidence save and explicit return-to-spawn.

## Crop and wardrobe registration

Every crop instance uses `FarmCropStage`:

```csharp
crop.assetId = "C01";
crop.species = "卷心菜";
crop.seedling = seedlingObject;
crop.mature = matureObject;
crop.seedlingSourceVersion = "meshy-toon-r02";
crop.matureSourceVersion = "unity-game-r01";
```

Its two objects share the same rooted world position; only one is active. Meshes/materials must be shared between repeated prefab instances. No growing state or source regeneration is performed here.

`FarmWardrobe.bindings` contains `FarmWardrobeBinding` entries, each with a target `Renderer` and `original` / `blueStars` / `watermelon` shared-material arrays. Each preset must match the renderer's material slot count. Preset changes validate all entries before applying any. The shader/material must explicitly use FabricUV (UV1) where required; the runtime does not rewrite UVs or infer texture channels.

Optional `FarmCameraOccluder` goes only on designated blocking surfaces. It needs a renderer and separate complete opaque/faded shared-material arrays. Without deliberately prepared fade materials the camera retracts and preserves imported materials. Never assign all imported objects a global transparent material as a substitute.

The Editor helper `LuluFarm.Editor.FarmOcclusionSetup.Configure(root, tree)` now prepares this opt-in setup. Call it after colliders and all LOD renderers are attached: `Configure(house, false)` or `Configure(tree, true)`. It saves separate URP Lit fade variants keyed by each original material's GUID/local ID, extracts base color/texture, and keeps the original arrays. Multiple renderer/LOD bindings fade together using per-renderer property blocks, then restore their exact material arrays and prior indexed property blocks. Fade conversion is a separate temporary view effect and still needs actual visual comparison.

The glTF normal-encoding fix is an import policy, not a runtime lighting workaround. `FarmAssetImportPolicy` keeps non-Lulu normal textures as `Default` plus linear sampling because the glTFast shader consumes raw RG. It excludes `/Lulu/`; rebuilding must preserve that exclusion and the current texture metadata. The rebuild script checks those fields and protected Lulu payload/metadata hashes after each Unity phase.

## Future Lulu replacement — current candidate remains frozen

The current `locomotion-r08` source, staged payload and original full-r02 history remain unchanged. This section describes a later authorized replacement, not work performed on the current character or approval of its known waist/neck/upper-leg defects.

1. Register the supplied replacement as an independent source/version and record its SHA256; keep r08 available. Stage the explicit new choice and regenerate its prefab/LOD references. Do not silently overwrite the registered model or select a failed repair candidate.
2. Keep the gameplay `playerRoot` unscaled and grounded; replace the visual hierarchy under `visualRoot` with +Y up and +Z forward. Assign `FarmRuntimeBootstrap.playerRoot`, `visualRoot` and `mainCamera` before `Start`. Review height, capsule radius/step clearance and camera target against the new mesh; the current capsule measurements are starting values, not universal anatomy.
3. Assign real `idleClip`, `walkClip`, `runClip` on the bootstrap and bind them to the replacement's actual imported skeleton. `FarmAnimationBridge` requires compatible transform paths and either all legacy or all generic clips; it does not retarget arbitrary rigs. Generic clips use `Animator.applyRootMotion=false`; movement stays with `FarmPlayerController`. Recheck stride, idle/walk/run blends, foot contact and sliding.
4. Every skinned LOD needs valid bones/rootBone/weights and the same skeleton mapping. Update `FarmWardrobe.bindings` for each applicable LOD renderer, matching each preset's material slot count. Preserve or deliberately supply the second FabricUV channel and its shader mapping; missing UVs cannot be repaired by assigning a texture name.
5. `FarmThirdPersonCamera` follows `playerRoot` and uses `visualRoot` as its heading target. Reconfigure once through the bootstrap, avoiding duplicate controllers or camera drivers. Rebuild and repeat fixed views, all motion phases, wardrobe, obstruction/collision and the actual route before promoting the new version.

Tree crown proxies are non-trigger SphereColliders on reserved layer 28; the runtime excludes them from player physics while including them in camera casts. Trunk colliders remain physical. A fading component owns an explicit collider list; the camera ignores only those colliders, only after opacity falls to `.35` or below. Other nearby walls/trees continue limiting the camera. Transition duration is initially `.12` seconds, target opacity `.22`; both need real near-wall/tree testing.

## Evidence and public methods

Default output:
`Application.persistentDataPath/FarmEvidence/<UTC session>/`

Override with player arguments:
`--farm-evidence /absolute/output/directory`

Files are created only during actual runtime:

- `route-samples.jsonl`: observed transforms, camera, collision, animation state, active stage, quality and memory every .5 seconds.
- `events.jsonl`: real user/runtime actions and marker proximity. Proximity and ordered traversal do not prove contact, aesthetics or gameplay acceptance.
- `runtime-latest.json`: actual frame distribution, device/OS/GPU/API, quality and current scene state. CPU/GPU timing is optional and separately flagged; zero unavailable GPU timing is not a passing result.
- numbered PNG plus paired JSON: a real end-of-frame framebuffer capture requested through HUD or `Diagnostics.CaptureScreenshot(label)`. Saving an image does not imply anyone viewed it.

Public operations: `runtime.SetMature(bool)`, `SetQuality(0|1)`, `TogglePause()`, `Player.Teleport(position)`, `CameraRig.Recenter()`, `wardrobe.SetPreset(0|1|2)`, `Diagnostics.SaveSnapshot()`, `Diagnostics.GetSnapshot(true)`, `Diagnostics.CaptureScreenshot(label)`.

Route markers carry `name`, world `position`, and proximity `radius`. The current overview sequence is house front, fields, pasture gate, trough, shore, dock, fish stall, house back, return. The recorder preserves actual ordered progress; normal gameplay does not automatically navigate.

## Reproducible simulated-input route

`Farm/07 Play simulated-input acceptance route` opens the real authored FarmWorld scene and starts Play Mode; or start a built player with `--farm-route --farm-evidence /absolute/evidence`. A running scene can call `FarmRoutePlayback.StartFor(runtime)`. It creates a temporary Input System gamepad, queues real movement/orbit/run/pause input events through the existing controller, and never teleports or writes player/camera transforms. Scene `routeMarkers` supply all key destinations; intermediate detours reflect overview r01. User movement keys, mouse-button input or touch stop the simulation. The device is removed afterward.

The route stops and records the location if no progress is observed for six seconds. It records key screenshots, orbits, movement/animation samples and an `automated-route.json` whose mode explicitly says simulated input, not manual UI or device acceptance. Stage, wardrobe and quality checks are separately labeled API exercises; every wardrobe LOD binding is checked for actual material assignment. Original state is restored after the API exercise, including on failure. Pausing and resuming are driven through Start input. Screenshots must still be viewed, and human mouse/Android touch operation must still be tested. This helper does not certify path feasibility before a real run.

## Actual-frame walkthrough recording

In visible Play Mode or a built player, press **F9** to start/stop. The editor also has `Farm/08 Toggle actual-frame walkthrough recording (Play Mode)`. A built player can start recording with `--farm-record-frames --farm-evidence /absolute/evidence`; add `--farm-route` only for the explicitly labeled simulated-input route. Manual recording by itself never drives movement or the camera.

`FarmFrameRecorder` captures the actual framebuffer after `WaitForEndOfFrame` at a requested 10 frames/second. Slow rendering/PNG encoding produces fewer observed frames, never generated catch-up frames. It does not change `Time.captureFramerate`, time scale, camera transforms, or simulation clocks. Resolution changes end the sequence; the default limits are 600 seconds or 1 GiB of PNG data. Output is `walkthrough-*/frame-*.png`, `frames.jsonl` (SHA256, wall-clock timestamp, camera/player/motion/input state), `recording.json`, and `frames.ffconcat`.

After stopping, run from that directory:

```sh
ffmpeg -f concat -safe 0 -i frames.ffconcat -fps_mode vfr -c:v libx264 -pix_fmt yuv420p walkthrough.mp4
```

The concat durations preserve observed wall-clock intervals. Watch the encoded video and compare its frame index before claiming visual review. Recording is not manual interaction evidence unless its input samples and actual operation support that claim.

**Performance is a separate run.** Any frame-sequence or single-screenshot operation permanently labels the current diagnostic session `capture_operations_present_not_a_clean_device_performance_run`. Capture frames and a one-second cooldown are excluded from frame-time aggregates; this exclusion does not rehabilitate a capture session into a clean device benchmark. Relaunch the player without recording/screenshot actions, exercise the route, and save only JSON diagnostics for device measurements.

## Required actual checks before acceptance

Compile all scripts with locked Unity/packages; load the assembled scene; inspect real imported Idle/Walk/Run and transitions; exercise mouse and Android multi-touch separately; test diagonal speed, pause, wall collision, tight camera obstruction, stages, shorts UV/materials and both URP profiles. Inspect screenshots, run the defined route and save the device report. Android model and OS still need to come from the connected device. This directory does not claim those tests have already happened.
