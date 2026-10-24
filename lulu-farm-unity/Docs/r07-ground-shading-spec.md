# r07 地面、光照与后期方案（O4，Opus 编写，供 D2/D3 执行）

日期：2026-10-24。依据：r06 实景截图（`Evidence/mac-player-route-r06-final/`）和总图 `art-concepts/05-assembled-farm-preview.png`。
所有改动都写进 Builder（`FarmProjectBuilder.cs` 的 `Lighting()`、`FarmLandscapePolish.cs`）和独立的新材质、新 Shader 版本。旧材质 `Grass.mat`、`WarmPath.mat`、`Grass-polish-r02`、`WarmPath-polish-r02` 保留不删。新版本统一命名为 `*-polish-r03`。

## A. 诊断（为什么看着简陋）

1. **路边的矩形色块**：道路网格（`RoadNetwork`）是单独一层 1.8 m 宽的四边形，两侧边缘用同一个 FarmGround Shader 画草。但它和地面网格（`GroundWithSoilAndPondOpenings`）的着色结果不一致，在门口、房前能看到深浅不同的直角矩形（加大对比度后在牧场门口那张截图里很明显）。这是"简陋感"最主要的来源。
2. **路沿过渡太窄**：遮罩只在中心距离 0.715–0.875 m 之间过渡（约 16 cm），边缘像贴纸。
3. **草地太平**：明暗只有 ±5% 的大块变化，而且只有两个色调。总图里的草地有三个色调、斑块更明显。
4. **环境光太暗太灰**：环境光三色是 天空 (.62,.73,.82)、地平线 (.54,.60,.57)、地面 (.32,.36,.26)，导致阴影偏灰黑，没有马卡龙风格那种通透感。

## B. D3：地面和道路（DeepSeek 执行）

### B1. 道路并进地面，消除矩形色块（必须做）
- 新建材质 `Ground-polish-r03`：`_RoadMode = 1`，遮罩用 B2 的新遮罩。把它挂到 `GroundWithSoilAndPondOpenings` 上。
- `RoadNetwork` 物体保留，因为遮罩要从它的网格里提取；只把它的 **MeshRenderer 设为 enabled = false**。不要删除，也不要改 `CreatePaths`。
- 验收要点：12 个固定机位上不能再有直角色块；道路位置和宽度与 r06 一致（同机位截图叠加比较）。

### B2. 新遮罩 `RoadEdgeMask-r03.png`（复制 `PolishRoadMask` 改一个新函数，旧函数不动）
- 分辨率 2048×1024。
- 边缘扰动改成两层：`wander = .045*sin(x*1.7+.6)*sin(z*1.3-.2) + .025*sin(x*4.1+1.9)*sin(z*3.7+.4)`（单位 m）。
- 过渡区间从 `.715–.875` 改为 **`.66–.98`**（约 32 cm 的柔和过渡）。
- 另外输出 G 通道作为"路肩"权重：`shoulder = smoothstep(.98,1.25,d) * (1 - smoothstep(1.25,1.55,d))`，也就是路外 0.3 m 左右的一条窄带，给 B3 用。

### B3. 新 Shader `LuluFarm/FarmGround-r03`（复制旧 Shader 另存，旧的不改）
在旧逻辑的基础上改这些：
1. **三色草地**：新增 `_GrassWarm = (.64,.76,.27)`。
   - `_GrassLow = (.40,.63,.17)`，`_GrassHigh = (.55,.75,.23)`（由 Builder 写入，不再按 ×0.89/×1.07 推算）。
   - 混合：`clouds` 的 smoothstep 改为 `(.30,.70)`；再叠一层 `warm = smoothstep(.62,.80, pigment(p*.11+float2(31.7,5.2)))*.55`，用 `lerp(grass, _GrassWarm, warm)`。
   - `_FineGrain` 提到 `.012`。
2. **路面**：`road = _RoadBase * tone`，加两项：
   - 路沿压暗：`edgeBand = roadWeight*(1-roadWeight)*4`（在过渡中间最强），`road *= 1 - .10*edgeBand`；
   - 碎石点：近处才显示，`pebble = step(.93, hash21(floor(p*4)))*(1-smoothstep(.02,.06,footprint))`，`road *= 1 + .06*pebble`。
3. **路肩**：采样遮罩 G 通道，`grass = lerp(grass, grass*float3(1.05,1.03,.92), .6*shoulder)`（路边的草略偏暖黄）。
4. 其余（雾、阴影、SSAO 关键字、阴影投射和深度 Pass）保持和旧 Shader 一致。

### B4. 验收证据（放在 `Evidence/r07/D3/`）
- 12 个固定机位 r06 对 r07 的同机位对比；另加 3 张近景：房前道路、牧场门口、池塘边。
- 性能：同 r06 条件下 5 分钟采样，报告均值、P95、最长帧。不下结论。

## C. D2：光照与后期（替换分工文档里的初始值）

### C1. `Lighting()`（Builder）
- 环境光（Trilight）：天空 `#C3DCF2`，地平线 `#DCE8C9`，地面 `#83A062`，强度 `1.05`。
- 主光：颜色 `#FFF0DA`，强度 `1.25`，角度保持 `(48,-35,0)`，`shadowStrength` 从 `.65` 改为 **`.55`**，软阴影。
- 雾：颜色 `#C9E0E6`，线性 32–80 m（远景树线要能淡进天空）。
- 天空（FarmSky）：先不动。

### C2. URP 资产（只改 DesktopURP 和 FarmDesktopRenderer）
- 阴影距离 `40`，四级级联，软阴影质量设为中。
- SSAO：强度 `.45`，半径 `.25`，Direct Lighting Strength `.15`，降采样关，After Opaque 关。
- 手机档（MobileURP）先不开 SSAO 和 Bloom。

### C3. 全局 Volume（新建 `FarmGlobalVolume-r03` 资产，由 Builder 放进场景）
- Tonemapping：**Neutral**（ACES 会把高饱和的玩具色压暗压灰；如果想对比，ACES 截一张图作参照即可，不采用）。
- Color Adjustments：Post Exposure `+0.10`，对比度 `+6`，饱和度 `+8`。
- Shadows/Midtones/Highlights：暗部 `(0.97, 1.0, 1.05)`（暗部略带蓝绿，让阴影不发黑）。
- Bloom：阈值 `1.0`，强度 `.2`，Scatter `.6`。
- Vignette：`.16`，Smoothness `.4`。
- 不加景深和运动模糊。
- 主相机打开 Render Post Processing；自动化截图工具（FarmAcceptanceRunner 342 行）里的关闭逻辑先不动，但要额外截一组开启后期的图。

### C4. 验收证据（`Evidence/r07/D2/`）
- 12 个固定机位改前改后对比；房屋背面、树荫下、田地三张近景重点看阴影颜色。
- 15 分钟性能对比。

## D. Opus 验收时看什么
- 不能再有直角色块，路沿柔和但 1 m 近看不糊。
- 阴影带颜色、不发黑，整体颜色更接近总图，但不刺眼。
- 噜噜和动物没有被后期冲淡或过曝（重点看黄色的噜噜和白色的鸭子）。
- 帧时间均值增加不超过 1 ms；有超过的情况也照实报告。
