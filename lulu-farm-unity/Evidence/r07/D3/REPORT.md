# D3 地面和道路

状态：**已完成，待 Opus 验收**。

## 做了什么

严格按 `Docs/r07-ground-shading-spec.md` B：新增 FarmGround-r03 Shader、Ground-polish-r03 材质和 2048×1024 RoadEdgeMask-r03。道路和路肩在地面材质中混合，RoadNetwork 保留，仅关闭 MeshRenderer；不改 CreatePaths、旧遮罩函数或旧 Shader。三色草地、双层扰动、.66–.98 过渡、细颗粒和近距碎石均使用给定数值。D2 光照不再调整。

`road-and-ground-geometry-check.json`：道路和地面网格及 meta 四项 SHA256 与改前一致。`ground-settings.json`：9 段道路、504 道路顶点和 228 地面顶点；RoadMode=1。改动列表见 changed-files.json。

## 实际执行与查看

- 开发包 `Builds/r07/D3/development/LuluFarm.app`；Succeeded，0 error、0 warning，798,997,373 字节。
- 实际 Player 模拟输入 31/31 点路线；25 张路线图在 route-contact/01–07.jpg 全部查看。不是人工全程漫游或手机验收。
- fixed/ 12 张、fixed-pp-on/ 18 张全部查看；房前、牧场门口、池塘道路三张近景另打开原图。r06-baseline/ 的 12 张也已全部查看（r06-contact/01–03.jpg）。
- compare.html 是 D2→D3 的 30 项同机位对照；compare-r06.html 是 r06→D3 的 12 张原始 PNG 透明度叠加，r06-camera-comparison.json 记录 12 个相机／分辨率一致。r06 对照包含 D1 谷仓和 D2 灯光差异，不把所有差异归因于道路。
- 牧场门口原叠层直角色块不再可见；道路边缘过渡变宽，近景仍有给定碎石公式形成的细小方形亮斑。细节见 visual-observations.json，美术判断交 Opus。

## 性能原值

M5／Metal／1280×720／电脑档／20 格全成熟，无截图录像。`performance/20261024-015305-476/performance/summary.json` 有效 312.6911 秒、2 圈、36,132 帧，均值 8.6539ms、P95 9.0690ms、最长 225.7145ms；配置未变，316 个采样窗口，无 >3 秒记录缺口，全部聚焦。

32 段原始 Profiler .data 已保留并全部由锁定 Unity 载入、导出时间线。见 profiler/export-index.json 和 ../D7/performance-table.md。Profiler 切段开销包含在数据中；与没有挂 Profiler 的 r06 不构成零开销对比。仅列实测值，原因和预算由 Opus 分析。

## 未做与已知问题

未改角色、透明淡出、房屋原竖线或远景地面边界；O3 透明叠层仍在。未做其他平台实测。路沿柔和程度与细小碎石效果需 Opus 判断，未自行偏离 spec 调参。Lulu、包锁检查无变化；最终 r07 整合包由 O6 负责。
