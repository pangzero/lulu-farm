# D5 界面整理

状态：**已完成，待 Opus 验收**。

## 做了什么

- 新增 `FarmPresentationModeR07`，由 Builder 接入。默认正常模式隐藏 Inspect 按钮、检查面板和底部调试栏；顶部保留标题、回正、暂停、模式开关。F3 与按钮均可切换模式。
- 开局按键提示单独显示 5 秒，再用 0.7 秒淡出；不复用常驻调试栏。既有 FarmHUD、输入、角色及相机脚本不改。
- 独立开发包与发布包位于 `Builds/r07/D5/`；发布包未启用 Development 选项，实际截图没有开发水印。
- 版本戳改为 `integration-r07-D5`。后续阶段代码由 `--r07-task` 控制，本轮场景只启用 D5。

## 实际执行和看过的证据

- `build-development.json`：Succeeded，0 error、0 warning，792,409,431 字节。`build-release.json`：Succeeded，0 error、0 warning，586,551,330 字节。
- `route/20261023-184645-328/automated-route.json`：31/31 点。是实际 Player 的模拟输入路线，不是人工全程漫游；25 张路线图全部借助 `route-contact/01–07.jpg` 查看。
- `fixed/` 的 12 张标准图逐张查看：overview、overview-close-diagnostic、spawn、fields、pasture、pond、house-front、house-back、pond-east、field-fence、dock、landscape-back。`compare.html` 为 D1 场景对 D5 同机位。
- `ui-development/20261023-184607-889/ui/` 和 `ui-release/20261023-184949-362/ui/` 各 4 张均实际查看：开局提示、正常稳定、调试检查面板、返回正常。按钮行为以真实 UI 回调脚本记录，JSON 明确标为 scripted。
- 独立原生 UI 操作记录见发布运行 `events.jsonl`：65.658s 切至 debug、71.520s 返回 normal；玩家位置不变。原生 UI 工具遇到同 bundle 多实例后截图指向旧窗口，未把这些截图当作完整人工 UI 验收。已关闭额外实例。
- 补充后期开启基线 `fixed-pp-on/` 18 张已全部查看（`fixed-pp-contact-r02/01–05.jpg`），包括六处近景。早期 ARGBHalf 直接读回的偏暗图另存 `fixed-pp-on-linear-readback-r01/`，不用于新对照；改为显式 sRGB 输出后相机、曝光、灯光均未改，见 `capture-readback-correction.json`。

## 采集数据（不下性能结论）

- 第二轮 `performance-r02/20261024-001055-043/performance/summary.json`：同一 M5、1280×720、电脑档、20 格成熟、无截图录像；配置未变，预热后 912.7228 秒、7 圈、102,399 帧，均值 8.7010ms、P95 8.5100ms、最长 19,762.5446ms。1Hz 采样窗口无 >3 秒缺口且始终聚焦。数值原样交给 Opus，未判定原因或设备性能达标。
- `profiler-r02/` 保存 92 个实际 `.data`，全部由锁定 Unity 载入并导出 92 份 `.timeline.json.gz`，索引见 `export-index.json`。时间线保留所有线程根节点及 ≥0.1ms 标记；细节留在二进制。切段开销包含在测量中，与 r06 无 Profiler 基线的差异必须由 Opus 分析。
- 首轮 `performance/` 在 564.7→1467.2 秒间有约 902.5 秒窗口缺口，不能充当连续 15 分钟结果。原始数据保留；`profiler/cpu-0055.data` 被 Unity 拒绝载入，错误记录保留，其余分段导出。第二轮临时 caffeinate 仅作用于该进程。
- Main Thread 原生单位不兼容和 Render Thread 不可用仍按原记录保留，不将不可用计数写成 0ms。温度未测。

## 未解决和已知问题

- 原有房屋／树木透明叠层、Lulu 腰部接缝和场景道路直角色块仍在，对应 O3、O1、D3；本项没有修它们。
- 发布首次构建出现 Burst 原生崩溃；原日志保留，后一次实际构建完成。期间辅助代码的编译错误已修复，失败日志未删。
- Profiler 切段日志出现一次 RenderTexture.active 释放警告；不在本项判断其与长帧的关系。
- 本机键鼠与脚本回调证据分开，Android 真机及其他平台未验证。用户美术与性能结论待 Opus／用户判断。

改动文件见 `changed-files.json`，实测汇总见 `metrics.json`。388 个冻结 Lulu 暂存文件与包锁在已执行编辑器步骤中核对未变；r06 交付和 S02 原件以本轮 preflight 记录为准。
