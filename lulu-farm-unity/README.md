# 噜噜农场 Unity 工程

当前状态（2026-10-23）：完整农场 r06 macOS 候选已构建并实际运行。73主资源、31/31路线、原生UI和三次重入检查已做；15分钟测试有效917.684秒，仍有偶发长帧，透明房屋／树叠层与Lulu冻结缺陷保留。尚不能把M0–M6全项或所有平台标记完成。交付入口 `Delivery/r06-20261023/`，状态与证据见 `Docs/FINAL-ACCEPTANCE-20261023.md`。Android按用户决定暂缓真机，Windows/iOS未测试；用户美术待验收。

编辑器已从官方 6000.3.16f1 发布下载并验证 Apple 签名，安装于：
`/Users/haowen/GameProject/farm-game/.unity-install/Editors/6000.3.16f1/Unity.app`

打开本目录作为 Unity 工程，主场景为 `Assets/Farm/Scenes/FarmWorld.unity`。`Assets/`（含 `.meta`）、`Packages/`、`ProjectSettings/` 一起保留；`Library/` 可由相同编辑器重建。

2026-10-23 已逐项核对 `Packages/manifest.json`、`Packages/packages-lock.json` 与实际 `Library/PackageCache/*/package.json`：全部 16 项直接依赖版本一致。URP 为 17.3.0、Cinemachine 为 3.1.5、Input System 为 1.14.2、glTFast 为 6.20.0、Unity UI 为 2.0.0、Test Framework 为 1.6.0，其余内置模块为 1.0.0。复现时保留锁文件，不自动升级。

## 数据和来源

- 原始、认可模型与独立派生源保留在相邻 `lulu-studio`，不覆盖。
- `Tools/sync_assets.py` 核对来源 SHA256，把明确版本转换为带外置纹理的 glTF 供 glTFast 导入。
- `Assets/Farm/Data/asset-registry.json` 记录当前暂存模型、原始来源、哈希、世界高度和状态。
- 接口源清单为 `lulu-studio/public/models/unity-integration/interfaces-manifest.json`，围栏步长 1.2，田格 1.2×1.2，岸高 0，水位 -0.105。
- Lulu 冻结使用 `locomotion-r08`，2026-10-19 用户明确允许先实现运动、后续换新模型；腰侧、颈部、腿顶缺陷仍记录为未通过美术，r09/r10 失败修复不接入。当前不改源模型；未来替换接口见运行说明的“Future Lulu replacement”部分。
- 法线贴图修正保存在 `Assets/Farm/Editor/ImportPolicy/FarmAssetImportPolicy.cs`：glTFast 6.20 读取原始 RG 通道，非 Lulu 法线纹理使用 `Default` 类型及线性采样，避免 Unity `NormalMap` 通道重排。独立 ImportPolicy 程序集在重新导入时继续执行；`/Lulu/` 被明确排除。重建脚本会检查修正没有回退，不重新运行临时的关法线诊断。

## 可复现执行入口

以下菜单是执行步骤，不是已经执行成功的记录：

1. `Farm/01 Configure and import`：URP 设置、来源适配 Prefab、LOD 和同条件对照 Prefab。
2. `Farm/01b Build representative calibration`：生成独立代表场景，实际确认主屋、前三种两阶段作物、Lulu、围栏、树与闭合岸线；不能代替完整农场。
3. `Farm/02 Build full farm scene`：按总图组装完整农场，单栋主屋、两阶段作物、中央牧场与右侧池塘。
4. `Farm/06 Acceptance - run static and fixed review`：真实 Unity 静态检查与固定图像；保存后仍需实际查看。
5. `Farm/08 Audit assembled contact and collision`：检查土格草地遮盖、作物根部、门净空、水面不可行走及码头碰撞与可见几何关系。
6. `Farm/07 Play simulated-input acceptance route`：模拟输入驱动现有控制器，卡住即记录停止，不瞬移、不冒充人工或真机测试。
7. `Farm/03 Build macOS development package`，随后实际运行包并操作完整路线。
8. `Farm/04 Build Android development APK`：需要官方 Android 模块、工具链与设备连接；状态单独记录。

可复现脚本为 `Scripts/rebuild-macos.sh`，先用 `--dry-run` 列出命令；默认刷新导入、生成完整场景并检查报告，再构建开发包。`--build-only` 使用已生成且登记戳有效的场景。脚本不重新暂存原始 GLB，保留已有运行包到归档目录；其实际重建结果需另行记录，语法／dry-run 检查不能当作执行成功。完整步骤见 `Docs/MACOS-交付与操作说明.md`。

## 操作和验收

键鼠与触控操作、路线与运行证据选项见 `Assets/Farm/Scripts/Runtime/README.md`。主镜头为 Cinemachine 透视第三人称，旋转、有限俯仰、缩放，相机相对移动；不增加俯视玩法镜头。

`Evidence/` 只保存实际编辑器、运行、构建输出。`first-editor-import.log` 是激活前的历史失败日志，已不代表当前状态；当前导入见 `import-report.json`／`import-stamp.json`，构建见 `build-macOS.json`，逐次日志与实际运行会话独立保留。图像、手工操作、模拟输入、用户美术和各平台设备状态分别记录，最终结论填入交付说明。

完整制作进度：`../lulu-studio/review/unity-integration-20261018/progress.json`。
