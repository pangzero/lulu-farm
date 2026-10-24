# 噜噜农场 Unity＋URP 整体整合方案

版本：v1.0 · 2026-10-18  
工程依据：`/Users/haowen/GameProject/farm-game/lulu-studio`  
目标产品：可下载安装的手机／电脑 3D 农场游戏  
文档状态：r06电脑版完整农场候选已实际构建、运行、录制和持续测试，长帧与美术保留项未解决，尚未全项验收；见最新检查点。

### 当前电脑版检查点 · 2026-10-23 r06

完整Unity农场候选已生成并实际运行：73主资源＋68LOD，单主屋、20块田、中央牧场、闭合池塘／码头／摊位按总图连接；Lulu模型冻结。实际31/31输入路线、原生鼠标／UI／阶段／换装／画质、三次场景重入已检查。12固定＋25路线图已逐张查看，187.549秒真实录像已编码并核对6个解码关键帧。M5 1280×720电脑档、全成熟20格持续测试有效917.684秒，7圈；均值8.393ms、P95 8.367ms，但8个窗口含>100ms长帧，其中3个>1秒，最长1859.271ms，原因未确定，不能宣布性能全部通过。透明树／屋顶叠层、源模型细缝和Lulu既有问题保留，用户美术待验收。

电脑交付候选：`/Users/haowen/GameProject/farm-game/lulu-farm-unity/Delivery/r06-20261023/`；源工程及逐项结论：`lulu-farm-unity/Docs/FINAL-ACCEPTANCE-20261023.md`，机器记录`Evidence/final-acceptance-r06-20261023.json`。Android按用户决定先不接真机、模块地区404未解决；Windows/iOS未构建实测。**当前是电脑版完整场景候选可审阅，M0–M6全项验收尚未完成**，剩余重点为长帧定位、透明遮挡外观和用户验收，不要回退成只有代码或许可证未激活。下方2026-10-18／19内容保留为历史快照。


本方案把现有资产接入 Unity，按原总览图组装完整农场，并建立可持续制作的角色、渲染、资源和验收流程。现有网页继续作为素材检查工具；正式游戏使用 Unity＋URP。用户已有的模型和卡通派生继续使用，原件与已认可历史版本均保留。


> 2026-10-19 用户调整：Lulu 模型美术修复先搁置，先让当前模型在农场内运动，后续由用户提供新模型替换。当前 locomotion-r08 仅作为可替换运动候选；接缝、腿顶等问题继续记录为未通过，不再复跑失败补片/封口方法。此调整不暂停其他 M0–M6 工作。

### 执行检查点 · 2026-10-19

- 15 种动物 `game-r04` 已完成独立源、两级 LOD 和实际固定图初审，原件保留；14 个共享族群幼苗已完成资源候选与种植检查，均待 Unity 整场确认。
- 成熟作物 11 件已有资源候选与 LOD；南瓜、草莓的关键局部不能用失败减面版替换。玫瑰独立语义修复 r04 已消除规则圆补丁，仍保留继承串绿等问题记录，完整归档继续进行。
- 编辑器已安装；M1 独立代表场景、M2 控制／镜头、M4 完整场景及检查入口已编写。19 个项目 C# 文件离线编译无错误；这不是 Unity Editor 实际导入、场景生成或运行验收。
- 当前唯一已执行的编辑器启动在许可证处停止。macOS 安装包、实际漫游／录像／性能以及 Android 模块和真机测试未完成。用户正在处理网络与许可证。
- 下方资源表保留方案制定时的输入基线；最新派生选择以 `public/models/unity-integration/manifest.json`、`public/models/unity-animals/manifest.json` 和进度文件为准，不能将旧高模数字当作最新资源总量。

## 1. 已确定的目标与当前结论

### 1.1 采用的总图

![农场总览与画风依据](/Users/haowen/GameProject/farm-game/art-concepts/05-assembled-farm-preview.png)

总图原件：[05-assembled-farm-preview.png](/Users/haowen/GameProject/farm-game/art-concepts/05-assembled-farm-preview.png)。原目录：[ASSET-CATALOG.md](/Users/haowen/GameProject/farm-game/art-concepts/ASSET-CATALOG.md)。历史批次与质量要求：[农场美术资产 Blender 分批执行计划](</Users/haowen/Documents/Obsidian Vault/04 project/Farm/农场美术资产 Blender 分批执行计划.md>)。

采用总图的区域关系、造型语言和色彩：左侧规则田地、后方中央主屋与农产摊位、前方中央牧场、右侧池塘与码头／渔产摊位，土路连接，边缘布置圆树、灌木和白花。总图用于布局与美术指导；玩家始终在可旋转的第三人称透视镜头中游玩。

用户已明确的决定：

- 3D 马卡龙动画画风，圆润饱满、柔和哑光、体块清楚，保留自然的前后体积。
- 使用最新组装的 Lulu `wardrobe-rig/full-r02` 作为角色接入起点；静态正式版 v1 只读保留。
- 中等距离跟随 Lulu，人物位于画面中央附近，支持水平旋转、有限俯仰和缩放。
- 不增加俯视／正交玩法镜头或种植视角切换；资产验收台的俯视图仍作为检查工具。
- 牧场棚屋 S02 暂缓，用围栏、入口门、饲料槽组织牧场。总图中的棚屋位置保留草地和动物活动空间。
- 作物仅幼苗、成熟两阶段；西葫芦 C12、葱 C16 的两个阶段继续暂缓，不做占位。

### 1.2 现在到底还差什么

**当前使用范围的主要静态模型已经具备。下一步的工作重点是游戏化整理、统一渲染、角色运动和场景组装。**无需再次生成整套作物、围栏、土格、岸石、设施或环境参考图。

| 部分 | 已具备 | 整合前仍需处理 |
|---|---|---|
| 14 种成熟作物 | Meshy 原件、卡通派生、相对减面版本 | 玫瑰串色；部分亮叶脉／贴图痕；成片种植所需 LOD 和贴图预算；Unity 内复查 |
| 14 种幼苗 | 4 个 Meshy 原型映射的 14 个微改卡通候选 | 宽叶 4 种仍高面；共享原型的资源复用；与成熟态同场校色和比例复核 |
| 15 种动物 | 原件与材质修订版，牛采用头部清理 v4 | 减面、尺度、必要眼部修订；静态展示可先组装，活动需要独立绑定和动画 |
| 21 件新设施／环境 | 原件与实际单件网页初看 | 尺寸适配、材质统一、定向减面、必要分件、接口拼接、侧背面检查 |
| 围栏／土格／直岸／水面／岸石 | B02 r04、B03 r03 的既有模型 | Unity 材质和碰撞适配；重复土格的定向优化；水面运行时渲染 |
| Lulu | 最新组装绑定版、原裤与同版型换装 | 运动范围与接缝复核、正式待机／行走／跑步、角色资源优化、Unity 驱动验证 |
| 农场整体 | 总图、单件预览、网页跟随镜头试验 | Unity 工程、完整布局、统一光照、水体、角色控制、实机性能与安装包 |

新设施大多已经是卡通造型，不能把“尚未在 Unity 统一材质”误记成“尚未建模”。已做过的卡通化也不因换引擎而全部重做。

## 2. 本次核对的依据与状态边界

本次读取工程 `AGENTS.md`、原计划第 0–4 节及第 10 节、当前清单和验收记录；实际查看原总图、B01 r03 认可图、成熟作物与幼苗当前版本的既有 3/4 证据、成熟玫瑰多视图对照、动物材质对照与牛 v4、Lulu 组装版，以及 21 件设施／环境的既有网页图板。此次复查使用真实历史渲染／网页截图，没有新画概念图充当模型。

对当前建议接入的 GLB 重新读取文件、SHA256 和 glTF 结构。动物与设施当前文件哈希均与清单相符；作物三角面与清单一致。本次核对不代替重新打开 Blender、Unity 导入、完整五视图验收或设备测试。

| 当前集合 | 数量 | 三角面合计 | GLB 文件体积合计，十进制 MB |
|---|---:|---:|---:|
| 成熟作物当前资源候选，含尚未通过视觉的玫瑰 | 14 | 3,017,108 | 217.34 |
| 幼苗当前映射卡通候选 | 14 | 1,322,608 | 65.81 |
| 动物当前修订版 | 15 | 3,432,710 | 304.35 |
| 新设施／环境 Meshy 原件 | 21 | 8,317,892 | 517.96 |
| Lulu 最新组装 GLB | 1 | 680,822 | 47.90 |

这些是资源文件的单份几何统计，不是整场每帧可见几何、显存或安装包大小。重复种植会增加渲染工作量；共享网格能节省重复资源，但不会消除每个可见实例的几何开销。Lulu 的蒙皮模型也需要单独优化。

21 件新设施源于 35 个下载文件名，14 个是重复或重命名副本，按哈希归并。当前范围 21 件已齐；S02 是用户暂缓，不是漏交。它们的 63 张内嵌图片多为 4K／2K，已有 RGBA8 解码估算约 3.17 GB（不含 mipmap 等），此数不是实测显存，也不是经过平台压缩的 Unity 运行时内存。

证据入口：

- [本次只读核对与全部建议文件哈希](/Users/haowen/GameProject/farm-game/lulu-studio/review/farm-integration-20261018/unity-plan-audit.json)
- [14 种成熟当前证据索引图](/Users/haowen/GameProject/farm-game/lulu-studio/review/farm-integration-20261018/unity-plan-mature-evidence-contact.jpg)、[14 种幼苗当前证据索引图](/Users/haowen/GameProject/farm-game/lulu-studio/review/farm-integration-20261018/unity-plan-seedling-evidence-contact.jpg)；仅整理已有检查图，非新增建模成果。
- [成熟作物清单](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/crops-meshy/manifest.json)、[两阶段版本登记](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/crop-two-stage/manifest.json)。
- [成熟派生验收](/Users/haowen/GameProject/farm-game/lulu-studio/review/crop-mature-remaining-20261018/acceptance.json)、[幼苗映射验收](/Users/haowen/GameProject/farm-game/lulu-studio/review/seedling-meshy-mapping-20261018/acceptance.json)。
- [动物当前版本](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/manifest.json)、[新设施原件清单](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/manifest.json)。

历史文档中仍存在“幼苗未制作”“设施全部 Blender 直接做”等旧快照。本方案以当前文件及用户后续授权为准，保留原批号用于归档。

## 3. 作物：已有卡通版怎样继续用

### 3.1 成熟态逐种选择与工作

下表是 Unity 接入起点，不代表用户已采用。B01 的旧 Blender r03 继续作为只读美术基准；表中是用户新 Meshy 的独立派生。`game` 只是历史资源候选命名，不能由名字推定已适合手机。

| 编号／作物 | 已有卡通源 GLB | 资源候选 GLB | 资源候选面数 | 继续处理与采用边界 |
| --- | --- | --- | --- | --- |
| C01 卷心菜 | [toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/toon-r02/cabbage-mature.glb) | [game-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/game-r02/cabbage-mature.glb) | 163,712 | 保留包心与外叶间隙；亮叶脉在 Unity 同场判断后局部柔化。 |
| C02 番茄 | [toon-r03](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/toon-r03/tomato-mature.glb) | [game-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/game-r02/tomato-mature.glb) | 206,646 | 保留果实较叶片略亮的材质区别、果梗连接；避免整体磨平。 |
| C03 玉米 | [toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/toon-r02/corn-mature.glb) | [game-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B01/game-r02/corn-mature.glb) | 111,880 | 保留棒粒层次和叶鞘；先做中景 LOD，不抹平穗粒与叶间空隙。 |
| C04 黄瓜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r01/cucumber-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r01/cucumber-mature.glb) | 126,162 | 保留黄花、心叶、垂瓜与卷须；细卷须独立检查减面损伤。 |
| C05 南瓜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r01/pumpkin-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r01/pumpkin-mature.glb) | 108,924 | 保留分瓣、粗瓜梗和卷须；校准橙皮高光与落地接触。 |
| C06 向日葵 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r01/sunflower-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r01/sunflower-mature.glb) | 172,700 | 保留大小花盘、厚花瓣与背托；籽粒细节转入烘焙时先验证轮廓。 |
| C07 小麦 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r01/wheat-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r01/wheat-mature.glb) | 293,722 | 粒列和三簇高低保留；中景简化穗粒，不压成一块金色板。 |
| C08 小白菜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/toon-r01/bokchoy-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/game-r01/bokchoy-mature.glb) | 157,324 | 白叶柄仍有细灰线，株型侧深偏浅；先定向材质修订，不称已重做株型。 |
| C09 粉玫瑰 | [toon-r03](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r03/rose-mature.glb) | [game-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r02/rose-mature.glb) | 366,048 | 视觉未通过：花瓣／叶片串色；停止旧阈值路线，另评语义区域修复。 |
| C10 草莓 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B06/toon-r01/strawberry-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B06/game-r01/strawberry-mature.glb) | 429,884 | 保留心形红果、浅籽、白花与三出叶；中心较密，优先整理 LOD。 |
| C11 花椰菜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/toon-r01/cauliflower-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/game-r01/cauliflower-mature.glb) | 279,322 | 保留奶白圆簇和包叶厚度；低角度遮挡与簇面平滑做近镜头复查。 |
| C13 西瓜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/toon-r01/watermelon-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B05/game-r01/watermelon-mature.glb) | 136,628 | 保留贴面条纹、裂叶和果梗；原件粗叶脉／瓜蔓局部观察后处理。 |
| C14 橙色郁金香 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B06/toon-r01/tulip-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B06/game-r01/tulip-mature.glb) | 124,284 | 保留杯口、厚瓣和长叶；统一花色，杯内平色中心属当前保留项。 |
| C15 生菜 | [toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/toon-r01/lettuce-mature.glb) | [game-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B04/game-r01/lettuce-mature.glb) | 339,872 | 保留卷缘与层叠；少量亮叶脉和中心融合局部修订，不用统一减面损坏卷叶。 |

当前 14 件的文件技术记录通过；13 件有带保留项的视觉初审，成熟玫瑰视觉未通过；这些新派生的最终用户美术与目标设备测试均待完成。前三种的历史幼苗失败不再阻塞其成熟版。

成熟玫瑰已经触发同一颜色阈值路线两轮未解决的停止规则。保留 toon-r03／game-r02 和失败证据，不能再次批量跑同一方法或标记合格。后续若恢复修复，应先评审“按花瓣／叶片语义选区与 UV 岛重绘或重烘焙”的独立路线；当前正式授权允许独立语义／UV 修复，旧颜色阈值失败路线仍禁止复跑。整场布局可以继续，玫瑰资产验收保持未通过，其他通过候选不能被它拖回未制作。

### 3.2 幼苗逐种映射与版本

| 编号／作物 | 共享族群 | 当前 GLB | 三角面 | 接入处理 |
| --- | --- | --- | --- | --- |
| C01 卷心菜 | 宽圆叶族 | [meshy-toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r02/cabbage-seedling.glb) | 243,152 | 保留 r02 背脉；重点另做游戏 LOD |
| C02 番茄 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/tomato-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C03 玉米 | 窄带叶族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/corn-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C04 黄瓜 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/cucumber-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C05 南瓜 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/pumpkin-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C06 向日葵 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/sunflower-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C07 小麦 | 窄带叶族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r01/wheat-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C08 小白菜 | 宽圆叶族 | [meshy-toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B08/meshy-toon-r02/bokchoy-seedling.glb) | 243,152 | 保留 r02 背脉；重点另做游戏 LOD |
| C09 粉玫瑰 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r01/rose-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C10 草莓 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r01/strawberry-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C11 花椰菜 | 宽圆叶族 | [meshy-toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r02/cauliflower-seedling.glb) | 243,152 | 保留 r02 背脉；重点另做游戏 LOD |
| C13 西瓜 | 早期双子叶代表族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r01/watermelon-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C14 橙色郁金香 | 基生披针叶族 | [meshy-toon-r01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r01/tulip-seedling.glb) | 35,000 | 沿用当前微改；同场校色、轻量 LOD |
| C15 生菜 | 宽圆叶族 | [meshy-toon-r02](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B09/meshy-toon-r02/lettuce-seedling.glb) | 243,152 | 保留 r02 背脉；重点另做游戏 LOD |

14 个都是已保存源与 GLB 的真实派生，来自 4 个共享原型。共享早期代表苗允许形态相近，不能写成 14 个独立植物学重建；不要加成熟果实、花球、麦穗或盛开花朵来增强幼苗辨识。

宽叶 4 种采用保留 243,152 面原几何的 r02：上一轮压到约 35,000 面导致背面叶脉退化，已弃用。其他 10 种当前约 35,000 面。后续宽叶优化需通过局部重拓扑／重烘焙的小样关卡，恢复正确背脉后才扩展；不得重新调用失败减面包覆盖 r02。

资源共享建议先共用同族贴图、材质及导入缓存。只有确认几何、UV 与局部造型相同，才可合并为共享网格加实例变换；已有微改不能直接丢弃。远距离可另做同族简化 LOD，保留当前版作近景对照。

### 3.3 两阶段整合方式

每种建立 `CropDefinition` 数据：编号、幼苗资源、成熟资源、根部原点、两阶段适配、土格定位、版本和验收状态。田格保存 `Empty / Seedling / Mature`；空格是地块状态，不是新增“成长态”。

以既有两阶段共同世界尺度为起点，植物和土格分离，一格 1.2×1.2 单位。只在总场比例明显失衡时修订适配记录并复查阶段配对，不能把每株归一到同高。换阶段时替换植物实例，土格保持原位；本阶段可以用检查按钮切换，实际生长计时、播种／收获规则另作玩法实现。

## 4. 动物、Lulu：哪些已经改过，哪些还没完成

### 4.1 动物

15 种已经有卡通外形与独立材质修订，主要处理眼部反光和材质；牛的默认指针进一步采用 `cow-head-clean-v4`。不再从动物 Meshy 原件重新开始整批卡通化。

| 编号／动物 | 当前 GLB | 三角面 | 后续工作 |
| --- | --- | --- | --- |
| A01 鸡 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/chicken.glb) | 235,116 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A02 粉猪 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/pig.glb) | 178,694 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A03 绵羊 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/sheep.glb) | 328,030 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A04 羊驼 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/alpaca.glb) | 358,918 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A05 仓鼠 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/hamster.glb) | 189,714 | 现有卷曲／凹陷瞳面仍明显，列近景定向修订；保留原表情 |
| A06 牛 | [v4](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animal-studies/cow-head-clean-v4.glb) | 163,414 | 采用头部清理 v4，保留粉内耳与白脸纹，细根部痕仍待近看 |
| A07 小鸭 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/duck.glb) | 197,276 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A09 驴 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/donkey.glb) | 212,182 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A10 普通水豚 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/capybara.glb) | 134,006 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A11 鸵鸟 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/ostrich.glb) | 366,294 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A12 小马 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/pony.glb) | 356,644 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A13 白鹅 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/goose.glb) | 173,960 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A14 山羊 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/goat.glb) | 224,368 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A15 小鹿 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/deer.glb) | 165,986 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |
| A16 黑猪 | [v1](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/animals-refined/v1/black-pig.glb) | 148,108 | 沿用 v1 材质修订；同场复核眼面与反光，另做游戏 LOD |

动物当前仍为静态模型，无正式骨骼与活动动画。整合第一版按总图摆放牛、羊、鸡、猪、鸭等代表动物，其他已入库动物保留在资产目录，可替换展示或少量分组布置，避免把 15 种同时挤满中央牧场。动物 AI、行走、进食与繁殖不由静态模型自动获得。

兔子 A08 当前只有参考而无入库 GLB，作为将来可选补充，不阻塞现有范围的农场。普通水豚 A10 与主角 Lulu 是不同资产，不可互相替换。

### 4.2 Lulu 接入与动画

接入起点：[最新组装 full-r02 GLB](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/wardrobe-rig/full-r02/lulu-rig.glb)，[可编辑源](/Users/haowen/GameProject/farm-game/lulu-studio/assets-source/wardrobe-rig/full-r02/lulu-rig.blend)，[当前验收限制](/Users/haowen/GameProject/farm-game/lulu-studio/review/lulu-wardrobe-rig-20261018/full-r02/acceptance.json)。原静态正式版：[lulu-official-v1.glb](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/lulu-official-v1.glb)，用户认可保持有效，不覆盖。

full-r02 有 8 个部件、23 根骨骼和 5 个诊断动作。当前 GLB 实读为 680,822 三角面、18 个图元、3 个材质、5 张内嵌图像。它是组装和有限小幅运动候选，不能称为已通过完整走跑。

接入按以下顺序：

1. 保留头部、五官、身体静态体积和原裤；建立统一角色根节点，试验显示高度 1.2 单位。角色碰撞胶囊与视觉网格分离。
2. 对右肩及另一肩、内臂、胯部、膝与裤腰做实际行走所需角度检查，先修能影响运动的接缝／穿插，另存独立版本。历史 r11 及眼下失败试验不作为基底。
3. 完成正式 Idle、Walk、Run，做速度与步频匹配、转向过渡、足底接触。先用原地动作配合控制器驱动，避免初期同时叠加根运动造成滑移。
4. 在 Unity 验证骨架、蒙皮、绑定姿势和 AnimationClip；先走 Generic／现有骨架路线。Lulu 的比例与骨骼不自动等同于 Humanoid，不把导入 GLB 当成 Mixamo 验证成功。
5. 若现有 GLB 动画接入不满足 Animator 流程，只为角色另出 FBX 派生桥接，逐帧比较静态和动作；静态设施与作物继续用 GLB，不全库转换。
6. 做保留脸、剪影和关节的角色重拓扑／烘焙候选，动画验收后再次看变形。不能用统一减面比例直接压到目标面数。

镜头与碰撞研发可临时推动静态 Lulu 验证路线，但必须标记“临时无步行动画”，不能据此完成正式角色验收。

换装沿用同腰线、同裤脚的短裤模板，只切材质和图案。FabricUV 为第二套纹理坐标（glTF `TEXCOORD_1`）；Unity 换装材质需明确采样这套 UV。标准材质的 UV0 采样不能直接替代它，角色也不生成覆盖此 UV 的静态光照 UV。身体隐藏区域必须由原版型短裤覆盖；高腰差异／高开衩等新剪裁是另一个几何任务。

## 5. 建筑、设施、环境：逐件怎么处理

### 5.1 21 件新 Meshy 输入

以下全部已入库并实际单件查看过，当前仍是原件。先保留圆润造型，再针对与总图的差距修材质和必要结构，另存 `unity-art`／`unity-game` 派生。

| 现有原件 GLB | 三角面 | MB | 具体整合／卡通化处理 |
| --- | --- | --- | --- |
| [S01 中央主屋](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s01-central-house.glb) | 1,331,312 | 56.80 | 保留橙瓦奶油墙与侧棚；主屋背面较空，四周检查门窗／檐下与附带绿化；优先优化瓦片与细装饰，建立简化碰撞。 |
| [S03 农产摊位](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s03-produce-stall.glb) | 1,697,652 | 65.55 | 保留橙白篷与货物色块；货物合并网格，首版静态，定向减面／烘焙；需要换货时另拆语义部件。 |
| [S04 渔产摊位](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s04-fish-stall.glb) | 729,250 | 37.77 | 保留黄白篷、蓝鱼与容器；合并鱼货先静态，统一木材与反光，清理密集小件开销。 |
| [S06 牧场入口门](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s06-pasture-gate.glb) | 187,176 | 18.31 | 定向拆门柱／门扇，首版静态开门；门柱、门高、木色与 B02 围栏衔接，保留独立门轴。 |
| [S07 码头模块](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s07-dock.glb) | 300,146 | 21.26 | 定码头面与岸高、立柱入水及接岸端；简化绳结木纹与碰撞，先验证重复段接口。 |
| [S08 划艇](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s08-rowboat.glb) | 316,246 | 22.01 | 保留船壳内外、舷缘与座板厚度；整理底部和简化材质，首版静态停靠，不含驾驶。 |
| [S09 饲料槽](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s09-feed-trough.glb) | 389,046 | 23.81 | 对齐动物口鼻高度，保留槽腔；饲料粒减少噪声与几何，整槽先静态。 |
| [S10 路灯](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s10-lantern-post.glb) | 213,660 | 21.54 | 暖木与灯罩同场校准；灯芯仅少量自发光，附带植被不能穿地；实时灯独立预算。 |
| [S11 独立木箱](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s11-wooden-crates.glb) | 648,592 | 33.67 | 箱与货物为合并输入；先作静态摆件，优化密集货物；空箱／换货需求再拆。 |
| [S12 浇水壶](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/s12-watering-can.glb) | 249,620 | 18.58 | 校准与 Lulu 手掌的比例、壶嘴／把手连接和开口；必要握持节点放在外层，不先增加浇水玩法。 |
| [E03 草地格](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e03-grass-tile.glb) | 184,628 | 19.59 | 当前为木边草地格；保留作局部模块或参考，主场草地用同风格连续轻量底面，不满场重复木边。 |
| [E04 路面格](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e04-path-tile-provisional.glb) | 84,346 | 16.93 | 现有黄土铺面＋木边已确认；作局部样块，连续路网从同色系派生，处理转弯与无错层连接。 |
| [E06 河岸弯角](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e06-shore-corner.glb) | 166,072 | 19.24 | 弯岸含石和水块、单合并网格；另存派生分离／去除附带水体，配 E05 检查闭合岸线，未具备完整内外角套件。 |
| [E08 圆树](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e08-round-tree.glb) | 87,664 | 11.18 | 沿用圆润冠团与树干；统一绿与木色，按前后体积制作 LOD，布置时留镜头通道。 |
| [E09 梨树](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e09-pear-tree.glb) | 201,120 | 17.67 | 保留梨形果、果梗与树冠；不是新增田格作物，不要求幼苗／成熟两套，近景保果实支撑关系。 |
| [E10 灌木](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e10-shrub.glb) | 149,332 | 15.26 | 保留矮宽叶团；同树形成高度层次，优化内部遮蔽面并留前后轮廓。 |
| [E11 白花丛](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e11-white-flowers.glb) | 439,736 | 24.55 | 保留白厚瓣、黄花心和叶片体积；降低密集几何，远景不变成白噪点。 |
| [E12 芦苇](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e12-reeds.glb) | 167,264 | 17.78 | 保留穗头、长叶与茎；减少尖碎边，根部接岸，按疏密变化而非全岸等距复制。 |
| [E14 睡莲](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e14-water-lily.glb) | 92,006 | 13.87 | 保留厚叶缺口、花瓣层次；水位适配与微小离面高差，避免闪烁，先静态。 |
| [E15 草垛](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e15-hay-bale.glb) | 556,044 | 26.86 | 保留捆带和大草束；减少草丝噪声、统一暖金色，放牧场边而不阻路。 |
| [E16 蓝鱼](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/facilities-meshy/meshy-r01/e16-blue-fish.glb) | 126,980 | 15.73 | 保留蓝身、白腹、厚鳍和眼神；近水面可见性检查，先静态，再考虑低成本游动。 |

新模型多为一个合并网格、一个材质，带有较复杂的颜色贴图。门扇、货物、屋旁绿化、岸角附带水面不能因为视觉上分得开，就当作已具备独立节点。需要运动／替换或拼接的部分才定向分件，其余可保持静态完整模型。

### 5.2 直接复用的旧资产

| 已有 GLB | 三角面 | 使用方式 |
| --- | --- | --- |
| [S05](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B02/s05-fence-repeat-r04.glb) | 3,048 | 围栏 r04，用户美术认可；只读复用，Unity 材质与接口适配 |
| [S05-endcap](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B02/s05-fence-endcap-r04.glb) | 2,104 | 围栏终柱 r04，按段归属规则使用 |
| [E01](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B03/e01-r03.glb) | 45,994 | 土格 r03；保留风格与格距，重复使用前做游戏派生 |
| [E05](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B03/e05-r03.glb) | 39,250 | 直岸 r03；保留截面、水位与岸坡，复核接岸角 |
| [E07](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B03/e07-r03.glb) | 288 | 水面 r03；原件为静态不透明零厚度平面，运行时水材质另做 |
| [E13](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B03/e13-r03.glb) | 23,040 | 石头组 r03；只读复用外观，处理实例尺度和着地 |
| [S01-native-alternative](/Users/haowen/GameProject/farm-game/lulu-studio/public/models/farm-assets/B14/r02/s01-main-house.glb) | 106,314 | 原生完整主屋 B14 r02；可编辑替代候选，非与新主屋同时摆放 |

- 围栏 S05 按 1.2 步长摆放，每段归属“左柱＋两横档”，末端补一个终柱。转角只保留一根共享角柱，不能重复堆柱；与新门的接口另核对。
- 土格 E01 保留用户认可的连铺宽木边风格，农场大面积草地／道路使用连续底面，避免把草地格和路面格的木框重复铺满整个世界。
- E05／E07／E13 保留 r03 原件。岸角 E06 的附带水体必须在独立派生中与主水面协调，最终只保留一套可见水面，避免重叠闪烁。
- E02 幼苗田格是 E01＋已有幼苗实例，不新增专用作物模型。
- S01 优先用用户新 Meshy 版校准，B14 原生完整主屋 r02 保留作可编辑替代方案；最终一栋中央主屋只选择一个版本。B02 的立面样段只是风格基准，不加入场景冒充完整主屋。

### 5.3 继续卡通化的明确优先级

| 优先级 | 对象 | 本轮后续应做的动作 |
|---|---|---|
| P0，独立质量问题 | 成熟玫瑰 | 保持视觉未通过；另评语义区域修复方案，停止旧颜色阈值路线 |
| P0，场景成立条件 | 主屋侧背、门与围栏、岸角与水面 | 检查可旋转镜头下的完整性，修必要分件与拼接；主屋原件背墙空白要设计判断 |
| P0，运行开销 | Lulu、重复作物与宽叶幼苗、摊位／主屋高模 | 先用代表镜头定位瓶颈，再定向派生；未优化高模不成片铺设 |
| P1，风格统一 | 已卡通作物／幼苗 | 保留现有成果，调亮叶脉、局部杂色、反光和与环境的色差，逐种留对照 |
| P1，材质整理 | 新设施、树灌木、花草、草垛 | 抑制写实纹理／烘焙杂色／过亮高光，统一木、墙、叶、石等材质族 |
| P1，动物融入 | 当前 15 种修订版 | 优先校正比例和反光；仅对实际近镜头暴露的眼部／脸部缺陷定向修订 |
| P2，场景丰富 | 微风、灯芯、鱼／船轻动 | 主体画面与性能过关后再加；不先增加大量动画、透明与后处理 |

## 6. 按总图整合成可以走进去的农场

### 6.1 布局与尺度

总图是从一个方向观察的构图，不含可直接照抄的工程尺寸。先还原区域关系，再为第三人称步行补足道路净宽、背面和转弯空间。不得只做总图朝向的一面布景。

建议第一轮场地范围约 34×24 单位，用作走测初值，非已测定最终大小。世界 Y 向上，地面 Y=0；约定世界 +Z 为总图后方、+X 为总图右侧。以主屋前的中心路口为定位参照，按下表安排首轮锚点，再以游戏镜头调整间距：

| 区域 | 首轮锚点 X/Z，仅建议值 | 按总图落实的内容 |
|---|---|---|
| 主屋区 | 0 / 6 | 中央主屋面向前方，入口台阶连路，旁边摆农产摊位与少量木箱 |
| 农产摊位 | 4 / 5.5 | 保留与主屋相邻关系；主屋自带侧棚已存在，控制独立摊位密度 |
| 田地区 | -9 / 2 | 首轮按图的 4 列×5 行组织，1.2 格距；幼苗和成熟交错，周边留行走道 |
| 牧场区 | 1 / -3.5 | 围栏、可通行入口、饲料槽与代表动物；S02 不补 |
| 池塘区 | 11 / 1.5 | 闭合岸线、独立水面，码头接岸，船在码头边，睡莲芦苇靠岸 |
| 渔产摊位 | 10 / -4 | 位于池塘前侧道路边，保持看得到水和码头的关系 |
| 景观边缘 | 各区边界 | 圆树、梨树、低灌木、白花与岸石，保留路径和镜头空隙 |

田地首轮 20 格足够体现原图，资源目录仍保留全部 14 种。用数据配置更换种类和两阶段，不必为展示所有阶段同时塞入 28 格。地图尺寸、坐标和株高调整必须写回场景配置，不能靠逐株临时拖动而失去可复现性。

Lulu 暂定高 1.2。主路净宽先按 1.8–2.4、门口净宽至少角色胶囊宽加两侧余量试走；这些是设计初值，待真实碰撞验证。新 Meshy 原件多数最长边被统一到约 1.9，不能把主屋、树、鱼、浇水壶按同缩放导入后直接摆放。每件记录尺寸适配，以门高、工具握持、槽高、围栏高和码头面为依据。

### 6.2 地面、田格与行走

草地与道路采用连续、可编辑的轻量地面网格，保留总图的平坦草地和圆润转弯。池塘范围挖出实际空间，不能在水下留一张与陆地齐平的可碰撞草地。田格视觉独立，植物根部贴合土面；Lulu 的行走依赖简化地面碰撞，不逐个碰撞小土块与木纹。

土格之间保留原图的田埂和宽木边；角色主要走田边道路，田内是否允许踩踏在后续玩法决定，场景测试应明确可走区域。不会因为增加一层全场碰撞平面而允许角色从池塘上直接走过。

### 6.3 牧场接口

沿用已认可围栏。新 S06 为合并模型，首版整合时定向拆出门柱和门扇，另存派生，门扇保持打开的静态姿态，让入口可见且可通行。自动开门、关门与交互提示属于后续玩法；门柱与围栏使用固定接口和简化碰撞。

动物脚底着地，饲料槽按动物口鼻高度与身体宽度摆放。先放牛、羊、鸡、猪、鸭等图中代表，给动物留空间，不把尺寸各异的原件统一缩成同高。

### 6.4 池塘、码头与鱼

保持 B03 的地面 Y=0、水面 Y=-0.105 关系。E05 直岸配 E06 岸角，先验证闭合岸线、内外轮廓、底部和每个接口，再放岸石、芦苇。必要连接片从已有截面派生，保留风格，不重新设计整套岸线。

码头行走面与岸边道路顺接，立柱实际入水；船不浮在空气中或陷入码头。睡莲叶与水面有小幅高差，避免共面闪烁。岸角附带水块单独清理或遮除后再接主水面。

首版采用低开销、偏不透明的水，参考图蓝鱼可做上部露水面的装饰实例，水下部分被水面遮挡。真正水下可见鱼需要另加透明／深度方案，不能把鱼全部放在当前不透明水下然后宣称已可见。鱼骨骼游动、船驾驶、游泳均不是静态组装的默认交付。

### 6.5 旋转镜头带来的完整性检查

每栋建筑与大树都要从四周看，重点查屋后、瓦下、窗侧、棚顶下、树冠背面、船内外和码头底部。道路与植被不只服务一个观赏机位；在主屋背面、牧场入口、田间转角、码头边和树下旋转镜头，仍要有完整画面。

## 7. Unity 工程与资源接入架构

### 7.1 工程与版本

建议独立工程目录：`/Users/haowen/GameProject/farm-game/lulu-farm-unity`，保持现有 `lulu-studio` 为源资产与验收工程。此路径已建立工程文件；截至2026-10-19，许可证检查尚未通过，首次Unity编译和场景执行未完成。

采用 **Unity 6.3 LTS＋同编辑器验证的 URP 包**作为当前建议基线，具体补丁号在开工时核对后锁定；同时锁定 Cinemachine 3、Input System、glTFast 的兼容版本并保存 package lock，不分别追逐每个包的最新版。官方当前列出的 6.3 LTS 支持期至 2027 年 12 月。[Unity 版本与支持](https://unity.com/releases/unity-6/support)

本次检查默认 `/Applications` 与用户 Applications 的 Unity Hub／Editor 常见位置均未找到；未据此断言全机没有自定义安装。正式开工第一项是核对编辑器、对应构建模块和目标设备。本次方案任务未安装软件，也未产出 Unity 构建。

### 7.2 资源流向

```text
受保护的 Meshy 原件／已认可模型／可编辑 Blender 源
    ↓ 记录来源名、SHA256、修改范围
独立美术派生 → 独立游戏派生／LOD／平台贴图
    ↓ 选择明确版本，编辑器导入
Unity 导入资源 → 统一材质 → 可复用 Prefab
    ↓ 使用独立适配与摆放数据
区域场景＋角色＋灯光水体 → 桌面／手机安装包与实测
```

GLB 优先通过 glTFast 编辑器导入，生成 Unity 资源后建立外层 Prefab；无需在游戏启动时逐件解析网页 URL。glTFast 官方支持导入场景、网格、材质、纹理和 AnimationClip，实际兼容性要在本项目模型上验证。[glTFast 编辑器导入](https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.14/manual/ImportEditor.html)

不得将整个网页 `public`／`dist` 或全部历史版本复制进游戏的 Resources／StreamingAssets。原始高模保留在资产工程中，游戏只引用选定派生及其依赖。材质、贴图和资源依赖显式保存，构建不依赖 localhost:5173。

### 7.3 资源、适配与实例分开

每个资源登记 `assetId / stage / sourceVersion / sourceSHA256 / derivativeVersion / sourceKind`，以及三角面、材质、纹理、包围盒、技术／视觉／用户／优化／设备状态。`sourceKind` 区分原生 Blender、Meshy 导入源和导入后编辑派生。

每个 Prefab 分三层：

```text
InstanceRoot：游戏位置、交互或数据 ID
├─ VisualAdapter：单位、朝向、根部定位与必要缩放
│  └─ Visual：选定资源与 LOD、材质绑定
└─ Collision：简化碰撞，独立于高模外观
```

Unity 坐标采用 Y 向上，外层统一视觉朝前约定为 +Z。glTF 导入器负责格式坐标转换，不能再凭经验整体翻面或叠加负缩放。用带方向标记的小样核对正面、旋转、法线、骨骼和尺寸后再应用全库。

资源更新只替换 Visual 对应版本，场景位置、碰撞和资产身份保持稳定。重复实例共用网格与材质，不能每株生成一份相同贴图。现有历史 `r02`、`r03` 不是全局唯一键，必须同时带资产 ID、阶段与批次。

### 7.4 场景和代码组织建议

建议目录 `Assets/Farm/`，下面分 `Art`、`Materials`、`Prefabs`、`Scenes`、`Scripts`、`Data`、`Settings`、`Editor`；该目录结构已建立；场景和 Prefab 必须由实际 Unity 导入／组装生成，文件夹存在不等于已完成。

| 模块 | 职责 |
|---|---|
| Bootstrap 场景 | 加载配置、输入、选定质量档与农场场景 |
| FarmWorld 场景 | 按总图组织 House／Fields／Pasture／Pond／Landscape；规模扩大后再拆附加场景 |
| AssetCalibration 场景 | 固定相机、灯光、曝光、背景，单件／灰模／新旧版本与 LOD 对照 |
| PlayerController | 地面移动、碰撞、朝向与速度；不把相机旋转写进模型源 |
| CameraRig | 独立旋转目标、跟随、距离、遮挡和输入锁定 |
| CropDefinition／FarmLayout | 两阶段资源、土格和实例位置；禁止把整场烘成一个 GLB |
| MaterialLibrary／QualityProfiles | 材质族、移动与桌面渲染档，禁止实例偷偷改曝光 |
| ImportValidator／AssetRegistry | 来源、尺寸、贴图和缺失引用检查，输出机器可读报告 |

首个小农场可用普通场景引用与共享 Prefab；分区或资源确实增加时引入 Addressables，并管理加载引用与释放，不提前搭建复杂联网更新系统。

## 8. Unity＋URP 怎样得到马卡龙动画画风

URP 支持跨手机到电脑的渲染工作流，但统一风格仍需要资产与灯光校准。[URP 官方介绍](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/urp-introduction.html)

### 8.1 先做一组同场校准

选 Lulu、主屋、围栏、圆树、卷心菜／番茄／玉米及一株幼苗，放进同一个校准场景。先确定体块、色彩、明暗与接触感，再扩展全部素材。原图的圆润屋瓦、奶油墙、暖木、明亮草地、水蓝池塘和柔和阴影是评价依据。

保留原 B01 的固定检查设置与证据。Unity 新建并保存自己的固定检查配置：线性色彩空间、相机、背景、太阳方向、天空环境、曝光、色调映射和阴影。跨引擎不能只复制同名曝光数字便宣称条件完全相同；Unity 内的新旧派生必须同条件比较。

### 8.2 材质分族处理

| 材质族 | 目标 | 对当前资产的动作 |
|---|---|---|
| Lulu 皮肤／动物毛皮 | 柔和体积、颜色干净、适度宽高光 | 保留五官和花纹；清掉扰乱体块的细噪声，不把眼睛一起磨成哑光 |
| 眼睛 | 清晰深色瞳孔和克制高光 | 眼部单独参数／遮罩，保留神态；近景凹坑属于几何问题，换灯不能算修好 |
| 叶片／幼苗 | 厚实、有前后层次、柔和明暗 | 抑制粗亮叶脉与密集噪点，保留物种差异与卷叶结构，不全库换同一绿色 |
| 果实／花瓣 | 番茄红、南瓜橙、花球奶白等主体清楚 | 果皮可比叶片略亮；保留花瓣层次、花球圆簇和果梗连接 |
| 木材／草垛 | 暖色、大形体与少量方向感 | 压低细木纹、草丝和黑脏缝，保留板条／捆扎关系 |
| 墙面／瓦片／岸石 | 奶油墙、橙瓦、柔和石灰蓝 | 保留倒角与凹凸，减少写实斑驳和过强环境烘焙阴影 |
| 金属小件／灯芯 | 少量材质区别 | 金属不做全场亮点；灯芯用克制自发光，实时点光单独预算 |

默认从 URP Lit 与少量共享 Shader Graph 开始，先做柔和连续明暗。强硬分档阴影、粗描边和全场强 Bloom 不作为默认风格。

glTF 金属粗糙度与 Unity Lit 的 smoothness／通道打包不同。沿用 glTFast 材质时核对实际结果；改成自有 URP 材质时，显式转换 `smoothness = 1 - roughness` 的语义及贴图通道，不能把粗糙度图直接塞进光滑度。基础色按 sRGB，法线／遮罩等数据图按其正确类型导入，核对切线、法线方向、透明模式和纹理坐标。[URP Lit 材质参数](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/lit-shader.html)

为平台压缩与管理，必要时把派生材质的内嵌图像导成独立纹理并保存映射。先确认贴图用途，减少烘在颜色图里的强光照与噪声；仅调 smoothness 无法消除颜色图中的假阴影。

### 8.3 灯光与后处理

首版固定晴天：一个暖中性太阳主光，柔和天空环境，静态地面／建筑适度烘焙，角色与动物使用探针光照。反射探针服务有限区域，叶片、土、木头的高光受控。优先实现脚底、屋基、围栏和植株根部的接触感。

桌面可以增加适度 SSAO、阴影质量与远处细节；手机先用主光阴影和低成本环境光，SSAO、附加光阴影与高成本水反射依据实测决定。色调映射与曝光固定后再改材质，不能逐件调曝光制造改善。

天空采用浅蓝渐变、少量软云与低细节远景树，远景颜色稍淡，保留总图的开阔感。景深和运动模糊不作为默认玩法效果，防止遮住田格和造成转镜头不适。

### 8.4 水和微动

复用 E07 的几何基础，独立 Unity 水材质负责蓝色层次、低幅波纹与边缘关系。手机基线不用屏幕空间反射或实时平面反射；需要场景深度／透明时再单独测成本。波浪幅度不改变码头接岸和睡莲水位。

树叶、幼苗可后续增加极轻的顶点风摆，根部固定，花果不散开；同族共享参数、实例可有相位差。船轻摆、鱼游动和动物活动在静态完整性与性能稳定后逐件接入。

## 9. 第三人称移动与旋转镜头

采用 Input System 的 Move、Look、Zoom、Interact、Pause 动作，将设备输入与角色逻辑分离。[Input System Actions](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.14/manual/Actions.html)

| 操作 | 电脑建议 | 手机横屏建议，待体验确认 |
|---|---|---|
| 移动 | WASD／方向键，预留手柄 | 左侧虚拟摇杆 |
| 旋转视角 | 按住鼠标拖动，灵敏度可调 | 右侧空白区域拖动 |
| 缩放 | 滚轮 | 双指缩放或距离按钮 |
| 交互 | E／手柄按键 | 明确的交互按钮；未实现玩法时不显示假按钮 |
| 回正／暂停 | 单独按键 | 小按钮，避开转镜头触控区 |

Cinemachine Third Person Follow 跟踪独立的旋转目标，使镜头能绕角色转，而角色自身朝向由移动决定；该组件支持平滑跟随与碰撞处理。[官方跟随说明](https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineThirdPersonFollow.html)

首轮参数延续已选镜头试验：透视 FOV 约 52°，距离约 5.1 单位，俯角约 35°，人物接近屏幕水平中线、略低于垂直中心；距离范围先试 2.5–8.6，俯仰先限约 15–55°。这些是体验初值，不是最终验收数值。

角色采用相机相对移动，速度归一化以免斜走更快；胶囊碰撞、地面探测和有限台阶能力与动画分开。镜头目标跟随人物平移，旋转不强制拽着 Lulu 原地转圈；平滑更新避免抖动，UI 操作期间不同时移动角色或转镜头。

镜头障碍用近似体积检测，覆盖相机近裁剪面。墙、屋顶和大树阻挡时先拉近相机；仍看不见角色时对指定遮挡物做局部淡化。淡化材质另做受控派生，不能直接把所有导入网格透明化。要实测穿过树下、紧贴围栏、绕主屋、走进牧场和站在码头边的情况。

## 10. 游戏优化与手机／电脑档位

### 10.1 当前减面版还需要继续优化的原因

成熟候选单件仍约 11.2 万至 43.0 万面；9 株草莓仅植物本体就约 387 万面。宽叶幼苗单件约 24.3 万面，9 株约 219 万面。Lulu 当前约 68.1 万面；主屋约 133.1 万、农产摊位约 169.8 万面。把它们同时放入跟随镜头，会有明显资源风险，网页单件能打开不等于手机整场可用。

优化顺序：先确认画风与大形体，再制作代表性低模／LOD、烘焙与贴图，最后用同条件画面对照和实机数据决定采用版本。压缩文件可减少包体与加载量，不能替代几何、蒙皮、透明和阴影成本治理。

### 10.2 首轮资产预算建议

以下是为首个场景制定的**候选制作目标范围**，没有任何一件因此已经通过；保形优先，达不到时先定位结构与镜头需求，不能强压面数。

| 类别 | 近景游戏候选三角面初值 | 中／远景策略 |
|---|---:|---|
| Lulu | 30,000–60,000 | 重点保脸、剪影和关节；需要时另做中景蒙皮 LOD |
| 成熟作物 | 多数 3,000–8,000；复杂花球／卷叶可先试到 12,000 | 中景 1,000–3,000，远景按物种／叶形族群简化，验收后采用 |
| 幼苗 | 800–3,000 | 根冠和叶形保留，中远景低模；宽叶先过小样再扩展 |
| 动物 | 10,000–25,000 | 保五官、轮廓与肢体；动画后复查关节与 LOD |
| 主屋 | 30,000–60,000 | 瓦、门窗、四面轮廓保留，远处取消小五金和细瓦缝 |
| 摊位／码头／船 | 8,000–30,000，按体量分别定 | 密集货物烘焙／简化；保持箱体和船内空间 |
| 树／灌木／花草 | 1,000–8,000 | 依屏幕占比做体块 LOD，阴影距离单列 |
| 重复土格／小道具 | 土格先试 500–2,000；工具 1,000–5,000 | 土块／纹理细节转入贴图；已有围栏先共享复用再看是否需要优化 |

角色与宽叶幼苗的降幅较大，是后续有实际制作量的任务。若两轮仍出现同核心轮廓／叶脉／变形损坏，保存失败对照并停止该路线，转向局部重拓扑或不同 LOD 设计；不能通过放远相机或换光掩盖。

### 10.3 纹理、批次与加载

手机初始多数纹理按 512／1K，主角或近景主屋关键图可 2K；桌面根据实际屏幕占比保留更高档。对基础色、法线、遮罩分别确认必要性，使用 mipmap 与目标平台支持的压缩格式，记录画面与内存变化。原始 4K 内嵌图不默认全部保留在发布版本。

同类作物、围栏、树和装饰尽量共用网格与材质。根据本项目渲染器及平台实测，选择 SRP Batcher、GPU 实例化或其他适合的方法；它们的收益不能简单相加，SRP Batcher 也不等于合成一次绘制。不要逐实例复制材质，使用 Frame Debugger 核对真正的绘制和批次。[Unity 绘制优化方法](https://docs.unity3d.com/6000.0/Documentation/Manual/optimizing-draw-calls-choose-method.html)

近景主角和建筑保留阴影，远景小草／花丛优先限制投影；按区域、视锥和距离控制可见性。高密度重复物不使用整株 MeshCollider。场景切换、质量切换和资产替换要释放不用的实例与加载引用；反复进入农场检查内存是否持续增长。

### 10.4 初始画质档与测试目标

目标机型尚未指定，下表用于首轮试验，需由真实设备结果修订，不能直接对外承诺帧率。

| 项目 | 手机基线 | 电脑基线 |
|---|---|---|
| 验证目标 | 约 1280×720 内部渲染、稳定 30fps；较强设备另测 60fps | 1920×1080、60fps 目标 |
| 帧时间 | 30fps 对应 33.3ms，记录 CPU／GPU 与 P95 | 60fps 对应 16.7ms，同样记录瓶颈和低帧 |
| 渲染 | Forward 起步，限制附加光与透明，Render Scale 可调 | 同一美术基线，提高分辨率、LOD 与阴影档位 |
| 阴影 | 先试 1K–2K 主光阴影、约 18–25 单位范围、少量级联 | 先试 2K 主光阴影、约 30–40 单位范围 |
| 后处理 | 克制调色；SSAO／高成本水效果先关闭或低档 | 在性能范围内提高接触感和水质 |
| 观察预算 | 首轮争取单镜头约 50 万面以内、约 150 批次以内作排查线 | 以实测帧时间为准，不以更高面数为质量目标 |
| 内存观察线 | 首轮纹理驻留争取约 256MB 以内；总内存记录，不替代设备限制 | 同样记录驻留和峰值，避免重复纹理与资源泄漏 |

主光阴影范围、分辨率、附加光、深度／不透明纹理、抗锯齿和渲染通道都要按设备检查，而非机械全开。[URP 性能设置](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/configure-for-better-performance.html)

用开发安装包连接 Profiler 测试，记录设备型号、系统、图形 API、分辨率、质量档、场景资源版本与 CPU／GPU／内存。编辑器帧率仅作诊断；未测试设备明确写未测试。[Unity 应用性能分析](https://docs.unity3d.com/6000.0/Documentation/Manual/profiler-profiling-applications.html)

## 11. 实施阶段、依赖与原批号归档

执行时以内部质量关卡连续推进已授权范围，不把每个里程碑变成重新索要启动许可。用户已明确授权连续完成 M0–M6，无需再次询问各阶段启动。

| 阶段 | 具体工作 | 交付与进入下一阶段的条件 |
|---|---|---|
| M0 工程与清单 | 核对 Unity／构建模块，建立 URP 工程与资产登记；锁版本 | 编辑器可开，样本 GLB 导入正确，来源与状态可追溯，无粉材质／引用丢失 |
| M1 代表实景校准 | Lulu、主屋、围栏、少量田格／作物／树／岸段；首批游戏派生 | 固定 Unity 图像对照，体块、材质、比例与总图协调；取得资源成本基线 |
| M2 角色与镜头 | 控制器、旋转跟随、遮挡、碰撞；正式走跑与换装验证 | 本机安装包可操作，关键路线与角色动作关卡通过；诊断动作不冒充走跑 |
| M3 全库适配 | 剩余作物／幼苗、动物和 21 件新资源的局部卡通修订、分件与 LOD | 各资产有明确版本与逐项状态，失败路线隔离；玫瑰仍失败时单列不合格项 |
| M4 完整农场组装 | 按总图完成田地、主屋、牧场、池塘、道路和景观 | 所有区域实际可走可看；一栋主屋，S02 暂缓；四周旋转、池塘闭合和地面接触通过 |
| M5 整场渲染与性能 | 水、阴影、必要微动、共享资源、档位、真机调优 | 优化前后同条件保形；手机／电脑分别记录真实结果，未测平台不补通过 |
| M6 验收与安装包 | 整理完整源工程、派生、证据、操作与已知问题 | 可安装运行、资源版本一致，技术／视觉／用户／优化／设备状态分开提交 |

M1 的小场景是校准关卡，最终交付仍是按总图组织的完整农场。M2、M3 中没有资产依赖的工作可交错安排，不能因一件玫瑰未通过而停止地形、镜头等独立任务，也不能把有问题资产悄悄算入验收通过。

归档继续使用 B01／B04／B05／B06 成熟派生、B08／B09 幼苗映射、B02 围栏、B03 地面水岸、B14 主屋和 B15–B21 各设施环境来源；整体场景整合与性能归 B22。Unity 的 M0–M6 是实施里程碑，不是新一套资产编号，也不追认 B15–B22 已完成。

## 12. 验收方法与完成定义

### 12.1 单件资产

每个发生模型／贴图修改的派生保存可编辑源、GLB 或必要角色 FBX、来源名／SHA256、修改范围、metrics、review-settings 和 acceptance。源重新打开、导出重新导入；检查几何、法线、厚度、材质、贴图、尺寸、原点、UV 和必要蒙皮。原件与已认可资产哈希不变。

正、侧、背、3/4、俯视分别留材质和中性灰模图，单图至少 768×768；关键连接补特写。新旧／LOD 共用相机、灯光、曝光、背景和显示比例，不靠换光、放大或景深制造改善。

作物每种每阶段保留 3×3、Lulu 比例与原固定农场距离检查：1280×720、DPR=1、约 12×8 格、1.2 格距；另外新增 Unity 实际第三人称距离检查。原正交检查台只作资产测量，不进入玩法镜头。

### 12.2 场景与操作

固定走测路线：主屋前 → 左侧田地外圈 → 田间转角 → 牧场入口与饲料槽 → 池塘岸边 → 码头 → 渔产摊位 → 绕主屋背面 → 返回起点。

沿路线检查：

1. 根部、脚底、屋基、围栏与码头实际接触；比例合理，土与植物分离。
2. 门口、转角和码头可通行，角色不穿墙／穿栏／踏水；台阶与边缘不抖动。
3. 近、中、远距离与水平旋转 360°、有限俯仰、缩放均能看清 Lulu；屋后、树下和窄处无明显镜头穿模。
4. 所有引用资源正确，切换作物阶段、换装和质量档不会丢材质、翻面、重复渲染或改错版本。
5. 新旧／LOD 对照保留轮廓、叶间隙、花瓣层次与主要花果连接；田格远景保持清楚。
6. 池塘闭合、不露底、不重叠水面，岸角和码头无缝隙／高差穿帮。
7. 触摸 UI 不同时触发移动／镜头；鼠标键盘与手机控制分别实际验证。

### 12.3 设备与证据

本机电脑先建立可安装运行的基线，早期即安排一台实际手机测场景；Windows、Android、iOS、macOS 分别只对真正测试的平台出结论，最终发行优先级和设备型号待确定。iOS／Android 的构建工具链及签名在 M0 按实际目标验证，不由一个桌面包推定成功。

对相同路线记录冷启动、热运行、快速转镜头、最大种植密度、反复进入场景和连续运行约 15 分钟的情况，观察掉帧、温升、内存峰值与恢复。截图用于画面，Profiler／设备日志用于性能，两者分别保存。

每件资产与整场均使用五栏状态：

| 技术检查 | 视觉初审 | 用户美术 | 资源优化 | 目标设备 |
|---|---|---|---|---|
| 未验证／通过／失败 | 未看／通过有保留／失败 | 待验收／明确采用的版本 | 未做／候选／同条件复核通过 | 未测／具体设备、配置与结果 |

网页已看、Unity 已导入、技术通过、用户认可不能互相替代。此次没有新增 Unity 画面、安装包或设备通过记录；此前浏览器复查受策略限制的项目继续保留未验证，本次不重写为已通过。

## 13. 最终交付清单

完整整合执行结束时，应交付以下可复现内容：

- Unity 源工程及锁定版本，能在指定编辑器打开，包含可运行 FarmWorld、AssetCalibration、角色与镜头。
- 采用的 Prefab、材质库、质量档、布局与作物两阶段数据、输入配置及必要控制代码。
- 每件实际采用资源的来源、哈希、独立派生源、LOD／贴图和状态清单；原始 GLB 与认可源保留。
- 完整农场多角度截图、第三人称漫游录像、关键接触／接口／遮挡证据、资产前后对照。
- 实测平台的安装包、操作说明、构建记录和资源版本；未测试平台及签名／设备缺项明确列出。
- 逐设备性能报告与已知问题清单，包含失败路线、当前限制及待用户美术验收项目。

以下是后续玩法阶段：播种收获、成熟计时、交易背包、动物活动 AI／饲养、建筑室内、开船、游泳等。当前整体整合先把世界、角色、画风与运行基础做完整，并预留数据接口；不会把静态模型已经具备写成这些玩法已经实现。

## 14. 下一次实际开工的入口

从 **M0＋M1** 开始：先建立 Unity＋URP 工程，导入明确版本的 Lulu、主屋、围栏、少量土格与作物、圆树和岸段，在同一场景确认画风、尺度、导入兼容性与资源成本。随后接 M2 的正式运动和镜头、M3 全库整理，最后按总图完成全部区域。

开工前无需再准备一轮整套模型或概念图。需要解决的是本方案已列出的具体问题：成熟玫瑰颜色、宽叶幼苗优化、Lulu 运动与资源、设施的侧背／分件／拼接，以及 Unity 内统一材质和目标设备验证。保持用户暂缓项，不恢复失败旧生成器，不覆盖任何原件。
