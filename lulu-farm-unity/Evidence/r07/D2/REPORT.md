# D2 渲染设置

状态：**已完成，待 Opus 验收**。

## 做了什么

按 `Docs/r07-ground-shading-spec.md` C 执行：Trilight 三色、主光 #FFF0DA／1.25／阴影 .55、雾 32–80；Desktop URP 阴影 40m／四级／中等软阴影，SSAO .45／.25／直接光 .15、不降采样、不 AfterOpaque。新 `FarmGlobalVolume-r03` 使用 Neutral、曝光 .1、对比 6、饱和 8、暗部偏色、Bloom .2 和暗角 .16。FarmSky 不改。

由 Builder 接入独立 `FarmRenderQualityR07`。桌面相机 HDR／后期开启；手机档沿用无 SSAO 的 renderer 并关闭 Bloom。现有 runtime、Lulu 和相机控制代码不改。参数见 `render-settings.json`，新增／生成文件见 `changed-files.json`。

## 实际执行与查看

- `build-development.json`：Succeeded，0 error、0 warning，792,610,944 字节。独立包：`Builds/r07/D2/development/LuluFarm.app`。
- 31/31 点实际 Player 模拟输入路线；全 25 张路线图已借助 `route-contact/01–07.jpg` 查看。包括阶段、三套短裤、手机／电脑档切换的脚本 API 记录，不称人工 UI 验收。
- `fixed/` 12 张标准机位全部查看（`fixed-contact/01–03.jpg`）；旧截图流程关闭后期的行为不改。
- `fixed-pp-on/` 18 张最终后期开启图全部查看（`pp-contact-volume-r02/01–05.jpg`）；房屋背面、树荫、田地三张近景另打开原尺寸查看。实际观察见 `visual-observations.json`。
- 新旧同相机、FOV、分辨率对照见 `compare.html`，30 个机位比较项记录在 `metrics.json`。
- 补充截图最初使用 SingleCameraRequest，发现锁定版本 URP 此入口不更新 Volume。原图保留为 `fixed-pp-on-no-volume-update-r01/`；改用 StandardRequest 后重拍，实际 Volume 栈记录为 Neutral／曝光 .1／Bloom .2／暗角 .16。见 `capture-volume-correction.json` 和最终 `review-settings.json`。真实 Player 的正常渲染本来就更新 Volume，路线和构建无需用偏暗／缺后期的诊断图代替。

## 采集数据（不下性能结论）

`performance/20261024-003339-040/performance/summary.json`：M5、Metal、1280×720、电脑档、20 格全成熟、无截图录像；配置未变。有效 912.7252 秒、7 圈、103,695 帧；均值 8.8013ms、P95 8.8560ms、最长 19,056.6597ms。原始路径以 `metrics.json` 的 source 为准。

`profiler/` 保存 92 份实际 `.data`，全部由锁定 Unity 载入并导出时间线，见 `export-index.json`。r06、D5、D2 原值并列于 `../D7/performance-table.md`；r06 没有挂二进制 Profiler，r07 包含十秒切段开销，不把这些差异直接解释成渲染成本或原因。Main Thread／Render Thread 不可用、无温度数据的限制继续保留。

## 已知问题与待判断

- 按 spec 的阴影明显变亮；白花／花椰菜局部对比减弱，Lulu 黄色和动物仍能辨认。是否符合美术方向由 Opus 判断，本项没有自行偏离给定数值。
- 更亮的雾色使远总览中外侧地面边界可见，已保留证据。道路直角色块仍在，下一项 D3 处理。
- 房屋背面原有竖向接缝及房屋／树的透明叠层仍在，留给原负责项；不修改 Lulu。
- 当前采集含长帧，交 O2 分析；未作性能验收结论。Android 真机、Windows、iOS、Intel Mac 未验证。

编辑器执行记录确认冻结 Lulu 文件与包锁未变。最终 r07 整合与发布交付包属于 Opus O6。
