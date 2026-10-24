# 噜噜农场

Unity 6.3 LTS + URP 的第三人称农场工程。当前交接候选 integration-r07-D6；DeepSeek 执行部分已完成，Opus 的新角色、长帧、淡出与最终美术验收仍需接续。技术记录不等于用户美术认可。

## 目录

- `lulu-farm-unity/`：可打开的 Unity 工程，包含运行资产、场景、Prefab、材质、代码和包锁。
- `lulu-studio/`：资产处理与网页预览的代码、工具和文档；完整原件和历史候选仍在本机。
- `art-concepts/`：总图与概念图。
- `AGENTS.md`：协作入口。

## 获取与运行

安装 Git LFS 后，用具有此私有仓库访问权限的 GitHub 账号执行：

```sh
git lfs install
git clone https://github.com/pangzero/lulu-farm.git
cd lulu-farm
git lfs pull
```

通过 Unity Hub 使用 **6000.3.16f1 Apple Silicon** 打开 `lulu-farm-unity/`；不要升级 Packages/manifest.json 或 packages-lock.json 中的版本。场景为 `Assets/Farm/Scenes/FarmWorld.unity`。

本机编辑器位置为 `.unity-install/Editors/6000.3.16f1/Unity.app`；编辑器本体不会提交。历史 CLI 包装脚本使用这个相对位置，其他机器可将同版本编辑器链接到这里再运行。应先读 Docs 中的分工与复现说明，避免重建覆盖其他 agent 的新工作。

## Git 范围

首次版本管理范围是代码、当前文档、概念参考及 **Unity 已暂存的完整运行资产**。材质、图片和几何缓冲等二进制通过 LFS 保存，Unity 的 .meta 与包锁一起提交。

本机美术库的 public、assets-source、review、reference-source 及历史资产清单未纳入首次远端；网页源工程保留，但远端克隆不包含完整网页模型库。没有把当前 Unity 场景所需运行资产排除在外。

Unity Library、编辑器安装、node_modules、dist、游戏包、Delivery、原始 Profiler、迁移备份不提交。这不是本机 165GB 工作区的全量备份。美术编辑和历史证据复现仍需本机归档；迁移并没有删除它们。

## 交接

- `lulu-farm-unity/Docs/R07-任务分工-20261024.md`
- `lulu-farm-unity/Docs/R07-DeepSeek-交付索引-20261024.md`
- `MIGRATION-20261024.md`

本机规范路径：`/Users/haowen/GameProject/farm-game`。旧 IdeaProjects 地址是兼容软链接。

## Opus r07 current work

The current new-Lulu sources, O1 WIP, tools, screenshots, rig master and wardrobe dependencies are now versioned at their original relative paths. Start at `lulu-farm-unity/Docs/R07-OPUS-CONTINUE-20261024.md`; do not restart or overwrite completed work. The Unity scene still uses the older replaceable character until the new candidate is validated.

The user also approved preserving r07 reports, images, logs, short recordings and exported timelines under `lulu-farm-unity/Evidence/r07/`. Full raw Profiler `.data` files remain local and are indexed separately in `R07-EVIDENCE-REMOTE-MANIFEST.json`. This is a limited exception to the broader local art/history archive exclusion described above.
