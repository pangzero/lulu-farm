# Lulu Studio

Farm Game 工作区下的 Lulu 与农场动物模型预览工程。2026-10-16 从 Obsidian 中的旧游戏工程迁入；2026-10-17 共入库 15 份动物 Meshy GLB（已有牛、羊、鸭，本次新增 12 份）。模型文件按 SHA-256 核对。当前路径：`/Users/haowen/GameProject/farm-game/lulu-studio`。

## Lulu 静态分件候选（2026-10-18）

[打开正式版对比与独立分件](http://127.0.0.1:5173/modular.html?rev=parts-v2&view=front&mode=assembled)。已保存八个独立 GLB 和可编辑组装 `.blend`，正式版 v1 与备份未变，未制作骨骼或动作。

**连接质量尚未通过：** 组装三面保留原轮廓，但拆开后的肩侧及手臂内面仍有折面；不能作为合格绑定基础。文件、真实截图、剩余拓扑问题及换装接口说明见 [分件检查记录](review/lulu-modular-20261018/README.md)。

## 运行

```sh
npm install
npm run dev
```

- 默认预览：http://127.0.0.1:5173/ ，默认 Lulu 正式版 v1（用户确认的脸颊修补 r4）。
- 模型资产预览：http://127.0.0.1:5173/gallery.html ，包含 Lulu 与 15 份动物模型；支持单独查看、每组四只分页同屏、旋转、缩放、平移、正侧背视角、灰模、线框和自动旋转。按需载入并释放其他模型，避免同时解码全部 4K 贴图。
- 作物工坊：http://127.0.0.1:5173/crops.html ，16 种新建 Blender 作物，支持三阶段对照、单株、3×3 平整田块、16 种总览和放大画布。
- 保留旧入口：http://127.0.0.1:5173/meshy.html?model=notail 。
- 历史程序模型：http://127.0.0.1:5173/lulu.html 。
- 生产构建：`npm run build`。

## 目录

| 目录 | 内容 |
|---|---|
| `public/models` | 15 份可预览的 Lulu GLB，含原始 Meshy 与无尾版 |
| `public/models/animals` | 15 份动物 GLB 原件副本与来源／哈希／三角面清单 |
| `public/models/animals-refined/v1` | 15 份独立材质修订版，当前动物预览默认使用 |
| `public/models/crops` | 16 种作物 × 3 生长阶段，共 48 个 GLB 与几何统计清单 |
| `assets-source/crops` | 每种作物一份可编辑 Blender 文件，三阶段独立集合 |
| `assets-source` | Blender 源、原始 Meshy 文件、历史材质贴图及备份 |
| `public/reference` | 网页使用的三面参考、轮廓数据 |
| `reference-source/lulu` | 原始 Lulu 参考与裁剪图 |
| `src` | 模型预览代码与样式 |
| `tools` | Lulu 制作、导入、导出及检查脚本；不会随网页启动执行 |
| `review` | Lulu 截图、对比页、版本备份和验证数据；旧文字报告已清理 |
| `migration` | 迁移文件清单、哈希验证与清理记录 |

## 文档位置

唯一资产说明位于 `/Users/haowen/Documents/Obsidian Vault/04 project/Farm/Lulu 资产说明.md`。

旧游戏方案、执行计划和建模过程报告已清理。模型、源文件、贴图、参考图及预览代码继续保留。

## 版本约定

- `official`：Lulu 正式版 v1，用户于 2026-10-18 确认 cheekfix-r4。新 GLB 与获批文件字节一致。
- `notail`：上一正式外观基线，no-tail-2，保留供历史对照。
- `original`：用户提供的原始 Meshy 模型。
- `retopo`：眼缘重铺试改，用户偏好上一版，因此仅作为候选保留。
- 其他按钮与 `lulu.html` 用于历史对照，不表示已通过用户验收。

历史脚本可能需要 Blender Python，或含 NumPy/Pillow 的 Python 环境。普通预览只需要 Node.js 和 npm。

## 农场动物（2026-10-17）

| 模型 | 项目文件 | 三角面 | 内嵌图片 | 骨架／动画 |
|---|---|---:|---:|---|
| 牛 | `public/models/animals/cow.glb` | 163,414 | 3 | 无 |
| 羊 | `public/models/animals/sheep.glb` | 328,030 | 3 | 无 |
| 鸭 | `public/models/animals/duck.glb` | 197,276 | 3 | 无 |
| 鸡 | `public/models/animals/chicken.glb` | 235,116 | 3 | 无 |
| 粉猪 | `public/models/animals/pig.glb` | 178,694 | 3 | 无 |
| 羊驼 | `public/models/animals/alpaca.glb` | 358,918 | 3 | 无 |
| 仓鼠 | `public/models/animals/hamster.glb` | 189,714 | 3 | 无 |
| 驴 | `public/models/animals/donkey.glb` | 212,182 | 3 | 无 |
| 普通水豚 | `public/models/animals/capybara.glb` | 134,006 | 3 | 无 |
| 鸵鸟 | `public/models/animals/ostrich.glb` | 366,294 | 3 | 无 |
| 小马 | `public/models/animals/pony.glb` | 356,644 | 3 | 无 |
| 山羊 | `public/models/animals/goat.glb` | 224,368 | 3 | 无 |
| 白鹅 | `public/models/animals/goose.glb` | 173,960 | 3 | 无 |
| 黑猪 | `public/models/animals/black-pig.glb` | 148,108 | 3 | 无 |
| 小鹿 | `public/models/animals/deer.glb` | 165,986 | 3 | 无 |

15 份 GLB 与下载原件字节一致，原文件名和 SHA-256 记录在 `public/models/animals/manifest.json` 与 `assets-manifest.json`，可供后续游戏引用或导入 Blender 编辑。本次只入库及接入预览，没有改动网格、UV 或材质。查看器在父级对象上统一显示高度，不代表实际体型比例。

- 新下载名 `Meshy_AI_Duck_1017004003…` 实际为白鹅，保存为 `goose.glb`；原黄色小鸭继续保留为 `duck.glb`。
- 两份 Pig 分别是 `pig.glb`（粉猪）和 `black-pig.glb`（黑猪），为独立生成的网格。
- 牛、羊、小鸭已用哈希核对在项目里；当前下载中没有兔子模型。
- `python3 tools/import_animal_models.py` 可重新核对这批文件、同步资产清单和预览目录；遇到同名但内容不同的资产会停止，不覆盖已有版本。

### 动物材质整批修订（2026-10-18）

用户确认牛眼部样例方向后，已制作全部 15 个动物的独立修订 GLB。动物预览默认使用修订版，点击“原版／材质修订”可在同一机位切换，下载链接跟随当前版本。Lulu 的当前正式版本见下方独立登记。

- [交互模型预览](http://127.0.0.1:5173/gallery.html?model=cow&view=quarter&eyes=refined&detail=head)
- [15 个动物的同机位截图对比](http://127.0.0.1:5173/review/animal-materials-20261018/index.html)
- 资产目录：`public/models/animals-refined/v1/`；版本、源哈希、材质参数及检查记录：`public/models/animals-refined/manifest.json`。

眼部：将既有虹膜／瞳孔面分配独立材质，按动物调整粗糙度、法线和反射，减弱碎亮纹。原有眼位、神态、顶点、法线、UV 和贴图主高光保留。牛另对头部及外耳原有黑色区域进行局部 UV 材质烘焙，清理色纹和凹凸噪声；保留白色脸纹、粉色内耳与角，避免按三角面涂色造成边界锯齿。

制作脚本：`tools/refine_animal_material_batch.py`、`tools/bake_cow_clean_material.mjs`。原件、预览代码备份位于 `review/animal-materials-20261018/baseline/`，90 张正／侧／斜角前后截图位于其 `screenshots/` 目录。已完成浏览器三角度检查，最终美术验收待用户确认。仓鼠等模型原有眼珠凹凸、局部眼缘接缝仍在；本轮未改网格，也未制作骨骼、LOD 或性能优化。之前的牛眼部研究文件保留在 `public/models/animal-studies/`。

**牛头清理更正：** 用户指出 v1 的耳部乱纹基本未变，复核属实；先前“已清理”的结论过强。当前牛的修订指向独立 `public/models/animal-studies/cow-head-clean-v4.glb`：用实黑材质覆盖黑毛内部面，保留边界面原贴图。侧面断续亮弧与耳面长划痕已有正常尺寸可见的减少；角根、耳根及额侧仍有少量细痕，不代表全部清干净。原件、v1 和已否决候选均保留，未改顶点、UV 或眼位。[牛头 v1／v4 同机位对比](http://127.0.0.1:5173/review/cow-head-cleanup-v2/index.html)。制作脚本 `tools/assign_cow_black_interior_v4.mjs`；最终美术验收待用户确认。

## 新作物库（2026-10-17，第一版）

卷心菜、番茄、玉米、黄瓜、南瓜、向日葵、小麦、小白菜、玫瑰、草莓、花椰菜、西葫芦、西瓜、郁金香、生菜、小葱。每种包含幼苗（sprout）、成长（growing）、成熟（mature）。这是按新参考图制作的造型样本，待用户确认画风；未制作风动、收获动画、LOD 或最终游戏性能优化。

`tools/build_crops.py` 是原生 Blender Python 建模脚本。叶片、叶脉、果实、花瓣保留为独立可编辑部件；GLB 导出时按部件角色合并。使用纯色 PBR 材质，无外部贴图依赖。`.blend` 为 Z 向上，GLB 为 Y 向上，根部在原点，种植间距 1.2 单位；三个阶段保留真实大小，不单独归一化。`.blend` 中三阶段沿 X 排列，便于编辑对照，导出的单株 GLB 均回到原点。

```sh
/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender --background --python tools/build_crops.py -- --render
```

末尾可加 `cabbage tomato corn` 等 ID，只重建选定作物。`--render` 同时输出 Blender 阶段对照图到 `review/crops/`。初轮版本备份为 `review/crops/crop-v1-initial.zip`；改已验收模型前另存版本。

### 卷心菜质量试改

`crops.html?crop=cabbage&mode=versions` 同屏对照原版 v1 与试改 v2，共用相机、灯光和世界尺度。卷心菜的成熟态、田块和总览默认加载 v2；版本栏可切回 v1。v2 仅为成熟态质量打样，待定稿；幼苗和成长态仍是 v1。源文件位于 `assets-source/crop-studies/cabbage-v2.blend`，独立 GLB 与网页清单位于 `public/models/crop-studies/`，制作脚本为 `tools/build_cabbage_study.py`。


## Lulu 正式版与骨骼副本（2026-10-18）

- 正式外观：`public/models/lulu-official-v1.glb`，来源 cheekfix-r4；`assets-source/lulu-official-v1.blend`。用户已确认；主预览和动物画廊的 Lulu 默认使用它。
- 独立绑定：`assets-source/rig/lulu-rig-r04.blend`、`public/models/rig/lulu-rig-r04.glb`。Blender 原生骨架与权重，23 根骨骼，每顶点最多 4 个权重。骨盆、脊柱、头颈、肩臂、手掌及腿脚均有骨骼；无手指骨。
- [基础绑定对照预览](http://127.0.0.1:5173/rig.html)：正式静态模型与真实蒙皮模型同机位并排，支持正侧背、骨骼、灰模和小幅姿态检查。
- 头脸刚性跟随头骨。静止网格、UV、材质和内嵌图片保留正式版本，导出追加骨架与蒙皮信息。
- 这是基础绑定副本，尚未接入 Mixamo 或制作走跑动作。肩腋及腕旁的原始相连网格仍会在外展/摆臂时牵拉；动画制作前需要专门解决，不宣称成熟游戏变形质量。
- 制作与复核：`tools/build_lulu_rig.py`、`tools/check_lulu_rig.py`；来源备份、回读检查和实机截图在 `review/lulu-rig-20261018/`。

## Lulu 腋下分离实验：已否决（2026-10-18）

用户已否决 r11：静止状态的胸侧和身体出现明显刀切感，破坏了原有圆润形体。此前将其描述为“轻微折痕和补面明暗差”不准确。`rig.html` 目前仍展示这份历史实验，不能视为已验收版本。正式静态 v1、r04 及独立备份保留。后续以正式静态 v1 为源，先设计换装分件、完成静止组装模型与独立部件，再处理骨骼动作；当前尚未交付模块化模型。详情见 [修改记录](review/lulu-rig-separation-20261018/README.md)。
