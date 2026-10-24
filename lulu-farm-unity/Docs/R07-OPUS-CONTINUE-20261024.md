# Opus r07 接续入口：保留已有工作

2026-10-24。工作区 `/Users/haowen/GameProject/farm-game`；私有仓库 `pangzero/lulu-farm`。其他机器以克隆根目录替代本机路径，先安装 Git LFS 并执行 `git lfs pull`。

首次 Git 交付遗漏了正在制作的新 Lulu 工作目录。本轮补入原始目录中的 60 个文件（460,789,639 字节）：当前静态源、修复数据、低模带动画 WIP、全部现有工具、对照图、上游 polish-r01、参考图、旧骨骼母版和换装纹理。原文件保持 SHA256 不变，没有重新建模。

逐文件来源、字节数和 SHA256：`R07-LULU-WIP-REMOTE-MANIFEST.json`。归档 GLB 均内嵌缓冲和图像，无外部 URI。

## O1 已有成果

1. 先读 `lulu-studio/review/lulu-game-r01/HANDOFF.md`。
2. 当前中间版：`lulu-studio/review/lulu-game-r01/lulu-game-lod0-wip.glb`。跑步仍会顶开短裤，腰侧原有细缝保留，不能标记最终版。
3. 当前静态源：`lulu-studio/review/lulu-hybrid-color-20261023/shorts-r01/lulu-colored.glb`。同目录保留便携版、灰模、补片 NPZ、参数、校验和对照图。
4. 修复前基线：`lulu-studio/review/lulu-hybrid-color-20261023/polish-r01/`。保留已有形体和眼睛，不重走失败路线。
5. 骨骼与三段动作：`lulu-studio/public/models/unity-lulu/locomotion-r08/lulu-locomotion-master.glb`。原件只读。该目录旧 LOD1 不等于新 Lulu 已有 LOD1。
6. 换装纹理：`lulu-studio/public/models/wardrobe-rig/materials-v2/`。

待办仍包括跑步穿插、新 LOD1、图集目标、三套换装、Unity 接入和实际验收。另存 `lulu-game-r02` 等新版本，不覆盖 r01。未制作 Blender 源的成果仍明确为 GLB 与脚本源，不虚构 Blend。

## 可移植工具入口

历史工具原样保存。render_lulu.py 含旧 Mac 绝对路径，旧 QEM 二进制也可能不兼容新环境。新增准备入口只在独立目录复制工具和输入、适配渲染路径、重新编译原 C++ 源，归档文件保持不变。

在仓库根目录运行，工作目录必须为空：

```sh
python3 -m venv /tmp/lulu-opus-env
/tmp/lulu-opus-env/bin/python -m pip install -r Scripts/requirements-opus-lulu.txt
/tmp/lulu-opus-env/bin/python Scripts/prepare-opus-lulu.py --workspace /tmp/lulu-opus-work
```

这只准备工作环境，不生成新模型，不替换 Unity 角色。环境需有 C++ 编译器；实际渲染和运行另需 Blender/Unity。先看 WIP 与已有三张对照图，再定向修正 HANDOFF 的未完成项。

## r07 其余接续

读取 `R07-任务分工-20261024.md`、`R07-DeepSeek-交付索引-20261024.md`、`r07-ground-shading-spec.md`、`r07-D1-O5-谷仓验收-20261024.md`。

- D1/D5/D2/D3/D4/D6/D7 已有执行成果，等 Opus 验收，不重做整套。
- O4 方案已写；O5 摆放返工意见尚未落实到 Builder，须核对。
- O2 长帧和 O3 淡出需接续诊断，不能凭性能表推定原因。
- 当前 Unity 仍使用旧 locomotion-r08，场景 integration-r07-D6。新 Lulu 验证前不默默替换。
- 当前报告、截图、日志与导出的 Profiler 时间线另外补入证据交付。约 80GB 原始 .data 继续保存在本机，未伪称全部上传。完整模型历史和冻结 r06 包也保留本机。

沿用固定版本、Builder 持久修改、原件保护、两轮失败停止和 D7 实际复验要求。技术、视觉初审、用户美术、资源优化、设备验证分别记录。Android 真机暂缓，不扩展玩法。
