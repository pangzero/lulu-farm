using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.EnhancedTouch;
using ETouch = UnityEngine.InputSystem.EnhancedTouch.Touch;
#endif

namespace LuluFarm
{
    [DefaultExecutionOrder(-100)]
    public sealed class FarmInputRouter : MonoBehaviour
    {
        public Vector2 Move { get; private set; }
        public Vector2 LookDegrees { get; private set; }
        public float ZoomSteps { get; private set; }
        public bool Run { get; private set; }
        public bool Paused { get; private set; }
        public bool ResetRequested { get; private set; }
        public bool PauseRequested { get; private set; }
        public Vector2 TouchMove { get; set; }
        public bool TouchRun { get; set; }
        public bool UIBlocked { get; private set; }
        public float mouseSensitivity = .18f;
        public float touchSensitivity = .16f;
        public bool MobileControls => Application.isMobilePlatform || forceTouchControls;
        public bool forceTouchControls;
        public string ActiveInputSource { get; private set; } = "none";
        readonly List<RaycastResult> hits = new List<RaycastResult>(16);
        readonly List<int> eligibleTouches = new List<int>(4);
        readonly List<Vector2> touchPositions = new List<Vector2>(4);
        Vector2 lastMousePosition;
        int lookFinger = -1;
        Vector2 lastTouchPosition;
        float previousPinch;
        bool mouseOwnsLook;
        float queuedZoom;
        bool queuedReset;
#if ENABLE_INPUT_SYSTEM
        InputActionMap map;
        InputAction moveAction, runAction, resetAction, pauseAction, mousePressAction, mousePositionAction;
        Vector2 queuedMouseDelta, mouseEventPosition;
        int mouseEventDeviceId = -1;
        bool mouseEventHeld, mouseEventOverUI, queuedMouseUIBlocked;
        sealed class MouseEventLease { public int owners; public bool previousMergingDisabled; }
        static readonly Dictionary<InputSettings, MouseEventLease> mouseEventLeases = new Dictionary<InputSettings, MouseEventLease>();
        InputSettings leasedMouseSettings;
#endif

        void OnEnable()
        {
#if ENABLE_INPUT_SYSTEM
            EnhancedTouchSupport.Enable();
            RetainUnmergedMouseEvents();
            map = new InputActionMap("Farm");
            moveAction = map.AddAction("Move", InputActionType.Value);
            moveAction.AddCompositeBinding("2DVector")
                .With("Up", "<Keyboard>/w").With("Down", "<Keyboard>/s")
                .With("Left", "<Keyboard>/a").With("Right", "<Keyboard>/d");
            moveAction.AddCompositeBinding("2DVector")
                .With("Up", "<Keyboard>/upArrow").With("Down", "<Keyboard>/downArrow")
                .With("Left", "<Keyboard>/leftArrow").With("Right", "<Keyboard>/rightArrow");
            moveAction.AddBinding("<Gamepad>/leftStick");
            runAction = map.AddAction("Run", InputActionType.Button, "<Keyboard>/leftShift");
            runAction.AddBinding("<Keyboard>/rightShift");
            runAction.AddBinding("<Gamepad>/leftStickPress");
            resetAction = map.AddAction("Recenter", InputActionType.Button, "<Keyboard>/r");
            pauseAction = map.AddAction("Pause", InputActionType.Button, "<Keyboard>/escape");
            pauseAction.AddBinding("<Gamepad>/start");
            // PassThrough callbacks retain every press/position/release in an input update.
            // Polling the final held state loses a complete drag delivered in one frame.
            mousePressAction = map.AddAction("MouseLookPress", InputActionType.PassThrough);
            mousePressAction.AddBinding("<Mouse>/leftButton");
            mousePressAction.AddBinding("<Mouse>/rightButton");
            mousePositionAction = map.AddAction("MouseLookPosition", InputActionType.PassThrough, "<Mouse>/position");
            mousePressAction.performed += OnMousePress;
            mousePositionAction.performed += OnMousePosition;
            map.Enable();
#endif
        }

#if ENABLE_INPUT_SYSTEM
        void RetainUnmergedMouseEvents()
        {
            // FastMouse can merge a first press with the following held movement before actions
            // see either event. Preserve the press location, restoring this runtime-only setting
            // when the last router is disabled. Focus and key/touch bindings stay unchanged.
            leasedMouseSettings = InputSystem.settings;
            if (!mouseEventLeases.TryGetValue(leasedMouseSettings, out var lease))
            {
                lease = new MouseEventLease { previousMergingDisabled = leasedMouseSettings.disableRedundantEventsMerging };
                mouseEventLeases.Add(leasedMouseSettings, lease);
            }
            lease.owners++;
            leasedMouseSettings.disableRedundantEventsMerging = true;
        }
        void ReleaseUnmergedMouseEvents()
        {
            if (leasedMouseSettings == null) return;
            if (mouseEventLeases.TryGetValue(leasedMouseSettings, out var lease) && --lease.owners == 0)
            {
                leasedMouseSettings.disableRedundantEventsMerging = lease.previousMergingDisabled;
                mouseEventLeases.Remove(leasedMouseSettings);
            }
            leasedMouseSettings = null;
        }
        void OnMousePress(InputAction.CallbackContext context)
        {
            AccumulateMouse(context.control.device as Mouse, context.ReadValue<float>() > .5f);
        }
        void OnMousePosition(InputAction.CallbackContext context)
        {
            AccumulateMouse(context.control.device as Mouse, false);
        }
        void AccumulateMouse(Mouse mouse, bool newPress)
        {
            if (mouse == null) return;
            if (mouseEventDeviceId != mouse.deviceId)
            {
                if (mouseEventHeld) return; // Another pointer cannot take over an active gesture.
                mouseEventDeviceId = mouse.deviceId;
                mouseEventPosition = mouse.position.ReadValue();
            }
            Vector2 position = mouse.position.ReadValue();
            bool held = mouse.leftButton.isPressed || mouse.rightButton.isPressed;
            bool overUI = IsOverUI(position);
            if (mouseEventHeld)
            {
                // Read position before ending a gesture: a release event can contain its final
                // movement. Duplicate callbacks for that same state have zero displacement.
                if (mouseOwnsLook && !Paused && !mouseEventOverUI && !overUI)
                    queuedMouseDelta += position - mouseEventPosition;
                queuedMouseUIBlocked |= mouseEventOverUI || overUI;
                mouseEventHeld = held;
                if (!held) mouseOwnsLook = false;
            }
            else if (newPress && held)
            {
                mouseEventHeld = true;
                mouseOwnsLook = !Paused && !overUI;
                queuedMouseUIBlocked |= overUI;
                // The press position is the origin. A cursor warp/move to the start is not look.
            }
            mouseEventPosition = position;
            mouseEventOverUI = overUI;
        }
#endif

        void OnDisable()
        {
#if ENABLE_INPUT_SYSTEM
            map?.Dispose(); map = null;
            ReleaseUnmergedMouseEvents();
            EnhancedTouchSupport.Disable();
#endif
            ClearInput();
        }

        void Update()
        {
            LookDegrees = Vector2.zero;
            ZoomSteps = queuedZoom; queuedZoom = 0;
            ResetRequested = queuedReset; queuedReset = false;
            PauseRequested = false;
            UIBlocked = false;
            Vector2 keyboardMove = Vector2.zero;
            bool run = false, mouseDown = false;
#if !ENABLE_INPUT_SYSTEM
            bool mousePressed = false;
#endif
            Vector2 mousePosition = lastMousePosition;
            float scroll = 0;
#if ENABLE_INPUT_SYSTEM
            keyboardMove = moveAction.ReadValue<Vector2>();
            run = runAction.IsPressed();
            ResetRequested |= resetAction.WasPressedThisFrame();
            PauseRequested = pauseAction.WasPressedThisFrame();
            if (Mouse.current != null)
            {
                mousePosition = Mouse.current.position.ReadValue();
                mouseDown = Mouse.current.rightButton.isPressed || Mouse.current.leftButton.isPressed;
                scroll = Mouse.current.scroll.ReadValue().y / 120f;
            }
#elif ENABLE_LEGACY_INPUT_MANAGER
            keyboardMove = new Vector2((Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow) ? 1 : 0) -
                (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) ? 1 : 0),
                (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow) ? 1 : 0) -
                (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow) ? 1 : 0));
            run = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
            ResetRequested |= Input.GetKeyDown(KeyCode.R);
            PauseRequested = Input.GetKeyDown(KeyCode.Escape);
            mousePosition = Input.mousePosition;
            mousePressed = Input.GetMouseButtonDown(0) || Input.GetMouseButtonDown(1);
            mouseDown = Input.GetMouseButton(0) || Input.GetMouseButton(1);
            scroll = Input.mouseScrollDelta.y;
#endif
            bool mouseOverUI = IsOverUI(mousePosition);
#if ENABLE_INPUT_SYSTEM
            LookDegrees = queuedMouseDelta * mouseSensitivity;
            if (queuedMouseDelta.sqrMagnitude > 0) ActiveInputSource = "mouse";
            queuedMouseDelta = Vector2.zero;
            UIBlocked = queuedMouseUIBlocked || (mouseOverUI && mouseDown);
            queuedMouseUIBlocked = false;
#else
            if (mousePressed) mouseOwnsLook = !mouseOverUI;
            if (!mouseDown) mouseOwnsLook = false;
            if (mouseOwnsLook && !mouseOverUI && !Paused)
            {
                if (!mousePressed) LookDegrees = (mousePosition - lastMousePosition) * mouseSensitivity;
                ActiveInputSource = "mouse";
            }
            UIBlocked = mouseOverUI && mouseDown;
#endif
            if (!mouseOverUI) ZoomSteps += scroll;
            lastMousePosition = mousePosition;
            ReadTouchLook();
#if ENABLE_INPUT_SYSTEM
            if (!Paused && Gamepad.current != null)
            {
                Vector2 stick = Gamepad.current.rightStick.ReadValue();
                if (stick.sqrMagnitude > .01f)
                { LookDegrees += stick * (110f * Time.unscaledDeltaTime); ActiveInputSource = "gamepad"; }
            }
#endif
            bool inputField = EventSystem.current != null && EventSystem.current.currentSelectedGameObject != null &&
                EventSystem.current.currentSelectedGameObject.GetComponent<UnityEngine.UI.InputField>() != null;
            if (UIBlocked) keyboardMove = Vector2.zero;
            Move = Paused || inputField ? Vector2.zero : Vector2.ClampMagnitude(keyboardMove + TouchMove, 1f);
            Run = !Paused && (run || TouchRun);
            if (Move.sqrMagnitude > .01f) ActiveInputSource = TouchMove.sqrMagnitude > .01f ? "touch" : "keyboard_or_gamepad";
            if (Paused) { LookDegrees = Vector2.zero; ZoomSteps = 0; }
        }

        void ReadTouchLook()
        {
#if ENABLE_INPUT_SYSTEM
            var touches = ETouch.activeTouches;
            touchPositions.Clear();
            bool ownerPresent = false;
            for (int i = 0; i < touches.Count; i++)
            {
                var touch = touches[i];
                int id = touch.touchId;
                bool end = touch.phase == UnityEngine.InputSystem.TouchPhase.Ended || touch.phase == UnityEngine.InputSystem.TouchPhase.Canceled;
                if (touch.phase == UnityEngine.InputSystem.TouchPhase.Began)
                {
                    if (touch.screenPosition.x > Screen.width * .42f && !IsOverUI(touch.screenPosition)) eligibleTouches.Add(id);
                }
                if (end) { eligibleTouches.Remove(id); if (lookFinger == id) lookFinger = -1; continue; }
                if (!eligibleTouches.Contains(id)) continue;
                touchPositions.Add(touch.screenPosition);
                if (lookFinger < 0) { lookFinger = id; lastTouchPosition = touch.screenPosition; }
                if (id == lookFinger)
                {
                    ownerPresent = true;
                    if (!Paused && !IsOverUI(touch.screenPosition))
                    {
                        LookDegrees = (touch.screenPosition - lastTouchPosition) * touchSensitivity * (720f / Mathf.Max(720, Screen.height));
                        ActiveInputSource = "touch";
                    }
                    lastTouchPosition = touch.screenPosition;
                }
            }
            if (!ownerPresent) lookFinger = -1;
            if (touches.Count == 0) eligibleTouches.Clear();
            if (touchPositions.Count >= 2)
            {
                float pinch = Vector2.Distance(touchPositions[0], touchPositions[1]);
                if (previousPinch > 0 && !Paused) ZoomSteps += (pinch - previousPinch) / 100f;
                previousPinch = pinch;
                LookDegrees = Vector2.zero;
            }
            else previousPinch = 0;
#endif
        }

        public bool IsOverUI(Vector2 position)
        {
            if (EventSystem.current == null) return false;
            var data = new PointerEventData(EventSystem.current) { position = position };
            hits.Clear();
            EventSystem.current.RaycastAll(data, hits);
            for (int i = 0; i < hits.Count; i++)
                if (hits[i].module is UnityEngine.UI.GraphicRaycaster) return true;
            return false;
        }

        public void SetPaused(bool value) { Paused = value; if (value) ClearInput(); }
        public void RequestRecenter() { queuedReset = true; }
        public void RequestZoom(float steps) { queuedZoom += steps; }
        void ClearInput()
        {
            Move = TouchMove = LookDegrees = Vector2.zero; TouchRun = Run = false;
            mouseOwnsLook = false; lookFinger = -1; eligibleTouches.Clear();
#if ENABLE_INPUT_SYSTEM
            queuedMouseDelta = Vector2.zero; queuedMouseUIBlocked = false;
            mouseEventHeld = false; mouseEventOverUI = false; mouseEventDeviceId = -1;
#endif
        }
        void OnApplicationFocus(bool focused) { if (!focused) ClearInput(); }
    }
}
