using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.UI;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace LuluFarm
{
    // Adds presentation controls without changing the established runtime/input scripts.
    public sealed class FarmPresentationModeR07 : MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public bool DebugMode { get; private set; }
        public bool Ready { get; private set; }
        Transform safe, header, inspect, inspection, status;
        Text modeLabel;
        Button modeButton;
        CanvasGroup intro;
        float shownAt;

        IEnumerator Start()
        {
            if (runtime == null) runtime = GetComponent<FarmRuntimeBootstrap>();
            while (runtime != null && (runtime.HUD == null || runtime.Diagnostics == null)) yield return null;
            if (runtime == null) yield break;
            safe = runtime.transform.Find("FarmHUD/SafeArea");
            if (safe == null) throw new InvalidOperationException("r07 presentation requires the built FarmHUD safe area.");
            header = safe.Find("Header"); inspect = header.Find("Inspect");
            inspection = safe.Find("Inspection"); status = safe.Find("Status");
            modeButton = AddButton("PresentationMode", header, "调试模式", new Vector2(-75, 0), () => SetDebug(!DebugMode));
            modeLabel = modeButton.GetComponentInChildren<Text>();
            var label = Label("OpeningControls", safe,
                runtime.Input.MobileControls ? "左侧移动 · 右侧拖动视角 · 双指缩放" : "WASD 移动 · Shift 跑步 · 拖动旋转 · 滚轮缩放 · R 回正",
                new Vector2(22, 28), new Vector2(1000, 40), new Vector2(0, 0));
            label.alignment = TextAnchor.MiddleLeft; label.rectTransform.pivot = new Vector2(0, .5f);
            intro = label.gameObject.AddComponent<CanvasGroup>(); intro.blocksRaycasts = false;
            shownAt = Time.unscaledTime; Ready = true; SetDebug(false);
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--r07-ui-capture") >= 0) StartCoroutine(CaptureModes());
        }
        void Update()
        {
            if (!Ready) return;
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && Keyboard.current.f3Key.wasPressedThisFrame) SetDebug(!DebugMode);
#endif
            intro.alpha = DebugMode ? 0 : 1 - Mathf.Clamp01((Time.unscaledTime - shownAt - 5f) / .7f);
        }
        public void SetDebug(bool value)
        {
            if (!Ready) return;
            DebugMode = value; intro.alpha = value ? 0 : 1 - Mathf.Clamp01((Time.unscaledTime - shownAt - 5f) / .7f);
            inspect.gameObject.SetActive(value); status.gameObject.SetActive(value);
            if (!value) inspection.gameObject.SetActive(false);
            ((RectTransform)header.Find("Recenter")).anchoredPosition = new Vector2(value ? -480 : -345, 0);
            ((RectTransform)header.Find("Pause")).anchoredPosition = new Vector2(value ? -345 : -210, 0);
            ((RectTransform)inspect).anchoredPosition = new Vector2(-210, 0);
            modeLabel.text = value ? "正常模式" : "调试模式";
            runtime.Diagnostics.RecordEvent("r07_ui_" + (value ? "debug" : "normal"));
        }
        public Button AddButton(string name, Transform parent, string caption, Vector2 position, UnityEngine.Events.UnityAction action, float width = 120)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image), typeof(Button));
            var rect = (RectTransform)go.transform; rect.SetParent(parent, false);
            rect.anchorMin = rect.anchorMax = new Vector2(1, .5f); rect.sizeDelta = new Vector2(width, 44); rect.anchoredPosition = position;
            go.GetComponent<Image>().color = new Color(.83f, .91f, .78f);
            var button = go.GetComponent<Button>(); button.targetGraphic = go.GetComponent<Image>();
            button.navigation = new Navigation { mode = Navigation.Mode.None }; button.onClick.AddListener(action);
            Label("Label", rect, caption, Vector2.zero, new Vector2(width - 8, 42), new Vector2(.5f, .5f));
            return button;
        }
        Text Label(string name, Transform parent, string text, Vector2 position, Vector2 size, Vector2 anchor)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Text)); var rect = (RectTransform)go.transform;
            rect.SetParent(parent, false); rect.anchorMin = rect.anchorMax = anchor; rect.sizeDelta = size; rect.anchoredPosition = position;
            var label = go.GetComponent<Text>(); label.font = runtime.uiFont; label.fontSize = 18; label.color = new Color(.22f, .29f, .25f);
            label.alignment = TextAnchor.MiddleCenter; label.text = text; label.raycastTarget = false; return label;
        }
        IEnumerator CaptureModes()
        {
            string dir = Path.Combine(runtime.Diagnostics.OutputDirectory, "ui"); Directory.CreateDirectory(dir);
            yield return new WaitForSecondsRealtime(1); yield return Capture(dir, "01-normal-opening");
            yield return new WaitForSecondsRealtime(6); yield return Capture(dir, "02-normal-settled");
            modeButton.onClick.Invoke(); inspect.GetComponent<Button>().onClick.Invoke();
            yield return new WaitForSecondsRealtime(.3f); yield return Capture(dir, "03-debug-inspection");
            modeButton.onClick.Invoke(); yield return new WaitForSecondsRealtime(.3f); yield return Capture(dir, "04-normal-return");
        }
        IEnumerator Capture(string dir, string name)
        {
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png"));
            File.WriteAllText(Path.Combine(dir, name + ".json"), JsonUtility.ToJson(new UIState {
                utc=DateTime.UtcNow.ToString("o"), debugMode=DebugMode, inspectionVisible=inspection.gameObject.activeSelf,
                inspectButtonVisible=inspect.gameObject.activeSelf, bottomDebugVisible=status.gameObject.activeSelf,
                introAlpha=intro.alpha, developmentBuild=Debug.isDebugBuild, width=Screen.width,height=Screen.height,
                method="standalone_UI_button_callbacks_scripted_not_human_click" }, true));
        }
        [Serializable] sealed class UIState {
            public string utc, method; public bool debugMode,inspectionVisible,inspectButtonVisible,bottomDebugVisible,developmentBuild;
            public float introAlpha; public int width,height;
        }
    }
}
