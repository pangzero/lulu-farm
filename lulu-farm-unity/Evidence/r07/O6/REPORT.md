# r07 O6 第三轮执行记录

**3.1–3.7 已完成，待 Opus 验收。3.8 原生键盘移动及录像已采集；鼠标完整环绕失败，连续切换观感未验证。环境声未试听。** 本记录只执行、列值和描述，不作美术、性能或最终验收结论。

执行分支 `opus/r07-o6-continue`，输入提交 `3bc1b3e4a35b7e8ea3ac2c0ce14d1664e7a6cc16`。本机日期 2026-10-25 Asia/Shanghai；日志、目录时间是 UTC 2026-10-24。收尾 fetch 后远端仍为同一输入提交。Unity 保持 6000.3.16f1；包版本、原始资产、r06、旧 Lulu locomotion-r08 及 lulu-studio review 均未编辑。

第 2 节快照与第 2.5 节重签均未重复。`snapshot-integrity-attempt-03.json` 复核 58 件原快照 SHA256，changedFiles 为空；最后一次运行后的 `final-integrity.json` 复核 403 件保护文件，changedFiles 为空。场景及 GeneratedR08 产物来自已有 Builder；未修改 Opus C#/Shader/脚本来绕过问题。

## 执行与命令

完整 argv、UTC、exitCode、完成检查见 [command-record.json](command-record.json) 和各 `*-execution.json`。

| 步骤 | 命令（在 lulu-farm-unity） | 执行记录 |
|---|---|---|
| 3.1 | `python3 Scripts/r07-run-editor.py O6 generate development` | generate/development exitCode 均 0，changedProtectedFiles 均为空；build-development.json = Succeeded，errors 0 / warnings 0，799222676 bytes。已完成，待 Opus 验收。 |
| 3.2 | `python3 Scripts/r07-run-player.py O6 route` | 第二次运行 31/31，四项检查 true，exitCode 0。已完成，待 Opus 验收。 |
| 3.3 | `python3 Scripts/r07-run-player.py O6 ambient` | exitCode 0；384 原始帧、WAV 已生成；按原 recording.json 编码。已完成采集，待 Opus 验收；声音未试听。 |
| 3.4 | `python3 Scripts/r07-run-player.py O6 performance` | exitCode 0；五项检查 true；有效 912.6931762695312 s，8 圈。已完成，待 Opus 验收。 |
| 3.5 off | `python3 Scripts/r07-run-player.py O6 performance --label wind-off --wind off --seconds 320` | 第二次运行 exitCode 0，五项检查 true；312.71258544921875 s，2 圈。已完成，待 Opus 验收。 |
| 3.5 on | `python3 Scripts/r07-run-player.py O6 performance --label wind-on --wind on --seconds 320` | exitCode 0，五项检查 true；312.7342834472656 s，3 圈。已完成，待 Opus 验收。 |
| 3.6 | `python3 Scripts/r07-run-editor.py O6 export`，再分别加 `--profiler-directory Evidence/r07/O6/profiler-wind-off` / `.../profiler-wind-on` | 三次 exitCode 0，保护文件列表为空。92 + 32 + 32 = 156 段均有 timeline gzip，索引状态 `exported_filtered_timeline_binary_retained`。已完成，待 Opus 验收。 |
| 3.7 | `python3 Scripts/r07-evidence-index.py O6`；`python3 Scripts/r07-compare-performance.py O6`；`python3 Scripts/r07-final-integrity.py O6` | 均 exitCode 0。metrics、compare.html、performance-table 和 final-integrity 已保存；1 路线、3 性能会话、30 对照项。已完成，待 Opus 验收。 |
| 3.8 | 直接启动本轮 development App，原生 CUA 键盘/鼠标；完整 argv 见 manual 与 manual-02 execution | 两次 Player exitCode 0。键盘移动已录制；两次窗口绑定下拖动均报 `noWindowsAvailable`，已停止该失败操作路线。完整绕屋/树转圈未完成。 |

第二轮输出保存在 `attempt-02/captured-output/`。根目录旧 `generate-20261024-140118*`、`generate-20261024-141736*`、`failure-audit.json`、`failure-context.txt` 是前两轮历史，不属于本次成功生成记录。

## 失败、异常及完整日志

- 本轮实际生成日志：[generate-20261024-165408.log](generate-20261024-165408.log)；构建日志：[development-20261024-165425.log](development-20261024-165425.log)。六份 Editor 日志（含四次导出）各有真实 Licensing Error：旧通道握手和 token 更新报错，随后连接 6000.3.16 客户端、更新许可并完成初始化。没有把这些行隐藏为“无错误”。显式 C# / Shader 编译错误模式未匹配，相关完整行号和前后 20 行见 [log-review/summary.json](log-review/summary.json) 及同目录上下文。
- 当前路线、ambient、三组正式性能，以及两次 manual 和两次中断会话的 Player 日志，Exception / Error 模式均未匹配。Shader 字样为退出 telemetry 的内存标签；不据此判断内存状态。负缩放/碰撞警告模式未匹配。补充范围见 [log-review/supplemental-summary.json](log-review/supplemental-summary.json)。
- 首次 route 在 1/31、5.181 s 时 `stopped_by_human_input`；输入来源未确定。同期有原生绑定/截图与用户回复，不能断言具体来源。全套 route JSON、events、截图、日志保留于 [attempt-03/route-01-input-stop/](attempt-03/route-01-input-stop/)。随后相同命令跑到 31/31，未改代码。
- 首次 wind-off 因失焦在约 140 s 时退出，measurement 132.297073 s，wrapper 2 / Player 0，duration/focus 检查 false；不纳入正式三会话。全量保留于 [attempt-03/wind-off-01-focus-loss/](attempt-03/wind-off-01-focus-loss/)，其 14 段也已另行导出时间线（export-175829，exitCode 0）。有效 off/on 启动时在预热前 Raise 窗口，测量中无 UI 操作，完成检查 allWindowsFocused true。
- 原生控制器第一次出现一次 ScreenCaptureKit -3811，下一次截图恢复；鼠标拖动多次 `noWindowsAvailable`。重置 CUA、重新绑定并 Raise 的第二次仍出现 -10005/noWindowsAvailable，未继续重复或改代码。键盘控制、F9 开始/停止与退出实际生效。详见 [visual-review/native-observations.json](visual-review/native-observations.json)。
- 单独 Swift 解码工具首次使用旧模块缓存遇到 `/tmp`/`/private/tmp` 重复模块错误并退出 139；换新临时缓存后同工具成功。它不是 Unity C#/Shader 编译错误；未修改 Opus 实现。

## 实际查看的图像及现象

### O3 路线对照

已打开 D6 与 O6 的 `015/016/021/022/023/024` 六对、全部 12 张原图及六张原像素并排图。逐图路径、SHA、相机差异及观察记录见 [visual-review/route-observations.json](visual-review/route-observations.json)、[route-pairs/provenance.json](visual-review/route-pairs/provenance.json)。这是相同路线事件名；记录的相机位置差 0.00453–0.01372 单位，yaw 差 -0.181906 至 +0.115784 度，不能称严格逐像素同机位。

- 015/016 码头：没有看到大面积发白叠层或强网格；这两帧没有形成严重房屋遮挡。
- 021/022 主屋背面：房屋为实色；屋顶直线分段、背墙竖向阴影仍可见。这两帧不能说明淡出切换表现。
- 023：D6 较连续的浅绿色透明树冠，在 O6 变为细密网点；曲线及部分多边形外缘仍可见。
- 024：O6 的 UI 下方几乎整片 3D 画面出现高对比密集网格，伴随斜向明暗/色带；窗和多边形硬边仍可辨，Lulu 能隔网点看到。保留原图，未改亮度或裁切来隐藏。

### O3 原生操作

实际从主屋前用键盘向西、向北到树下，再向东到主屋后侧。第二次最终位置 (-0.578516, 0.025000, 11.220000)，相机 yaw 仍 0 度。实时截图以及解码帧 320/400/490/580 已打开：树干/树冠遮挡区呈细密点阵；末段几乎全景出现浅绿与深色块组成的点阵，UI 保持不透明。

鼠标完整绕转 **未完成**；“恢复时是否闪烁/跳动、切换瞬间风动是否中断、房屋亮度颜色是否突变”均 **未验证**。没有用自动路线代替这项原生操作。两次键盘录像保留：

- [manual/o6-native-keyboard.mp4](manual/o6-native-keyboard.mp4)：1078 帧，编码 167.116933 s；源录制达到 1 GiB 上限停止。
- [manual-02/o6-native-keyboard-02.mp4](manual-02/o6-native-keyboard-02.mp4)：590 帧，F9 人工开始/停止，约 88 s。各自 `.encoding.json` 核对所有原帧 SHA 和 VFR 时间；原始 PNG 留本机。只实际查看操作截图和指定解码帧，未声称连续观看全部视频。

### O5 谷仓 / O4 地面与天空

已逐张打开 `fixed/` 全部 12 张，以及 O6/D6 `fixed-pp-on/` 的 pasture、spawn、overview、house-front、close-house-road 各五张，共 22 张 1600×900 原图。精确清单及逐图观察见 [visual-review/fixed-observations.json](visual-review/fixed-observations.json)。五对固定机位的记录相机及后处理字段一致，D6 快照 SHA 未变。

- 谷仓在牧场右后侧，画面占比变小；主屋门和一层可见；羊和猪在所看画面中分离。筒仓在谷仓右侧、靠池塘方向。
- 出生点右下角仍有谷仓绿色屋顶边缘，但占比比 D6 小；前景出现草堆。
- 谷仓绿色屋顶可见深色瓦缝和亮边；仅凭这些机位不能确定镜像后的所有法线/主光响应。未匹配负缩放或碰撞警告，见日志记录。
- `fixed-pp-on/close-house-road.png` 路面主要呈浅黄，未清楚辨认独立圆点；标准 `fixed/spawn.png` 在 Lulu 左侧有浅圆形斑点。保留两种图像设置，未混称同条件。
- overview 的远处地平线为灰白雾色，远端对比减弱；斜向的两条地面外缘仍能看到。没有描述为方形边缘已消失。
- 所看固定 12 张没有全黑、洋红或整栋主屋完全缺失的画面；这不是美术验收。

### O4 动物与环境声

[ambient/o6-ambient.mp4](ambient/o6-ambient.mp4) 实际采集 384 帧；recording.elapsedSeconds=56.136940，首/末帧时间约 0.046031/56.086029 s，编码 384 个视频样本/56.090900 s，最大 PTS 误差 0.000016656 s。直接使用原 recording.json，没有复制或重写停止清单。编码 readback 见同名 `.encoding.json`。

已实际打开解码帧 99/112/139/167：前景粉猪头部/眼耳轮廓在 139 附近有轻微差异；牛在后中、羊在右侧，这些采样帧的差别太小，无法据此确认二者呼吸/转头是否明显或夸张。已解码 12 帧但仅声明查看上述四帧；连续播放感受保持未验证。记录见 [visual-review/ambient-observations.json](visual-review/ambient-observations.json)。

环境声 **未试听**。实际 WAV：[runtime-audio.wav](ambient/20261024-170858-156/ambient-proof/runtime-audio.wav)。音量、刺耳程度和循环感留给用户实际试听。

## 采集环境与存储

Apple M5、24 GiB、macOS 26.4 (25E246)、Metal；内置屏，无外接屏，窗口 1280×720、非全屏、电脑质量档。主会话与有效风动 A/B 均在接电后执行。正式采集期间本任务不运行 Editor、渲染、编码、压缩、看图或并行 agent 工作；本任务 Vite 已停止。

系统不是只有游戏进程：Codex/ChatGPT、Unity Hub/许可服务、闲置 Chrome/Safari、Finder/系统服务仍存在；用户暂停后仍有三个 claude 进程，快照 CPU 约 0.3–0.4%。IDEA 退出经复查。最初电池 13%，等接电后又遇到 IDEA/系统高负载，自动审批拒绝了一次启动；用户退出 IDEA 并暂停其他任务后重新取样、获准启动。完整快照见 [environment-observation.json](environment-observation.json) 和引用文件。没有连续测量后台 CPU 归因或机身温度。

空间不足时，按用户授权将历史 385 件 Profiler raw 无损 gzip 至仓库外 `/Users/haowen/GameProject/local-evidence-archives/r07-profiler-20261025/`，逐件解压 SHA/字节数相同后释放未压缩重复副本。原 53,755,540,402 bytes，压缩后 15,072,357,811 bytes。索引/恢复说明：[storage-maintenance/](storage-maintenance/)。压缩在性能采集前完成。本轮 O6 `.data` 与全部原始视频帧仍本机保留，不上传；压缩时间线、录像、WAV、代表图、完整日志和清单上传。

## 性能原值

主会话 summary 的 `wallFrameTimeMs`：mean **8.54513893050077 ms**；p95 **9.689125000001297 ms**；maximum **91.54212499993264 ms**；`unscaledDeltaExceedsWallFrames` **0**。这些与下表的 Unity unscaledDeltaTime 指标分别记录，未互换；[performance-original-values.json](performance-original-values.json) 同时保存三会话原值。

以下原样附入 performance-table.md，不作原因、预算或验收判断。

# 性能记录原值

r06 had no binary Profiler; r07 captures include CPU Profiler and ten-second rotation flush overhead. Same M5, 1280x720, Desktop and 20 mature plots, but profiler overhead is not subtracted. D6 final route moves two west-house intermediate points 0.6m east to avoid the inherited fence endpoint; the 31 points and key stops remain, but this is not an identical-path A/B comparison. No causal or acceptance conclusion.

| 阶段 | 有效秒 | 圈 | 帧 | 均值 ms | P95 ms | 最大 ms | 二进制 Profiler |
|---|---:|---:|---:|---:|---:|---:|---|
| r06 baseline | 917.684 | 7 | 109241 | 8.3926 | 8.3672 | 1859.2706 | 关 |
| D5 | 912.723 | 7 | 102399 | 8.7010 | 8.5100 | 19762.5446 | 开 |
| D2 | 912.725 | 7 | 103695 | 8.8013 | 8.8560 | 19056.6597 | 开 |
| D3 | 312.691 | 2 | 36132 | 8.6539 | 9.0690 | 225.7145 | 开 |
| D4 | 912.739 | 8 | 105841 | 8.6175 | 8.9825 | 2658.1440 | 开 |
| D6 | 912.750 | 8 | 99359 | 9.1232 | 13.0045 | 5273.0780 | 开 |
| O6 | 912.693 | 8 | 106807 | 8.5450 | 9.4375 | 90.6556 | 开 |
| O6 performance-wind-off | 312.713 | 2 | 36472 | 8.5724 | 8.3733 | 3727.3924 | 开 |
| O6 performance-wind-on | 312.734 | 3 | 37219 | 8.4022 | 8.9289 | 172.9845 | 开 |

只采集和列值；原因、预算和验收由 Opus 判断。Main Thread / Render Thread 不可用项不能当作 0ms；温度未测。

## 交回范围与未完成项

已完成的采集项均待 Opus 验收。仍需原生鼠标完整环绕、连续切换及动物动态观感检查；环境声由人试听。当前图像中的网格/色带和地面远缘已保留证据，是否修订由 Opus 判断。未执行 O7、Android 或其他平台；未修改 Lulu。

本机开发包：`Builds/r07/O6/development/LuluFarm.app`。工程生成产物：`Assets/Farm/Scenes/FarmWorld.unity` 与独立 `Assets/Farm/GeneratedR08/`。本次改动文件列表、可上传证据 SHA 和本机原始数据路径分别见 `changed-files.json`、`evidence-files.json`、`local-raw-inventory.json`。构建包保持本机；使用相同分支、锁定编辑器和 3.1 命令可重建。本报告没有将执行完成标为用户美术认可或性能结论。
