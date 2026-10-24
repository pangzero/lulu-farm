# Lulu game-r01 交接（O1 进行中，2026-10-24 02:45）

在云端完成的中间结果。**不是交付版**，也不是美术认可版。

## 输入
- 模型：`review/lulu-hybrid-color-20261023/shorts-r01/lulu-colored.glb`（静态，约 65 万三角面）
- 骨骼和动作：`public/models/unity-lulu/locomotion-r08/lulu-locomotion-master.glb`（23 骨，Idle/Walk/Run）

## 关键发现
- 新模型的身体、手臂、腿、短裤和 full-r02/locomotion 是同一套"rig-local"坐标；新模型里外层组装节点的变换是 缩放 0.57、平移 (0.0009, 0.53, 0.025)。
- 所以直接沿用旧骨骼节点、IBM 和三段动画（原样复制）。头、橘子、颈部、眼睛用组装矩阵的逆变换换算到 rig-local 坐标。
- 新 Arm_R 和旧 Arm_R 形状不同，权重改从 Arm_L 左右镜像过来（骨骼名 Left 和 Right 互换）。
- r08 的腿整条绑在 Foot 骨上，所以腿顶会露出短裤；现在腿在短裤裤口以上跟随周围短裤的骨骼，裤口以下过渡回 Foot。
- 颈部：Spine2 → Neck → Head 按高度平滑过渡（y 从 -0.123 到 -0.04）。头、橘子、眼睛 100% 绑 Head 骨。
- 材质不用顶点色（Unity 不保证支持）：
  - 头部非脸区域和颈部：柱面 UV + `body-wrap-basecolor.png`（与 portable 同算法）；
  - 脸：平面投影 UV + face-basecolor；
  - 眼睛：原 UV 重采样；
  - 其余部件：单色材质；
  - 橘子拆成果肉和叶子两个材质；
  - 短裤保留 UV1（FabricUV，按单个源三角形逐角点采样，避免 UV 接缝处拉花），用于换装。

## 工具（tools/）
- `qem.cpp` + `Simplify.h`：Fast-Quadric-Mesh-Simplification（sp4cerat，MIT 协议）。改了三处：边界和锁定点不塌缩；共线阈值放宽到 0.99999；法线翻转阈值改为 0。编译：`g++ -O2 -o qem qem.cpp`（qem.cpp 开头需要 `#include <cstdint>`）。
- `decim.py`：先精确焊接，再对非边界点做 2e-4 聚类焊接（去掉 Meshy 的极细三角形），然后 QEM。边界锁定，保证部件之间不开缝。
- `build_game.py lod0|lod1 out.glb`：完整构建（减面、属性重采样、权重、材质、动画）。需要 numpy、scipy、PIL，以及同目录下的 `new.glb`（shorts-r01）和 `master.glb`（locomotion-r08 master）。
- 各部件目标面数见 `TARGETS`。LOD0 合计约 2.92 万三角面，各部件偏差最大约 4 mm（rig-local 单位，换算到世界尺寸约 2.5 mm）。

## 结果（lulu-game-lod0-wip.glb）
- 静态外观和源模型几乎一致：`screenshots/static-source-vs-lod0.png`。
- 三段动作都能播放：`screenshots/anim-walk-run-idle.png`。
- 跑步时向前迈的腿会把短裤前片顶开，露出腿。r08 同样有这个问题，新版略好（`screenshots/run-shorts-r08-vs-new.png`）。已经试过加大短裤裤管跟随大腿骨的比例，效果不明显。下一步考虑把 Run 的大腿摆幅缩小到约 75%，同时把参考速度按同样比例调低，或者给短裤做局部修形。
- 腰侧手臂附近的深色细缝是原模型就有的，未处理。

## 待办
1. 跑步时短裤被顶开的问题（见上）。
2. 生成 LOD1（`build_game.py lod1`，约 1.4 万三角面），检查眼睛贴片是否高出头部表面（贴片低于头面就要外推）。
3. 写 README 和 metrics，补五视图、换装三套（UV1）的截图。
4. 给 DeepSeek 写 Unity 替换步骤：
   - 转成 gltf 文件夹；
   - 在 registry 里给 Lulu 写入新版本；
   - 短裤材质的三套预设和 FabricUV Shader；
   - worldHeight 和控制器参考速度（Walk 和 Run 的源速度沿用 manifest，按新的缩放重新换算）；
   - 胶囊碰撞、相机高度、遮挡淡出参数。
5. Unity 里实测，并与 r06 同机位对比。
