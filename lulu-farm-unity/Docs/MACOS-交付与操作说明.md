# 噜噜农场 macOS 交付与操作说明

当前交付 **r06 macOS 完整农场开发候选**。完整世界和操作基础已运行检查；偶发长帧、透明遮挡外观及用户美术仍待解决或确认，未宣布所有平台完成。

| 交付项 | 结果 | 证据／入口 |
|---|---|---|
| Unity 源工程 | 73主资源实际导入，完整场景生成；固定版本依赖锁定 | `Assets/`、`Packages/`、`ProjectSettings/` |
| macOS包 | 实际构建0错误0警告，arm64＋x86_64；实际只测M5 | `Delivery/r06-20261023/LuluFarm-macOS-r06.zip` |
| 实际路线和UI | 31/31输入驱动路线；原生拖动、UI隔离、暂停、阶段／换装／画质通过所查案例 | `Evidence/final-acceptance-r06-20261023.json` |
| 田地阶段 | 固定机位实际点击并核对幼苗／成熟几何 | `Evidence/field-stage-manual-r06-review-20261023.json` |
| 画面初审 | 12固定＋25路线图已看；房屋／树透明叠层与模型细缝保留 | `Evidence/world-visual-independent-review-r06-20261023.md` |
| 录像 | 1277实际帧，187.549秒VFR，已核对6个解码关键帧 | `Delivery/r06-20261023/LuluFarm-walkthrough-r06.mp4` |
| macOS持续测试 | 有效917.684秒／7圈；普通帧预算良好但有明显长帧，未通过无卡顿验收 | `Evidence/mac-performance-r06-analysis-20261023/summary.md` |
| 用户美术 | 等待用户确认 | 技术／初审不代替认可 |
| Android | 用户暂不连接设备；模块地区404未解决，无APK／真机验收 | 手机控制和质量配置已保留 |
| Windows / iOS / Intel Mac | 未实测；前两者未构建 | 不由M5结果推定通过 |

完整逐项结论见 `Docs/FINAL-ACCEPTANCE-20261023.md`，文件哈希见 `Delivery/r06-20261023/delivery-manifest.json`。

## 工程与版本

工程目录是 `/Users/haowen/GameProject/farm-game/lulu-farm-unity`。用 Unity Hub 的“添加已有项目”打开此目录，编辑器选择 **Unity 6000.3.16f1（6.3 LTS）**。本机编辑器位于：

```text
/Users/haowen/GameProject/farm-game/.unity-install/Editors/6000.3.16f1/Unity.app
```

主场景为 `Assets/Farm/Scenes/FarmWorld.unity`，在编辑器打开后按 Play；`FarmCalibration` 是内部代表资产校准场景，不能作为完整农场交付场景。场景沿用原总图的左侧田地、后方单栋主屋与农产摊位、前方中央牧场、右侧池塘与码头／渔产摊位关系。

交付工程必须保留 `Assets/`（含全部 `.meta`、外置纹理与 glTF 缓冲）、`Packages/`、`ProjectSettings/`。`Library/`、`Temp/`、`Logs/` 是本机缓存，可由同版 Unity 重建。`Tools/`、`Scripts/`、`Docs/`、`Preflight/` 和 `Evidence/` 保存复现工具、来源与检查记录，也随源工程归档；不要把缓存当作源文件替代。

直接依赖锁定如下；传递依赖以 `Packages/packages-lock.json` 为准。复现时保留 `manifest.json` 与锁文件，不自动升级。

| 依赖 | 版本 |
|---|---|
| Universal Render Pipeline | 17.3.0 |
| Cinemachine | 3.1.5 |
| Input System | 1.14.2 |
| Unity glTFast | 6.20.0 |
| Unity UI | 2.0.0 |

已暂存的 Unity 资源位于 `Assets/Farm/Art/`，登记在 `Assets/Farm/Data/asset-registry.json`。打开工程和从这些资源重建不需要重新生成 Meshy 模型。重新从原始 GLB 暂存才使用 `Tools/sync_assets.py`，它依赖相邻的 `lulu-studio` 和明确来源清单；常规重建脚本不调用它。

## 重建 macOS 包

先保存工作并关闭此工程的 Unity 编辑器。脚本会检查编辑器版本、依赖锁文件和项目锁；不删除锁文件、不自动安装或升级软件。默认重建会按当前 Editor 代码重新生成 Prefab、材质配置与 `FarmWorld`，需要保留的手工场景改动应先单独归档。

```bash
cd /Users/haowen/GameProject/farm-game/lulu-farm-unity
bash Scripts/rebuild-macos.sh --dry-run
bash Scripts/rebuild-macos.sh
```

编辑器安装在其他位置时：

```bash
LULU_UNITY_EDITOR="/Applications/Unity/Hub/Editor/6000.3.16f1/Unity.app" \
  bash Scripts/rebuild-macos.sh
```

仅重建已生成场景的运行包：

```bash
bash Scripts/rebuild-macos.sh --build-only
```

默认执行三个已有入口，每一步使用独立 Unity 进程，保留真实日志：

1. `LuluFarm.Editor.FarmProjectBuilder.RefreshMaterialsAndImport`：以已保存的 URP 配置刷新导入，重建登记资源的 Prefab、LOD 与来源对照。
2. `LuluFarm.Editor.FarmWorldReview.GenerateAndReview`：生成完整场景、输出整场固定视图、静态检查与接触检查。图片仍需打开查看。
3. `LuluFarm.Editor.FarmProjectBuilder.BuildMac`：构建 `BuildOptions.Development` 的 macOS 应用。

脚本将每次日志与报告归档到 `Evidence/rebuild-macos-<UTC>-<PID>/`，检查报告属于本次执行且状态符合要求。原有 `.app` 先移动到 `Builds/macOS/archive/<UTC>-<PID>/`，新包固定输出到 `Builds/macOS/LuluFarm.app`。脚本成功只表示相应重建与报告检查完成，不自动标记运行或美术通过。

等价 Unity CLI 形态如下，`--dry-run` 会列出本机可直接使用的完整命令：

```bash
"/path/to/Unity.app/Contents/MacOS/Unity" \
  -batchmode -quit \
  -projectPath "/path/to/lulu-farm-unity" \
  -buildTarget StandaloneOSX \
  -executeMethod LuluFarm.Editor.FarmProjectBuilder.BuildMac \
  -logFile "/absolute/path/build-macos.log"
```

上述单独构建入口要求当前来源登记、导入和场景生成戳一致。整场固定视图使用真实 URP 渲染，默认脚本不加 `-nographics`。逐资产完整固定图的 Editor 入口是 `LuluFarm.Editor.FarmAcceptanceRunner.RunAll`，也可从 `Farm/06 Acceptance - run static and fixed review` 执行；它与完整路线操作是不同检查。

## 运行与操作

在 Finder 双击 `Builds/macOS/LuluFarm.app`。开发包使用ad-hoc签名、codesign完整性核对通过；未做Developer ID公证和外部设备分发验证；本说明不承诺商店或所有 Mac 均已验证。

| 操作 | 方式 |
|---|---|
| 移动 | WASD 或方向键，按相机朝向移动 |
| 跑步 | 移动时按住 Shift |
| 绕人物旋转／有限俯仰 | 在场景区域按住鼠标左键或右键拖动 |
| 远近 | 鼠标滚轮 |
| 回正相机 | R，或顶部“回正视角” |
| 暂停／继续 | Esc，或顶部“暂停／继续” |
| 检查面板 | 顶部“检查” |
| 退出 | macOS 的 Command-Q |
| 实际帧录像开关 | F9；部分键盘需 Fn-F9 |

镜头是中等距离透视第三人称跟随，可水平旋转，保留有限俯仰与缩放，没有俯视或正交玩法模式。鼠标从检查按钮开始的拖动已在实际Mac窗口确认不会转动镜头。Batch Editor鼠标测试夹具仍失败并已停止，不能与真实窗口结论混写。CUA未独立证明实体Shift长按，Run已由输入驱动路线确认，实体键盘组合项保留待用户复核。

检查面板里的“作物”依次切换 **混合种植 → 全幼苗 → 全成熟 → 混合种植**。混合种植只是两种阶段同时分布于不同田格，不是第三个成长态。“短裤”依次选择原版、蓝色星星、西瓜短裤，保留同版型和 FabricUV；“画质”切换电脑／手机配置。手机配置在 Mac 上仅用于观察质量差异，不能视为 Android 性能测试。

“保存当前画面”截取实际帧；“保存运行记录”输出运行 JSON；“返回起点”会明确瞬移并记录事件。完整路线验收中不要用“返回起点”代替走回。路线为：**主屋前 → 田地 → 牧场入口 → 饲料槽 → 池塘 → 码头 → 渔产摊位 → 主屋背面 → 返回**。

手机输入实现保留左侧虚拟摇杆、右侧拖动转镜头、双指缩放及走／跑按钮。当前用户暂不连接 Android 手机，实际触控、多指归属、设备温度和性能继续标为未验证。

## 证据保存与检查边界

默认运行证据位于 `Application.persistentDataPath/FarmEvidence/<UTC会话>/`。可指定一个绝对目录：

```bash
cd /Users/haowen/GameProject/farm-game/lulu-farm-unity
open "Builds/macOS/LuluFarm.app" --args \
  --farm-evidence "$PWD/Evidence/manual-macos-final"
```

使用新目录区分每次检查；游戏会在指定目录下创建会话。已有应用正在运行时先退出，确保新的启动参数生效。常用记录如下：

| 证据 | 含义 |
|---|---|
| `Evidence/rebuild-macos-*/` | 此脚本实际执行的导入、场景与构建日志、报告快照 |
| `Evidence/build-macOS.json` | 最近一次构建结果；不等于设备运行通过 |
| `Evidence/acceptance/*/static-validation.json` | Unity 中的资源、蒙皮、引用、阶段与场景静态检查 |
| `Evidence/scene-contact-audit.json` | 接地、田格、门口、水面与码头接触探针 |
| `Evidence/world-review-*/` | 实际 Unity 整场离屏视图，需要另行实际查看 |
| 运行会话中的 `route-samples.jsonl` / `events.jsonl` | 实际位置、相机、输入、阶段与事件；接近标记不等于完整操作通过 |
| 运行会话中的 `runtime-latest.json` | 设备、画质、分辨率、帧时与可用性标记 |
| 实际帧 PNG 与对应 JSON | 画面、相机状态与哈希 |
| `walkthrough-*/frames.jsonl`、`frames.ffconcat`、`recording.json` | 实际帧时间与录像来源；需编码后观看 |

F9 录像记录真实帧；已有 `Preflight/encode-vfr-recording.sh` 可在本机编码，或按运行目录里的 `frames.ffconcat` 使用 FFmpeg 保留实际时间间隔。录制、截图会影响性能，**设备性能单独重启一轮**，固定分辨率和质量档，不录制、不截图，再保存 JSON。换过画质或分辨率的混合会话不能当单档性能通过。

`--farm-route` 是模拟输入路线，会自动操作，必须与真人键鼠记录分开。它不能代替用户手工测试，也不能把卡住、瞬移或 API 切换称为手工走通。完整说明见 [运行控制与证据说明](/Users/haowen/GameProject/farm-game/lulu-farm-unity/Assets/Farm/Scripts/Runtime/README.md)。

## 原生资产与保留项

完整原生源、GLB、来源哈希、metrics、review-settings、acceptance 和历史图像引用已有 [资产交付索引](/Users/haowen/GameProject/farm-game/lulu-studio/review/unity-integration-20261018/delivery-asset-index-20261023.md)，不在此复制大表。其 [独立链接核对记录](/Users/haowen/GameProject/farm-game/lulu-farm-unity/Preflight/delivery-index-check-20261023.json) 包含 **362 个唯一档案链接**；这是档案完整性记录，不是本次最终 Unity 视觉或设备验收。源文件继续保留在相邻 `lulu-studio`，Unity 工程中的 `.meta`、Prefab、材质、布局、碰撞和 LOD 则独立归档。

Lulu 当前冻结使用 `locomotion-r08` 临时运动派生，源头为最新组装 full-r02；不修改角色源模型，不接入被拒绝的 r11 或失败修复候选。用户已允许先运动、后续换新模型；腰侧、颈部和腿顶等已记录外观缺陷仍保留，不能标为正式美术认可。角色控制与外观分离，后续替换时仍需重新核对骨骼、Idle／Walk／Run、短裤材质与比例。

作物保留 14 种的幼苗与成熟两阶段。幼苗来自四个共享 Meshy 原型的映射及派生，不宣称十四种完全独立建模。C12 西葫芦、C16 葱和 S02 牧场棚屋继续暂缓；牧场由围栏、入口门和饲料槽组成。场景只放一栋中央主屋，B02 立面样段不当完整主屋使用。

本次交付范围是完整世界、角色移动、跟随镜头、画风与运行基础。播种收获、交易背包、动物 AI、建筑室内、开船和游泳属于后续玩法，不包含在本次包的验收范围。正式移动端优化、签名分发和设备结论按平台分别继续记录；开发包不等于商店发布版本。
