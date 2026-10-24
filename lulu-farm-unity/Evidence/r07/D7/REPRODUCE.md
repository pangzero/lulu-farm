# r07 DeepSeek 执行工具

在 Unity 工程根目录运行。编辑器固定为 `../.unity-install/Editors/6000.3.16f1/Unity.app`。不要并发运行同项目编辑器；性能采集时只运行一个游戏实例，不运行编辑器、截图、视频编码或其他渲染任务。

1. `python3 Scripts/r07-evidence-index.py D3 --before D2` 保存前一阶段证据与代码快照（示例）。已有快照拒绝覆盖。
2. `python3 Scripts/r07-run-editor.py D3 generate development` 使用 Builder 生成场景、12 标准固定机位、18 个后期开启机位，并开发构建。包装脚本核对 388 个冻结 Lulu 文件和包锁。
3. `python3 Scripts/r07-run-player.py D3 route` 运行可见 macOS 开发包，31 点模拟输入路线；不是人工全程漫游。
4. `python3 Scripts/r07-run-player.py D3 performance` 独立无截图测试。D3 320 秒（含 5 秒预热）；其他阶段 920 秒。20 格全成熟、电脑档、1280×720。仅在进程生命周期使用 caffeinate 防休眠。
5. `python3 Scripts/r07-run-editor.py D3 export` 用锁定版本的 Unity ProfilerDriver 读取真实二进制记录。原始文件保留；时间线导出每线程根节点及 ≥0.1ms 标记，细节仍可在原始 `.data` 查看。失败段明确记录，不伪造时间线。
6. `python3 Scripts/r07-evidence-index.py D3` 汇总实测原值、路线、同机位和构建记录。此工具不生成验收结论。

Unity binary logger 自动追加 `.raw`；Player 退出后包装脚本仅将 `.data.raw` 重命名为 `.data`，不改变二进制内容。采集按 10 秒分段，切段本身有开销，与未挂 Profiler 的 r06 数据不能直接当作零开销对照。Opus 负责分析。

标准 12 固定机位沿用旧工具，不修改其关闭后期的逻辑。额外 18 个机位以 HDR 相机渲染到 SDR sRGB ARGB32 目标，适用于屏幕 PNG；原始 ARGBHalf 直接读回的偏暗 D5 证据保留在 `D5/fixed-pp-on-linear-readback-r01`，不用于新的画面对比。

D6 附加检查：`python3 Scripts/r07-run-player.py D6 ambient`。实际按钮回调切换风动／环境声／手机档，保存实际界面，录制四个诊断固定视角的真实帧。诊断相机与模拟路线明确分开，未增加玩法视角。音效为本工程数学合成，来源见 `Assets/Farm/Audio/R07/audio-source.json`。

所有 REPORT 的状态为“已完成，待 Opus 验收”或明确未完成。技术记录不等于用户美术认可；性能只列实测数据，不下结论。Android、Windows、iOS 和 Intel Mac 不由本机测试推定。

## 最终阶段及录像

当前 Builder 未传 `--r07-task` 时默认为 D6；显式 D5/D2/D3/D4 可分别复现先前阶段。场景需生成后再构建。Opus 接入新 Lulu 后，勿无条件重跑历史导入流程覆盖其工作。

D6 实际录像为 `../D6/ambient/d6-motion-r02.mp4`，无声轨；运行会话 `ambient-proof/runtime-audio.wav` 是实际 AudioListener 输出，无麦克风。原录制器在会话退出时再次写 summary，导致 elapsedSeconds 长于已停止帧序列。此次编码使用在实际 StopRecording 当时逐字节保存的 recording-stop-snapshot.json；退出清单保留，未改动历史录制器。`ambient/encoding-input/PROVENANCE.md` 说明两个清单与硬链接帧来源。

复现录像时，应在显式停止后、进程退出前保存该实时清单，或由 Opus 独立修正原录制器重复 StopRecording 的摘要行为。不要手工估计帧时长或伪造停止时间。
