using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace LuluFarm
{
    public sealed class FarmHUD : MonoBehaviour
    {
        FarmRuntimeBootstrap runtime;
        Font font;
        Text pauseLabel, qualityLabel, stageLabel, wardrobeLabel, status;
        GameObject inspection;
        RectTransform safeRoot;
        Rect previousSafeArea;
        float nextRefresh;
        static readonly Color Ink = new Color(.22f, .29f, .25f);

        public void Build(FarmRuntimeBootstrap owner)
        {
            runtime = owner;
            font = owner.uiFont != null ? owner.uiFont : Resources.Load<Font>("FarmChinese");
            if (font == null)
                font = Font.CreateDynamicFontFromOSFont(new[] { "PingFang SC", "Noto Sans CJK SC", "NotoSansCJK-Regular", "Microsoft YaHei", "Arial Unicode MS", "Arial" }, 24);
            if (font == null) font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var canvasGO = new GameObject("FarmHUD", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 50;
            var scaler = canvasGO.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);
            scaler.matchWidthOrHeight = .5f;
            safeRoot = Rect("SafeArea", canvasGO.transform, new Vector2(0, 0), new Vector2(1, 1), Vector2.zero, Vector2.zero);
            ApplySafeArea();
            var header = Panel("Header", safeRoot, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, -35), new Vector2(0, 70), new Color(.98f, .96f, .89f, .94f));
            Label("Title", header, "噜噜农场", new Vector2(28, 0), new Vector2(230, 55), 26, TextAnchor.MiddleLeft, new Vector2(0, .5f));
            Button("Recenter", header, "回正视角", new Vector2(-345, 0), () => runtime.Input.RequestRecenter());
            pauseLabel = Button("Pause", header, "暂停", new Vector2(-210, 0), () => runtime.TogglePause());
            Button("Inspect", header, "检查", new Vector2(-75, 0), () => inspection.SetActive(!inspection.activeSelf));
            inspection = Panel("Inspection", safeRoot, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-150, -254), new Vector2(280, 352), new Color(.98f, .96f, .89f, .96f)).gameObject;
            qualityLabel = Button("Quality", inspection.transform, "画质：电脑", new Vector2(-140, 131), () => runtime.SetQuality(runtime.QualityLabel == "电脑" ? 0 : 1), 250);
            stageLabel = Button("Stages", inspection.transform, "作物：混合种植", new Vector2(-140, 76), () => {if(runtime.MixedStage)runtime.SetMature(false);else if(!runtime.MatureStage)runtime.SetMature(true);else runtime.SetMixedStages();}, 250);
            wardrobeLabel = Button("Wardrobe", inspection.transform, "短裤：原版", new Vector2(-140, 21), () =>
            {
                if (runtime.wardrobe != null) runtime.wardrobe.SetPreset((runtime.wardrobe.CurrentIndex + 1) % 3);
                runtime.Diagnostics.RecordEvent("wardrobe_" + (runtime.wardrobe != null ? runtime.wardrobe.CurrentIndex.ToString() : "unconfigured"));
            }, 250);
            Button("Capture", inspection.transform, "保存当前画面", new Vector2(-140, -34), () => runtime.Diagnostics.CaptureScreenshot("manual"), 250);
            Button("Evidence", inspection.transform, "保存运行记录", new Vector2(-140, -89), () => runtime.Diagnostics.SaveSnapshot(), 250);
            Button("ResetPlayer", inspection.transform, "返回起点", new Vector2(-140, -144), () =>
            { runtime.Player.Teleport(runtime.Player.spawnPosition); runtime.Diagnostics.RecordEvent("teleport_to_spawn"); }, 250);
            inspection.SetActive(false);
            status = Label("Status", safeRoot, "", new Vector2(20, 20), new Vector2(1000, 36), 16, TextAnchor.MiddleLeft, Vector2.zero);
            status.color = new Color(.13f, .22f, .16f);
            if (runtime.Input.MobileControls)
            {
                var joystick = Panel("MoveJoystick", safeRoot, Vector2.zero, Vector2.zero, new Vector2(118, 150), new Vector2(170, 170), new Color(.95f, .96f, .87f, .5f));
                var knob = Panel("Knob", joystick, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, new Vector2(65, 65), new Color(.3f, .53f, .4f, .7f));
                knob.GetComponent<Image>().raycastTarget = false;
                var control = joystick.gameObject.AddComponent<FarmTouchJoystick>();
                control.input = runtime.Input; control.knob = knob; control.radius = 65;
                Button("Run", safeRoot, "走／跑", new Vector2(-100, 145), () => runtime.Input.TouchRun = !runtime.Input.TouchRun, 120, new Vector2(1, 0));
                Button("ZoomIn", safeRoot, "近", new Vector2(-250, 90), () => runtime.Input.RequestZoom(1), 90, new Vector2(1, 0));
                Button("ZoomOut", safeRoot, "远", new Vector2(-350, 90), () => runtime.Input.RequestZoom(-1), 90, new Vector2(1, 0));
            }
        }

        void Update()
        {
            if (runtime == null || runtime.Input == null) return;
            if (Screen.safeArea != previousSafeArea) ApplySafeArea();
            if (Time.unscaledTime < nextRefresh) return;
            nextRefresh = Time.unscaledTime + .25f;
            pauseLabel.text = runtime.Input.Paused ? "继续" : "暂停";
            qualityLabel.text = "画质：" + runtime.QualityLabel;
            stageLabel.text = runtime.MixedStage ? "作物：混合种植" : runtime.MatureStage ? "作物：成熟" : "作物：幼苗";
            wardrobeLabel.text = runtime.wardrobe != null && runtime.wardrobe.IsConfigured ? "短裤：" + runtime.wardrobe.CurrentName : "短裤：尚未接入";
            string controls = runtime.Input.MobileControls ? "左侧移动 · 右侧拖动视角 · 双指缩放" : "WASD 移动 · Shift 跑步 · 鼠标拖动旋转 · 滚轮缩放 · R 回正";
            status.text = runtime.Input.Paused ? "已暂停" : controls;
            if (runtime.Recorder != null && runtime.Recorder.IsRecording)
                status.text = "录制中 · " + runtime.Recorder.WrittenFrames + " 帧 · F9 停止 · " + status.text;
        }

        void ApplySafeArea()
        {
            previousSafeArea = Screen.safeArea;
            if (safeRoot == null) return;
            safeRoot.anchorMin = new Vector2(previousSafeArea.xMin / Screen.width, previousSafeArea.yMin / Screen.height);
            safeRoot.anchorMax = new Vector2(previousSafeArea.xMax / Screen.width, previousSafeArea.yMax / Screen.height);
            safeRoot.offsetMin = safeRoot.offsetMax = Vector2.zero;
        }

        Text Button(string name, Transform parent, string text, Vector2 position, UnityEngine.Events.UnityAction action,
            float width = 120, Vector2? anchor = null)
        {
            Vector2 a = anchor ?? new Vector2(1, .5f);
            var rect = Panel(name, parent, a, a, position, new Vector2(width, 44), new Color(.83f, .91f, .78f));
            var button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = rect.GetComponent<Image>();
            button.onClick.AddListener(action);
            button.navigation = new Navigation { mode = Navigation.Mode.None };
            var label = Label("Label", rect, text, Vector2.zero, new Vector2(width - 10, 42), 19, TextAnchor.MiddleCenter, new Vector2(.5f, .5f));
            return label;
        }

        Text Label(string name, Transform parent, string text, Vector2 position, Vector2 size, int fontSize, TextAnchor alignment, Vector2 anchor)
        {
            var rt = Rect(name, parent, anchor, anchor, position, size);
            if (alignment == TextAnchor.MiddleLeft) rt.pivot = new Vector2(0, .5f);
            var label = rt.gameObject.AddComponent<Text>();
            label.font = font; label.text = text; label.fontSize = fontSize;
            label.color = Ink; label.alignment = alignment; label.raycastTarget = false;
            label.horizontalOverflow = HorizontalWrapMode.Overflow;
            label.verticalOverflow = VerticalWrapMode.Overflow;
            return label;
        }

        static RectTransform Panel(string name, Transform parent, Vector2 min, Vector2 max, Vector2 position, Vector2 size, Color color)
        {
            var rect = Rect(name, parent, min, max, position, size);
            rect.gameObject.AddComponent<Image>().color = color;
            return rect;
        }
        static RectTransform Rect(string name, Transform parent, Vector2 min, Vector2 max, Vector2 position, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rect = go.GetComponent<RectTransform>(); rect.SetParent(parent, false);
            rect.anchorMin = min; rect.anchorMax = max; rect.pivot = new Vector2(.5f, .5f);
            rect.sizeDelta = size; rect.anchoredPosition = position;
            return rect;
        }
    }

}
