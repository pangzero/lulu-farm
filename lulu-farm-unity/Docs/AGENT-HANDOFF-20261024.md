# 噜噜农场：交给后续 agent 的接手说明

整理日期：2026-10-24（Asia/Shanghai）。接手基线：2026-10-23 的 **integration-r06**。这是一份交接入口，不代表继续制作、重新运行验收或新的用户美术认可。本次只核对现有文件与记录，未改模型、场景、代码或历史交付包。

## 1. 当前交付状态

完整农场已有可运行的 macOS 开发候选。Unity 实际导入 73 件主资源与 68 个 LOD 载荷；场景引用 59 种资产 ID，按总图建立单栋主屋、20 块田、中央牧场、右侧池塘／码头／摊位及连接道路。其余已导入动物可作为库资源使用。

实际完成：31/31 点模拟输入路线（非人工全程漫游、无瞬移）、原生窗口走动／拖动／UI 隔离／暂停／换装／画质、同机位田地阶段几何切换、三次场景重入对象检查、12 张固定图＋25 张路线图复核，以及 15 分钟独立持续测试。1277 个真实录制帧已编码为 187.549 秒视频，并打开六个解码关键帧核对；没有完整逐帧观看声明。

**M0–M6 尚未全项验收完成。**偶发长帧未解决，透明树／房屋有淡色叠层，用户美术待验收。Android 真机由用户明确暂缓，模块地区 404 尚未解决；Windows／iOS 未构建实测，Intel Mac 未实测。

## 2. 必须交付的六类内容

| 内容 | 当前入口 | 接手用途／边界 |
|---|---|---|
| Unity 可编辑工程 | `lulu-farm-unity/`；冻结快照 `Delivery/r06-20261023/LuluFarm-Unity-source-r06.zip` | 场景、Prefab、脚本、材质、Shader、LOD、碰撞、输入、质量配置、锁定包版本和重建工具。保留全部 `.meta`。 |
| 美术源及采用版本清单 | 相邻 `lulu-studio/`；本工程 `Docs/ASSET-INTEGRATION-STATUS-20261023.md` 与同名 JSON | 原始 GLB、选定派生、可编辑 Blender 源、贴图、来源 SHA256、metrics、review-settings、acceptance。Unity 源 ZIP 不含全部上游 Blender／Meshy 原件。 |
| 目标图与产品约束 | 相邻 `art-concepts/05-assembled-farm-preview.png`；整合方案、原执行计划、两个工程的 AGENTS | 保持原图区域关系、3D 马卡龙方向和旋转第三人称，不重做已具备的整套资产。 |
| 当前状态与工作队列 | 本文；`Docs/FINAL-ACCEPTANCE-20261023.md`、`Docs/KNOWN-ISSUES.md`；资产工程 `review/unity-integration-20261018/progress.json` | 区分已做、未完成、未验证、用户暂缓和美术待认可；含失败方法与下一步。 |
| 可运行基线与验收证据 | `Delivery/r06-20261023/LuluFarm-macOS-r06.zip`、`LuluFarm-walkthrough-r06.mp4`、`LuluFarm-evidence-r06.zip` | 接手前先看／运行 r06，再做同条件比较；图像、日志、性能和人工／模拟输入记录分开。 |
| 复现方法与完整性 | `Docs/MACOS-交付与操作说明.md`、`Scripts/rebuild-macos.sh`、`Packages/`、`Delivery/r06-20261023/delivery-manifest.json` | 编辑器与依赖版本、命令、设备条件、文件哈希；已有包装脚本只做过语法／dry-run 检查，其等价 Editor CLI 步骤实际执行过。 |

同一台电脑接手：上述目录已经存在，给 agent 本文路径及工程访问权限即可，无需重新复制几 GB 文件。另一台电脑接手：按下面的迁移要求传文件。

## 3. 先读哪些文件

本机工作目录：`/Users/haowen/GameProject/farm-game/`。先读取两份 AGENTS，再按以下次序核对：

1. `lulu-farm-unity/Docs/FINAL-ACCEPTANCE-20261023.md`、`Evidence/final-acceptance-r06-20261023.json`、`Docs/KNOWN-ISSUES.md`。
2. `lulu-studio/review/unity-integration-20261018/progress.json` 和 `lulu-studio/docs/噜噜农场_Unity-URP整体整合方案.md` 的最新检查点。
3. 原执行计划 `/Users/haowen/Documents/Obsidian Vault/04 project/Farm/农场美术资产 Blender 分批执行计划.md` 的最新检查点、相关质量条款和失败停止规则。
4. 实际打开总览图 `art-concepts/05-assembled-farm-preview.png`、认可的 `lulu-studio/review/farm-assets/B01/B01-r03-candidates.jpg`、B01/B02 验收记录和本次 r06 实景图／录像。固定总览图是检查工具，玩法没有俯视模式。
5. `lulu-farm-unity/Assets/Farm/Data/asset-registry.json`、`Docs/ASSET-INTEGRATION-STATUS-20261023.json` 与 `lulu-studio/review/unity-integration-20261018/delivery-asset-index-20261023.md`。
6. `lulu-farm-unity/Docs/MACOS-交付与操作说明.md`、运行脚本目录的 `README.md`、本轮任务相关代码。

历史文档中有许可证未激活、尚未实际导入、幼苗尚未制作等旧快照。以对应日期的实际报告和最新用户指令解释，不把旧文字当作当前阻塞，也不删除失败历史。许可已激活。原生档案索引的 Unity pending 不覆盖后续实际 r06 验收记录。

## 4. 当前采用版本与用户边界

- Unity 农场的 Lulu 固定使用 **locomotion-r08**，源头 full-r02。用户明确要求本轮先不动 Lulu 模型，允许先运动、后续换新模型。保留原裤和 FabricUV 第二套坐标。不要自动接入 r11 或失败修复版。
- 资产工程另有 head-approved-v1、eye-r01、polish-r01 等独立美术工作。它们属于另一条制作记录，**没有因此替换 Unity 的当前角色**。以后更换需要明确选择和重新验证骨骼、动画、换装、比例；接手整合工作不得顺带修它们。
- 一栋中央主屋采用登记的 Meshy S01 派生；B14 保留替代，B02 是立面样段。不能把三者同时当主屋入场。
- 14 种作物只有幼苗、成熟两阶段。幼苗是四个 Meshy 族群原型映射成十四个派生，不称十四份独立原始建模。
- 动物采用 `unity-animals/game-r04` 及登记的牛来源。场景放总图的五种代表动物，其余十种在库内，不把未摆满十五种当漏导入。
- S02 牧场棚屋、C12 西葫芦、C16 葱继续暂缓，无占位；牧场使用围栏、入口门、饲料槽。
- 当前范围是世界、控制、画风与运行基础。播种收获、背包交易、动物 AI、室内、开船、游泳和商店上架需要另列后续任务。
- 原件、认可版本与旧候选不覆盖；改动保存独立版本。技术、视觉初审、用户美术、资源优化、设备测试分开记录。

## 5. 下一步的优先级与定位入口

| 优先级 | 工作 | 已有证据／代码 | 本项完成的条件 |
|---|---|---|---|
| P0 | 定位明显长帧，再作定向修复 | `Evidence/performance-long-frames-r06-20261023.json`、`Evidence/mac-performance-r06-analysis-20261023/`；`FarmPerformanceSession.cs`、`FarmRuntimeDiagnostics.cs`、`FarmRoutePlayback.cs` | 独立 Profiler 时间线建立原因；同设备、同档位、同密度、无截屏录像重新持续测量，报告尾部和最长帧，不能只报平均值。 |
| P1 | 改善树／屋顶淡出叠层 | `Evidence/world-visual-independent-review-r06-20261023.json`；`FarmCameraOccluder.cs`、`FarmThirdPersonCamera.cs` | 田地、屋后、码头等旋转时人物清楚，淡出／恢复无明显层叠伪影；回归镜头碰撞与接地。 |
| P2 | 同原图复核整场画面并定向完善 | 总图、r06 12 张固定图、路线图 | 保持区域关系、单主屋、田格 1.2×1.2 与物种高度差；新旧同机位比较，用户认可另记。 |
| P3 | 核对剩余输入、资源与退出期日志 | 原生 UI 记录、registry、`Docs/KNOWN-ISSUES.md`、交付 `先读我.md` | 实体 Shift 组合按键可独立复核；不擅自减坏高面例外。退出时线程及约 2.39MB Immediate MemoryLeaks 清理信息仍保留，不能宣告无泄漏。 |
| 用户条件满足后 | Android 模块、APK 与真机 | 当前 Android 暂缓记录和手机质量／触控代码 | 真机连接可用后独立构建、触控、性能与温度测试；不由 Mac 手机档切换推定通过。 |

性能基线：Apple M5／24GB／macOS 26.4／Metal，1280×720，电脑档，20/20 格全成熟。有效 917.684 秒、7 圈、109241 帧；均值 8.393ms，P95 8.367ms，最长 1859.271ms；8 个统计窗口含 >100ms 长帧，其中 3 个含 >1 秒长帧。每窗口可有多次长帧，不能将窗口数称为精确卡顿次数。

主线程 Recorder 因原生单位 `TimeNanoseconds` 适配缺失而不可用，渲染线程计数器也不可用；低频 FrameTiming CPU/GPU 样本另有实际值。**诊断适配问题与游戏长帧原因是两件事，尚未证明因果。**不可用计时不能解释成 0ms。当前没有温度数据。

## 6. 已停止的失败方法与必须保留的修复

- Batch Editor 虚拟鼠标回归出现非零预期但实测全零，多次尝试后已停止该测试方法。真实聚焦 Mac 窗口的拖动、UI 起点隔离与暂停有独立通过证据；两者不能混写。不要继续同样的夹具小参数重试，也不要抹掉失败记录。
- Lulu 局部补片／封口等失败修模路线已停止，且用户冻结当前模型；不要在性能任务中继续修角色。
- 成熟玫瑰采用独立语义图集修复 `atlas-semantic-r06`／`atlas-lod1-r04`，旧颜色阈值方法停止。
- 宽叶幼苗保留 r02 背脉与体积，不复用失败的统一降面；旧原生幼苗三份失败小样不当正式输入。
- 非 Lulu glTF 法线维持 **Default 类型＋线性采样**，由 `Assets/Farm/Editor/ImportPolicy/FarmAssetImportPolicy.cs` 保证原始 RG 通道。不要恢复造成色带的 NormalMap 通道重排，不对冻结 Lulu 套该批修正。
- 地面使用逐像素世界位置雾，保留已修复的色带问题；船位根据测量抬高 2.9cm 后船内干燥；UI/Default 已显式保留以免运行包按钮洋红。
- 同一核心问题连续两轮仍失败，停止该方法、留对照和说明；不降低标准宣告通过，其他独立工作继续。

## 7. 复现与交付检查

固定版本：Unity **6000.3.16f1**、URP **17.3.0**、Cinemachine **3.1.5**、Input System **1.14.2**、glTFast **6.20.0**。以 `Packages/manifest.json` 和 `packages-lock.json` 为准，不自动升级。

本机 Editor：`/Users/haowen/GameProject/farm-game/.unity-install/Editors/6000.3.16f1/Unity.app`。

在 Unity 工程目录先执行只读预检：

```bash
bash Scripts/rebuild-macos.sh --dry-run
```

需要重新生成场景／构建时，先保存独立修改、退出同工程 Editor，再选择 `bash Scripts/rebuild-macos.sh` 或 `--build-only`。默认脚本重建导入、Prefab 和场景，会替换生成结果；场景与材质的持久修改应同步对应 Builder／导入政策，否则下次生成可能丢失。`--build-only` 需要匹配登记 SHA 的场景生成戳和导入记录；新机器仅解压源 ZIP 不具备原来的完整 Evidence，请先恢复相关证据或运行完整流程生成自己的记录，勿伪造戳。

验证路线：主屋前 → 田地 → 牧场入口 → 饲料槽 → 池塘 → 码头 → 渔产摊位 → 主屋背面 → 返回。检查旋转、缩放、碰撞、遮挡、阶段、换装、画质、UI 输入归属和重入。修改后检查实际图片和运行包，性能另启无录像／截图会话。源或导出变动按原计划重开源、回读模型、固定五视图和必要种植对照。保存实际日志、画面、来源与逐项状态。

## 8. 交给另一台机器时

已备好的四份文件在 `Delivery/r06-20261023/`：

- `LuluFarm-Unity-source-r06.zip`：1,728,186,755 字节。可编辑 Unity 项目，含已暂存的美术运行资源和说明，不含 Library／Temp／Logs 缓存，也不含全部上游 Blender 源。
- `LuluFarm-macOS-r06.zip`：378,701,641 字节。冻结的可运行 Mac 基线，ad-hoc 签名、未公证，实际只测 M5。
- `LuluFarm-evidence-r06.zip`：40,329,606 字节。精简实际检查证据，不能替代全部上游验收档案或原始1277帧。
- `LuluFarm-walkthrough-r06.mp4`：164,853,213 字节。实际漫游录制，约6.8fps是录制采样频率，不代表游戏帧率。

一并传 `delivery-manifest.json` 与**本文**。本文是 10 月24日新增说明，不在冻结的 r06 源 ZIP 中；无需为附加一份说明改动既有 ZIP 的哈希。

若接手者要继续修模型／烘焙／重导入，另外交付 `lulu-studio` 中索引引用的原件、派生 `.blend`、GLB、贴图、来源清单、相关制作脚本与 review 档案；完整原生资产包目前没有另做一个便携 ZIP，不能误称已包含于 Unity 源包。按清单选择文件时连同外部纹理／缓冲等依赖一起复制。参考图和最新整合／执行计划也要附上。

建议保持 `farm-game/lulu-farm-unity`、`farm-game/lulu-studio`、`farm-game/art-concepts` 的相邻目录关系。原始来源清单和部分文档含本机绝对路径；迁移后按清单重新定位，保留来源哈希和旧快照，勿只改路径后假称所有源已复验。Unity 已暂存资源可独立打开；重新暂存上游 GLB 的 `Tools/sync_assets.py` 需要相邻资产工程与来源清单。Unity 编辑器安装、许可证与各平台构建模块由新环境自行准备。

## 9. 可以直接发给接手 agent 的启动文本

```text
请接手噜噜农场现有 Unity＋URP 工程，先读取：
/Users/haowen/GameProject/farm-game/lulu-farm-unity/Docs/AGENT-HANDOFF-20261024.md

按交接文档读取两份AGENTS、最新验收／问题／进度、整合方案和原执行计划，实际查看总图、认可基准、r06实景和运行包。以integration-r06为接手基线，先核实现场文件是否有后续变更；不从头重做。

本次继续农场整合收尾：优先用实际Profiler证据定位明显长帧并定向修复，其次改善树／房屋透明叠层，再做同条件整场画面与输入回归，产出独立新版本电脑包、实际录像和性能／验收记录。先说明你核实的当前状态和第一项行动，再持续执行。

Lulu模型继续冻结，使用当前locomotion-r08，不自动接入资产工程的独立头／眼／身体试验。保留全部原件、认可历史和r06对照。Android真机暂缓；不自行扩展播种收获、交易背包、动物AI、室内等后续玩法。按文档保留失败方法停止规则和逐项诚实验收，不把技术通过写成用户美术认可。
```

这段文本用于用户启动后续任务；本文件本身没有向其他聊天或 agent 发送消息。
