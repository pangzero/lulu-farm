# r07 DeepSeek 任务线 · 进度（2026-10-24）

用户在 D1 完成后要求停手，因此本轮只交付 D1。以下为实际状态，不是验收结论。

| 编号 | 任务 | 状态 |
|---|---|---|
| D1 | S02 谷仓派生和入场 | **已完成，待 Opus 验收**（证据 `Evidence/r07/D1/`） |
| D5 | 界面整理 | 未开始（代码无改动） |
| D2 | 渲染设置 | 未开始 |
| D4 | 装饰批量摆放 | 未开始 |
| D6 | 动感 | 未开始 |
| D3 | 地面和道路 | 未开始（Opus 的 `Docs/r07-ground-shading-spec.md` 已存在，方案已解锁） |
| D7 | 15 分钟 Profiler 采集 | 未做（D1 只跑了 31 点路线 + 12 机位 + 开发构建） |

## 开始 D5 前已经回滚干净

停手前曾短暂改过两处 D5 相关代码，已全部撤回并核对：

- `Assets/Farm/Scripts/Runtime/FarmHUD.cs`：与 r06 源包内同名文件 **SHA256 完全一致**
  （`9c806b0b…4c61`），即零改动。
- `Assets/Farm/Editor/FarmProjectBuilder.cs`：与 r06 源包同名文件 diff，只剩下 D1 的 S02 放置块
  （`Place("S02",…)` + `Footprint(barn,.98f)` + 羊位置）和三行注释，没有其它残留。
- 没有生成 `Builds/macOS-release/`，没有 `Evidence/r07/D5/`。

## D1 交付物与包

- 场景 / Prefab / 包都由 `Scripts/rebuild-macos.sh` 重新生成；旧包已归档到
  `Builds/macOS/archive/20261023-182520-66795/`。
- 当前 `Builds/macOS/LuluFarm.app` = D1 开发构建（Succeeded，0 error / 0 warning）。
- 31 点路线、12 固定机位、静态度量都在 `Evidence/r07/D1/`，同机位对照页是同目录下的
  `compare-r06-r07.html`。

## 仍需注意

- `FarmProjectBuilder.cs` 里运行时字段 `sceneRevision` 仍为 `integration-r06`，所以路线 JSON 的
  `revision` 显示 r06；场景内容已经是 r07 D1。
- D1 的已知问题（筒仓方位、主屋遮挡、尺度）写在该目录 `REPORT.md` 第 5 节，等 O5 判断。
