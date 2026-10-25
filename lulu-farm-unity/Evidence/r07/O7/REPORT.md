# O7 Mac 执行记录

状态：已完成，待 Opus 验收。仅执行、采集与描述；无技术/美术/性能验收结论。

## 输入与边界

- 分支：`opus/r07-o7-sky-island`；输入提交 `8da91976b110a9b397d26e5014f812696932db45`。
- 依据：`Docs/R07-O7-执行计划-20261025.md`、O6 执行规则、Opus 续作进度和三个 AGENTS.md。
- 本机根：`/Users/haowen/GameProject/farm-game`。Unity 固定 `6000.3.16f1`；未升级包，未重签导入，未运行 ConfigureAndImport，未修改 Opus Editor/Runtime/Shader 源代码。
- O6 对照仅快照一次，61 项；`snapshot-verification.json` 实际 SHA256 重查 changed=[]。图片来自 O6；代码/设置快照是 O7 执行前输入，不声称代码来自 O6。
- 生成场景由已有 Builder 生成；场景和新 GeneratedR08/GeneratedR09 资源随本次提交保存。受保护原件、Lulu、r06、锁定包及道路地面共403项，`final-integrity.json` changedFiles=[]。
- 执行跨北京时间2026-10-25凌晨与下午；日志名称/内容中的时间为 UTC。原生和性能是不同会话。

## 计划步骤与实际结果

| 步骤 | 实际命令/操作 | 记录结果 |
|---|---|---|
| 1 | fetch、checkout、lfs pull；`r07-evidence-index.py O7 --before O6` | 输入8da9197，快照61项一次 |
| 2.1 | `python3 Scripts/r07-run-editor.py O7 generate development` | 两步exit0、changedProtectedFiles=[]；开发包Succeeded、0 error/0 warning |
| 2.2 | `python3 Scripts/r07-run-player.py O7 route` | 第二次31/31、4检查true；首次失败完整保留 |
| 2.3 | `python3 Scripts/r07-run-player.py O7 ambient` | exit0，373帧/56.0846秒、WAV；按真实时间戳编码 |
| 2.4 | `python3 Scripts/r07-run-player.py O7 performance` | exit0、五检查true；有效912.711609秒、8圈；未做A/B |
| 2.5 | `python3 Scripts/r07-run-editor.py O7 export` | exit0、protected=[]；92/92原始段导出timeline gzip，全部完整解压CRC核对 |
| 2.6 | `r07-evidence-index.py O7`、`r07-compare-performance.py O7`、`r07-final-integrity.py O7` | 30个固定机位对照、8行性能历史记录、403项保护哈希无变化 |
| 2.7 | 新证据helper启动开发包；cua_repl键盘实走、R回正、F9帧录制 | 东南西北4墙截图、溪流截图、82.9156秒连续牧场、主屋背面和树下录像；原生会话exit0 |

开发包：`Builds/r07/O7/development/LuluFarm.app`，820,926,709字节，构建10.41228秒。包在本机，未上传Builds。`build-development.json` 的自动字段 device=not_tested 保持原文；实际本机运行证据另见 route/performance/native，不覆盖生成器字段。

生成产物记录：`sky-island-r10.json`、`animal-walk-r10.json`、`occlusion-dither-r09.json`。计划文字称7个新Shader，列出的新文件实际为6个；Editor日志确认这6个编译/序列化，并包含既有LivingSurface-r08的编译记录。未把“保存了Shader”当成实际运行证据。

## 失败与日志

1. 首次路线只有1/31，applicationFocused=false，Player exit0但wrapper exit2。归档 `attempt-01/route-unfocused/`。退出时真实 NullReferenceException：FarmRoutePlayback.SaveResult:281 → Stop:252 → OnDisable:297。未删报错、未改代码。
2. 第二次相同命令和31点数组，原生激活并发送未绑定动作的Q取得焦点，31/31、25张路线图、完成事件122.140701秒；4检查true。不能仅由两次结果断言首次异常根因。
3. generate/development/export完整Editor日志保留。未匹配到C#/Shader编译错误；出现许可握手Error随后初始化继续、CS0108 audio遮蔽、ILPP重复提示、生成材质名称不匹配及关闭线程提示。构建摘要0warning不能代替这些Editor诊断。export收尾还有 `debugger-agent: Unable to listen on 43`，下一行仍为正常退出，原文一并保留。
4. performance.log:39–45 有 `Releasing render texture that is set to be RenderTexture.active!`，栈 FarmProfilerCaptureR07.NextChunk:49 → Update:42。完整上下文见 `log-review/final-runtime-performance.log.keyword-context.txt`。不解释原因、不绕过。
5. 原生工具drag返回noWindowsAvailable，按计划使用键盘/R；多非modifier组合键被拒绝后改顺序按键。一次工具报告窗口由用户改变，重新读取状态恢复焦点；发生于视觉会话，不在性能会话。
6. 首次牧场录制59.711578秒，不满足60秒；独立补录82.915649秒/578帧。前一段未删除或拼接充数。

完整日志和关键词前后20行在 `log-review/`；所有实际异常均保留。只按执行计划交回，不修改Opus代码。

## 实际画面观察

### 天空岛、岛边与水系

已实际打开全部12张fixed、6组O6/O7后处理固定图原图，以及四墙和溪流5张原生帧。逐图路径、哈希和观察见 `visual-review/fixed-observations.json` 与 `native-review/`。

- 总览能看到岛形外缘、草顶/崖壁分层、云海、积云和远处小岛；小岛深色底部在部分角度可见。未在所查图发现大面积洋红或缺材质黑块。
- 四墙实际位置：西(-16.220,7.141)、南(-16.220,-11.220)、东(16.220,1.340)、北(12.810,11.220)，坐标为(x,z)，根部y约0.025。每张图有原始帧JSON和SHA256，直接复制像素，无重绘。
- 向外走时在不可见边界停下，前方仍可见草地，具有“撞空气”现象。没有用瞬移替代走查。
- 东侧Lulu实际站到溪流水面；池塘与溪流之间仍隔连续岸石和草带。侧向画面只能看到溪流末端很小一段向下水线，当前跟随角度未看到完整瀑布落差或明确水雾。
- 南/北原生图中花草看似接草面，未见清楚空气缝隙；这些角度不能排除全部浮空。暖光带在默认跟随视角未清楚辨认，侧崖浅黄色土层不直接当作暖光带证据。
- 云层轮廓和蓝灰间隙可见；不把明暗分层自动判为地平线接缝。固定图详细描述另列。

### 动物与飞鸟

- `native-review/pasture-continuous-75s.mp4` 实际82.9143秒（文件名75s为预估名，录制实际82.915649秒），来自单个连续牧场会话578帧，未切机位、未拼接。
- 另有四机位ambient录制56.0846秒（编码视频56.0443秒，减去首帧PTS）；不能替代上述连续长片。实际打开20张ambient与25张长片解码样帧，长片包含约0.14–0.15秒间隔连续帧。审阅方式是解码样帧，不声称连续播放看完每帧或试听。
- 牛羊猪鸡鸭移位/转向可见，牛蹄相对身体有微小变化；羊猪腿有围栏遮挡。鸭约30px高，左右姿态轻微变化，尚不能确认与迈步同步。不能据此确认无滑步。
- 存在二维投影局部重叠；未凭投影断言三维互穿。所查样帧未见明确走出围栏，但未逐帧排除穿谷仓/槽/草垛/彼此。自动路线完成31点，不能据此推定所有动物碰撞均无问题。
- 鸟在固定图和北墙/东侧原生帧为较小灰剪影。另实际查看12张连续解码帧，所选时段无法可靠辨认鸟翼和尺寸，扑翼仍未验证；见 `visual-review/birds-observations.json`。尺寸适宜性和动作观感由Opus/用户判断。

### 淡出与光线

- 实际逐张打开O6/O7 route 015/016/021–024共12张原图，并保存6组源像素并排图和机位差异。Lulu附近透明区域可见，外围仍有明显细颗粒及斜向明暗/色带；不写“网格完全消失”。
- **022不能叫严格同机位**：O6实际相机距3.478869、O7约5.099991，相机位置相差1.616436m；其他组也有约0.003–0.035m偏差。固定图30组的相机/分辨率参数相同，场景光线本身是本轮修改。
- 原生实际走至主屋背后约(0.095,8.399)，树下相机有缩近，R回正与步行覆盖多个角度；大范围颗粒层和Lulu附近较清楚的区域可见。不是鼠标360°验证。视频 `native-review/house-back-tree-fade.mp4`。另实看4张解码帧，末帧623中Lulu清晰圆区外仍有大面积密集红绿色点阵，见 `visual-review/native-fade-observations.json`。
- O6/O7固定图中屋顶/木材略偏暖，阴影位置/轮廓变化；未定量测影长，不推断变长程度。未改曝光来制造对比。
- 环境声：**未试听**。实际WAV在ambient会话目录，交用户/Opus试听。

## 性能原值与环境

有效采集912.711608887秒，8圈，107340帧；全部采样窗口applicationFocused=true，configurationUnchanged=true，停止时路线仍运行。无截图、编码或看图操作混入性能会话。

| 主会话字段 | 原值 |
|---|---:|
| wallFrameTimeMs.mean | 8.502867005161287 ms |
| wallFrameTimeMs.p95 | 9.526875000005930 ms |
| wallFrameTimeMs.maximum | 1099.388290999996798 ms |
| unscaledDeltaExceedsWallFrames | 2 |

Main Thread / Render Thread unavailable 的原因与原值保留，不按0ms解释；温度未测。Profiler导出过滤到>=0.1ms及roots，共13,589,570个事件；本机原始.data保留全部标记。导出过滤不是原始样本删除。

机器：Mac17,2、Apple M5、24GB、Metal、macOS26.4。游戏1280×720窗口、电脑质量档、20成熟田格。测试后系统只报告内置Color LCD（3024×1964物理像素，逻辑1512×982@120Hz），无外接屏记录。

**环境限制**：用户两次确认接电；实际pmset在启动前交流电/电池之间切换，主会话中和结束均报告电池供电，电量约95%→85%。不能称全程插电。MoonBrowser仍开着，初始点样本renderer53.8%/GPU helper20.9%，Codex及系统服务也在；未观察到Unity Editor、其他游戏、编码、压缩同时运行。按计划如实交回这些干扰条件，不能称完全排除后台负载的基准。见三份performance-environment文件。

以下是 `performance-table.md` 原文，保留不同Profiler条件与路径限制，不作归因：

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
| O7 | 912.712 | 8 | 107340 | 8.4437 | 8.9156 | 2964.8178 | 开 |

只采集和列值；原因、预算和验收由 Opus 判断。Main Thread / Render Thread 不可用项不能当作 0ms；温度未测。

## 交回范围与本机保留

- 提交：本报告、执行日志/JSON、fixed与route图、O6对照快照、同机位对照、原生四墙图、实际MP4/WAV、抽查解码图、压缩timeline、metrics、review-settings、逐项保护/哈希记录、Builder生成场景/资源。
- 本机开发包：`Builds/r07/O7/development/LuluFarm.app`。不将可打开包或编译成功等同于验收。
- 原始Profiler：92件、16,618,085,561字节，留 `Evidence/r07/O7/profiler/*.data`。完整PNG序列3108帧留本机；`local-raw-inventory.json`和各frames.jsonl保留哈希。远端不上传原始.data或全套帧PNG。
- 历史空间整理：依照已有授权，将177件O6/D6原始Profiler共29,596,231,713字节无损压缩至8,156,332,221字节；逐件解压SHA256核对后释放旧原始副本。归档 `/Users/haowen/GameProject/local-evidence-archives/r07-profiler-20261025-o7-space`；账本在`storage-maintenance`。旧报告/时间线/图像/资产未改。恢复时按账本输出原路径，并核对原SHA；不覆盖现存文件。
- 当前O7原始Profiler未压缩或删除；没有把本次包覆盖r06。

待Opus处理：技术日志与异常、溪流接岸/水面行走/隐形墙表现、O3颗粒和色带、动物完整步态/滑步/碰撞、飞鸟和瀑布观感、性能环境与数据解释。用户美术认可、声音主观评价和其他平台均未验证；没有扩展玩法。
