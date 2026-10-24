# r07 O6 Mac 执行记录 — 第二轮（2026-10-24）

本轮状态：**失败**。按新增第 2.5 节完成空跑和正式重签后，从 3.1 执行一次生成。Unity generate 退出 0，已生成固定图；但包装脚本检出 6 个受保护旧材质被改写，退出 1，**development 未启动**。本记录仅描述执行和画面，不作验收结论。

第一轮基于 cfb6818 的导入哈希失败记录保留在 [attempt-01/REPORT.md](attempt-01/REPORT.md)，其原始日志仍在本目录。此次输入为后续提交，不能将两轮失败混为同一原因。

## 基线与已执行命令

- 仓库：`pangzero/lulu-farm`；分支：`opus/r07-o6-continue`。
- 输入提交：`7e1571104ae68c77fb7474652654456b602703d9`。
- `git fetch origin opus/r07-o6-continue`、`git merge --ff-only origin/opus/r07-o6-continue`、`git lfs pull` 均退出 0。执行前工作树干净，原有 O6 快照已存在。
- Unity 仍为 `6000.3.16f1`，包锁和 Opus 源码未改。
- **未重做第 2 节快照，未运行 ConfigureAndImport。**

| 步骤 | 命令 | 状态 | 实际结果 |
|---|---|---|---|
| 2.5 空跑 | `python3 Scripts/opus-r07-restamp-path-migration.py` | 已完成，待 Opus 验收 | exit 0；五项 checks 全 true；applied=false |
| 2.5 正式 | `python3 Scripts/opus-r07-restamp-path-migration.py --apply` | 已完成，待 Opus 验收 | exit 0；五项 checks 全 true；applied=true；原记录已备份 |
| 3.1 | `python3 Scripts/r07-run-editor.py O6 generate development` | 失败 | Unity generate exit 0；包装器 exit 1，6 个 changedProtectedFiles；development 未执行 |
| 3.2 | `python3 Scripts/r07-run-player.py O6 route` | 失败 | 前置检查失败，未执行 |
| 3.3 | `python3 Scripts/r07-run-player.py O6 ambient` | 失败 | 前置检查失败，未执行 |
| 3.4 | `python3 Scripts/r07-run-player.py O6 performance` | 失败 | 前置检查失败，未执行 |
| 3.5 | `python3 Scripts/r07-run-player.py O6 performance --label wind-off --wind off --seconds 320`，然后 `python3 Scripts/r07-run-player.py O6 performance --label wind-on --seconds 320` | 失败 | 两个会话均未执行 |
| 3.6 | `python3 Scripts/r07-run-editor.py O6 export`，以及分别追加 `--profiler-directory Evidence/r07/O6/profiler-wind-off` / `Evidence/r07/O6/profiler-wind-on` | 失败 | 无采样，三次均未执行 |
| 3.7 固定图索引 | `python3 Scripts/r07-evidence-index.py O6` | 已完成，待 Opus 验收 | exit 0；30 组固定图相机/分辨率记录一致；路线 0、性能会话 0；生成 metrics.json、compare.html |
| 3.7 保护校验，恢复前 | `python3 Scripts/r07-final-integrity.py O6` | 失败 | exit 1；403 项中 6 个旧材质变化，结果保存在 attempt-02/final-integrity-generated.json |
| 保护内容恢复 | 对六个变更材质保存前后字节，再恢复至执行前 HEAD | 已完成，待 Opus 验收 | 六件恢复 SHA 均等于冻结清单基准；没有继续构建 |
| 3.7 保护校验，恢复后 | `python3 Scripts/r07-final-integrity.py O6` | 已完成，待 Opus 验收 | exit 0；403 项，changedFiles=[]；这是清理后的状态，不覆盖生成时失败事实 |
| 3.7 性能表 | `python3 Scripts/r07-compare-performance.py O6` | 失败 | 未采集性能，未执行 |
| 3.8 原生窗口 | 打开 O6 开发包并用键鼠检查 | 失败 | 本轮无开发包，未执行 |

后续“失败”项均因前置检查失败而未执行，没有对应的进程退出码，也没有运行后的错误判断。

## 2.5 重签事实

空跑和 apply 的五个检查全部为 true：

`stampMatchesPreMigrationSnapshot`、`prefixReplacementOnly`、`stampStatusImported`、`stampHasNoIssues`、`stampNotAlreadyCurrent`。

旧 registry SHA 为 `5f1de0afeb014c5cf9971745ab149f93dd43805520739f25f2c226017afe450b`，现 SHA 为 `308cbb262c6c8ffd343154fc7c71a3bad0919d6dddb7796caeaf0a4a47a12a34`，218 处路径前缀迁移。工具备份了原始 stamp；实测备份与第一轮只读副本逐字节相同。重签没有重建模型或 Prefab。

证据：[空跑](import-stamp-resign-dryrun.json)、[正式重签](import-stamp-resign.json)、[旧 stamp 副本](attempt-02/import-stamp-before-path-migration.json)、[重签后副本](attempt-02/import-stamp.json)。正式 apply 只运行一次。

## 本次保护检查失败

完整日志：[generate-20261024-141736.log](generate-20261024-141736.log)，122,902 bytes、1,119 行；SHA256 为 `3d7fccf8923e8c169ef47acd24ca7570519a7fec07163156212e913b82a9ce2d`。

[执行 JSON](generate-20261024-141736-execution.json) 中 Unity exitCode=0，但 changedProtectedFiles 有六件。包装器随即退出 1，没有进入 development。该生成日志未找到 C# 编译错误或 Shader error，也未找到负缩放/碰撞相关警告；运行时和开发构建尚未检查。启动期 Licensing Error 保留在完整日志及 [上下文](attempt-02/generate-error-context.txt)。

六件均位于 `Assets/Farm/Materials/OcclusionFade/`：

| 文件 GUID 前缀 | 来源 |
|---|---|
| 73284d9… | S01 主屋 |
| cf6c92d… | S01 主屋 LOD1 |
| 74ce7fb… | E08 树 |
| 8403be2… | E08 树 LOD1 |
| cc48e14… | E09 树 |
| 13224fa… | E09 树 LOD1 |

它们均列入 `Evidence/r07/D5/before/protected-lulu.json`，但语义上是**主屋和树的淡出材质**，不是 Lulu 模型本体。六件文本差异都只有两项：删除 `_ALPHAPREMULTIPLY_ON`，以及 `_SrcBlend: 1 → 5`。没有对应材质纹理引用、颜色或模型几何的差异。

只读代码对应：Builder 第 289/563 行先调用旧 `FarmOcclusionSetup.Configure`；该方法读取已有材质，在第 102 行写 SrcAlpha、第 108 行关闭 premultiply、第 114 行置脏，并在第 72 行 SaveAssets。随后 Builder 第 387 行才调用新 Dither Apply；新方法另存 GeneratedR08，不撤销前面的旧材质写入。本轮未修改这条生成链，也未改保护清单。

证据：[变更分析](attempt-02/protected-change-analysis.json)、[生成后保护校验](attempt-02/final-integrity-generated.json)、[完整生成差异](attempt-02/generated-working-tree.patch)、[恢复记录](attempt-02/protected-restoration.json)。六件前后原始文件位于 attempt-02/protected-before 和 protected-after。

为保留旧资源，已在留证后将**仅这六件**恢复为执行前 HEAD 字节；未把恢复后的空变化结果当成生成成功，未绕过检查启动包。请 Opus 修订旧淡出材质的写入路径或明确保护策略后再接续。

## 实际查看的图像

生成了 12 张标准图及 18 张后期开启图。索引中 30 组新旧 position/target/fov/width/height 全部相同。实际打开查看了后期组下列五张 O6 原图、五张 D6 原图，并查看了五组并排图：

| Shot | Observed image content |
|---|---|
| `pasture` | O6谷仓在画面右侧，主屋门和一层正面露出，前方仍有围栏与Lulu。羊与猪轮廓分离，可见羊脚。筒仓在谷仓画面右侧、靠池塘。绿色瓦面和深色瓦缝可见；镜像法线与多角度主光关系未验证。 |
| `spawn` | D6右下大片绿色谷仓屋顶占据前景；O6仅右下边缘保留一部分谷仓屋顶/墙面，中间围栏及道路露出，前下方可见移位草捆。 |
| `house-front` | 两版主屋门、灯和台阶均可见；O6右边缘谷仓占画面面积减少。左前梨树树冠仍遮住部分画面。 |
| `overview` | O6谷仓更小且更靠右。D6顶部浅色地面尖角和直边对蓝色天空较明显；O6天空更灰白、顶部边缘对比较低，但左右地面/天空分界仍可辨认，未记录为完全消失。 |
| `close-house-road` | 两版道路呈大块浅黄色。D6靠台阶的轻微方块色差较易辨认，O6该处色差较弱；原图中未能清楚辨认独立圆点，圆点形状未确认。右侧阴影位置有变化。 |

[查看五组并排证据](attempt-02/same-camera-pairs/)；D6 在左、O6 在右。单张原图 1600×900，拼接图 3200×900；工具显示拼接图时缩至 2048×576，原图也已分别查看。拼接仅原像素并排，未调整曝光、色彩、尺度或灯光，左右半图与原 RGB 像素逐字节核对。其余 25 张 O6 图已保存，**未实际查看**。

这些是编辑器固定机位输出，不能替代 Player 路线、原生窗口操作或动态判断。未作美术、法线或渲染验收结论。

## 尚未执行与未验证

- O3 路线 021–024、015/016：没有本轮路线截图，未检查抖动淡出、半透明叠层或网点。
- 原生窗口房后与树下旋转：未执行；闪烁、风动连续性、淡入淡出颜色/亮度跳变未验证。
- 动效录像、环境声：未采集；**未试听**。
- 31 点路线、碰撞、镜头、人工键鼠：未执行。
- 主会话及风动 A/B：未执行；没有 wallFrameTimeMs mean/p95/maximum 或 unscaledDeltaExceedsWallFrames 数值，没有性能表、Profiler .data 或时间线。
- macOS 开发包未构建，其他平台未测。没有设备性能结论。

## 环境与工作区

本轮使用同一 Mac 和锁定编辑器。开始前未发现同工程 Editor 或游戏进程；观察到 Hub/许可证客户端、Codex、Vite/esbuild 等进程。因流程未到性能采集，没有性能期间的电源、外接显示器、全屏或并发程序记录，不能借用首轮准备记录冒充性能现场。没有同时采集与编码、看图的情况，因为本轮根本未采性能。

当前本地 `FarmWorld.unity` 和新 `GeneratedR08/` 仍保留 Builder 输出；六个旧材质已恢复。生成时的场景、新材质和 meta 的精确副本在 [attempt-02/generated/](attempt-02/generated/)，旧材质生成后状态另存在 protected-after。未把这些变更直接提交到正式 Assets；没有手工修改场景或 Opus 代码。Unity/包版本、原始模型、r06、旧 Lulu 源文件均未主动修改。

第 2 节 before 快照保留原字节，未重建。第一轮 REPORT、命令记录、机器记录、保护校验和文件清单已归档到 attempt-01，完整首轮日志保留原路径。当前提交范围仅 O6 证据目录。

## 供 Opus 接续的脚本记录

只读查看 `r07-run-player.py` 时发现：O6 的 requiredDuration 当前固定为 900 秒，未根据 `--seconds 320` 改为 300 秒。按计划跑 A/B 时可能得到 requiredDuration=false；此项是**代码条件检查，尚无实跑结果**。本轮未修改脚本或运行更长会话绕过条件。

本次完成的是重签执行、生成尝试、失败留证和部分固定图观察。3.1 保护关卡仍失败；3.2–3.6、性能汇总及 3.8 未完成，交由 Opus 处理后接续。
