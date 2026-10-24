# D1 · S02 牧场谷仓派生和入场

状态：**已完成，待 Opus 验收**
日期：2026-10-24（Asia/Shanghai）
执行者：DeepSeek 任务线
基线：integration-r06（`Docs/AGENT-HANDOFF-20261024.md`）

本报告只记录实际执行与实测数据。技术检查 ≠ 视觉初审 ≠ 用户美术认可；本项**没有**做美术认可，也不写"通过"。

---

## 1. 做了什么

1. **登记 S02**：在 `lulu-studio/public/models/unity-integration/manifest.json` 仿照 S01 增加 S02 条目，并把 `S02` 从顶层 `deferred` 列表移除（现为 `["C12","C16"]`）。S01 记录逐字段未改。
2. **新增派生执行脚本** `lulu-studio/tools/unity_assets/run_s02_r07.py`：复用现有 `process_bvh.py`（与 `run_atlas.py` / `run_facility_lods.py` 同一入口），但因为需要给 LOD0 传 2048 贴图分辨率、给 S02 单列三角面预算，没有改动原有两个 runner 的资产表。
3. **Blender 4.5.3 LTS** 生成两份派生：
   - `atlas-r01`（LOD0）：目标 38000 三角面，贴图 2048×2048
   - `atlas-lod1-r01`（LOD1）：目标 11500 三角面，贴图 1024×1024
   两份都用现有流程：先 weld、再按预算 Decimate、全新 UV atlas、BVH 最近面颜色/法线传递、导出 GLB、重新导入回读、五视图渲染。
4. **同步进 Unity**：`python3 Tools/sync_assets.py --ids S02`。`asset-registry.json` 从 73 条变 74 条，逐条比对确认**只新增 S02，其余 73 条没有任何字段变化**（含 Lulu）。
5. **Builder 放置**（`Assets/Farm/Editor/FarmProjectBuilder.cs` 的 Pasture 段）：
   - `Place("S02", new Vector3(1.8f,0,-.1f), pasture, 180)` —— 门朝 -Z（牧场门方向），世界高度 3.0 m。
   - `Footprint(barn,.98f)` —— 实心盒状碰撞覆盖整个占地（约 3.37 × 3.07 m），模型上的大门是装饰、没有室内，门洞不可进入。
   - 羊从 r06 的 `(1,0,-1.5)` 移到 `(0.6,0,-2.9)`：原位置落在谷仓占地内。
   - 谷仓占地 `x 0.08–3.52 / z -1.66–1.46`；饲料槽 S09 在 `x 3.9–4.9`、动物均在谷仓南侧，都没有被压到。北侧围栏在 z=1.9，谷仓后沿 z=1.46，留 0.44 m。
6. **完整重建 + 12 固定机位 + 开发构建 + 31 点路线**（D7）。

## 2. 实测数据

| 项目 | 原件 | atlas-r01 (LOD0) | atlas-lod1-r01 (LOD1) |
|---|---|---|---|
| 三角面 | 707,180 | 38,000 | 11,498 |
| 顶点 | 380,095 | 35,634 | 13,275 |
| 贴图 | baseColor 4K / metalRough / normal 4K（JPEG） | basecolor 2048² + normal 2048² | basecolor 1024² + normal 1024² |
| GLB 字节 | 36,520,836 | 7,387,044 | 2,385,996 |
| SHA256 | `d4299d1e…a1b095` | `f38c4d05…ec1d` | `fb501baa…0f58` |
| 拓扑（derived） | — | boundary 0 / nonmanifold 0 / zero_area 0 / finite true | 同左 |

- 原件 SHA256 在派生完成后**重新实测仍为** `d4299d1ea171c7970fbabd7266e2cd6af93f0b8726ff0e5c5003a6bf00a1b095`，未被改动。
- `original_unchanged: true`（两份 metrics.json 都有记录）。
- Unity 内实测（`GenerateAndReview-static-validation.json`）：S02 占位包围盒 3.439 × 3.004 × 3.130 m，LODGroup 两档 38000 / 11498，导入错误 0、警告 0。
- 开发构建：`Evidence/build-macOS.json` = Succeeded，0 error / 0 warning。

## 3. 实际看过哪些截图

Blender 五视图（材质 + 灰模）在 `blender/atlas-r01/`、`blender/atlas-lod1-r01/`：

- **实际打开逐张看过**：`material-quarter`、`material-front`、`material-back`、`clay-quarter`、`original-material-quarter`（LOD0）；`material-quarter`（LOD1）。
- 其余 `material-side/top`、`clay-front/side/back/top`、`original-material-back` 只取文件、未逐张目视。

Unity 12 固定机位（`unity/world-review-r07/`）：

- **实际打开看过**：`overview`、`pasture`、`house-front`。
- 其余 9 张（`spawn`、`fields`、`pond`、`house-back`、`pond-east`、`field-fence`、`dock`、`landscape-back`、`overview-close-diagnostic`）只归档、未逐张目视。

路线截图（`route/<timestamp>/0xx-auto-*.png`）：实际打开看过 `011-auto-6-pasture-gate.png`（牧场门口地面视角）。

同机位对照页：`compare-r06-r07.html`（左 r06、右 r07，12 组并排；左图来自 `Evidence/world-review-20261023-015045/`）。

## 4. 没做成 / 未做

- **草垛没有切开**。Meshy 生成时草垛和底座是连体几何，本次派生完整保留，没有做任何分离、重拓扑或局部重建。是否切开属于 O5 判断。
- **没有做室内**，也没有做可开启的门。门是贴图/几何装饰，整栋为实心碰撞。
- **没有把谷仓加进 `FarmOcclusionSetup` 淡出系统**。靠近时靠相机碰撞（BoxCollider）推近，不产生透明层。若 Opus 希望谷仓也淡出，需要另做。
- **手机档（MobileURP）没有实测**，S02 在手机档的 LOD/贴图表现未验证。
- **没有做视觉验收或美术认可**，也没有人工键盘漫游本项。
- **没有改 `Docs/r07-ground-shading-spec.md` 相关的任何地面/光照内容**（属 D2/D3）。

## 5. 已知问题（交给 Opus 判断）

1. **筒仓在谷仓西侧（-X）**，参考图 `barn-silo-ref-01.png` 里筒仓在谷仓东侧。当前是门朝 -Z 的摆法（分工文档要求），要同时满足"门朝 -Z"和"筒仓在东"，只能镜像几何或在派生阶段重排，本次没有做。
2. **牧场机位下谷仓遮住主屋正面下半部**。`pasture.png` 里主屋的门和一层被谷仓挡住。分工文档给的初始位置 `(1.8, 0, 0.2)` 会挡得更多，本次已往南让到 `z=-0.1`（再往南会压到羊和饲料槽之间的通道）。
3. **尺度偏大**：worldHeight 3.0 m 对应占地 3.44 × 3.13 m，占牧场宽度约 36%；总图里大约 25–30%。worldHeight 按分工文档"先设 3.0"执行，是否调小属 O5。
4. **谷仓与世界高度是按竖直包围盒整比缩放的**（和 S01 同一套 `worldHeight / b.size.y`），筒仓顶部到 3.0 m。
5. **`sceneRevision` 仍写着 `integration-r06`**（`FarmProjectBuilder.cs` 运行时字段），本轮没有改；路线结果 JSON 的 `revision` 字段因此仍显示 r06，这不代表场景是 r06。

## 6. 31 点路线与构建结果

- **31/31 点**：`automated-route.json` 里 `status = completed_input_route_visual_and_manual_ui_pending`、`reachedWaypoints = 31`、`plannedWaypoints = 31`、`completedLaps = 1`、`loopingWithoutTeleport = false`。全程 131.0 s，末点 `returned` 位置 ≈ `(-0.24, 0.025, 3.16)`。
- 这是**模拟输入事件**（虚拟手柄），`applicationFocused = false`，不是人工键鼠记录，也不代表 UI 或设备验收。
- 路线中途没有出现 `auto-route-blocked-*` 截图，也没有 `stopped_by_human_input` / `unexpected_pause_during_route` 事件。
- 路线截图 25 张在 `route/<timestamp>/`，JSONL 记录完整（`events.jsonl`、`route-samples.jsonl`、`performance-configurations.jsonl`）。
- 开发构建：`Evidence/build-macOS.json` = `Succeeded`，792,397,119 字节，0 error / 0 warning；包在 `Builds/macOS/LuluFarm.app`。
- 静态度量：`GenerateAndReview-static-validation.json` = `static_checks_pass_runtime_and_visual_pending`，`sceneErrors` 空，316 个静态碰撞体，74 个资产。
- 本项**没有**采集 Profiler 15 分钟数据（分工里 D7 的 15 分钟采集是本轮收尾时统一做，D1 只跑路线 + 机位 + 构建）。

## 7. 文件清单

新增：

```
lulu-studio/tools/unity_assets/run_s02_r07.py
lulu-studio/public/models/unity-integration/atlas-r01/S02.glb
lulu-studio/public/models/unity-integration/atlas-lod1-r01/S02.glb
lulu-studio/assets-source/unity-integration/atlas-r01/S02.blend
lulu-studio/assets-source/unity-integration/atlas-lod1-r01/S02.blend
lulu-studio/review/unity-integration-20261018/assets/S02/**            （metrics / 五视图 / review-settings）
lulu-farm-unity/Assets/Farm/Art/S02/**                                  （sync_assets 生成的 glTF 暂存）
lulu-farm-unity/Assets/Farm/Prefabs/S02.prefab                          （Builder 生成）
lulu-farm-unity/Evidence/r07/D1/**                                      （本目录）
```

修改：

```
lulu-studio/public/models/unity-integration/manifest.json               （+S02 条目；deferred 去掉 S02）
lulu-farm-unity/Assets/Farm/Data/asset-registry.json                    （+S02 条目，其余 73 条未变）
lulu-farm-unity/Assets/Farm/Editor/FarmProjectBuilder.cs                 （Pasture 段放置 S02、移动羊）
```

未改动：S02 原件、S01 及其它全部资产源、`Delivery/r06-20261023/`、`locomotion-r08`、`lulu-studio` 任何已有 review 版本。

重新生成的场景与包：`Assets/Farm/Scenes/FarmWorld.unity`、`Builds/macOS/LuluFarm.app`（旧包已由 `rebuild-macos.sh` 归档到 `Builds/macOS/archive/20261023-182520-66795/`）。
