# 农场迁移记录

2026-10-24，用户授权将完整农场移到与 IdeaProjects 平级的 GameProject。

## 当前路径

- 工作区：`/Users/haowen/GameProject/farm-game`
- Unity：`lulu-farm-unity/`
- 美术与预览：`lulu-studio/`
- 总图与概念：`art-concepts/`
- 固定编辑器：`.unity-install/Editors/6000.3.16f1/Unity.app`

同文件系统原子改名完成迁移，没有重新复制模型。旧 `/Users/haowen/IdeaProjects/farm-game` 是指向新目录的兼容软链接，磁盘内容实际在 GameProject。旧聊天、历史检查记录、已归档交付和 Blender 内部旧绝对链接仍可经此入口解析；不要在旧地址另外新建第二套工程。

当前代码、网页源下载链接、当前资产清单、交接文档和 Unity Hub 编辑器登记已更新。两个现有 Obsidian 农场文档只替换工作区路径，没有改制作状态。部分 Python 制作脚本的工作区根目录改为从脚本位置推导。

历史 Evidence/review、原始模型、Blender 源、认可版本、构建及 Delivery 内的文件未改写；其中旧路径是当时记录，兼容入口继续有效。迁移不是资产修改，也不是新的美术验收。

## 核对与回溯

详细清单：`migration/CURRENT.txt` 所指目录中的 `migration.json`。盘点 118,308 个文件，未编辑文件的 inode、字节数、修改时间一致，未发现意外变化。112 个当前文本文件修改前的逐字节备份在该目录的 before/；Hub 与 Obsidian 文件备份在 external-before/。路径替换前后 SHA256 已记录。

验证结果在同一迁移目录归档。请以实际验证记录判断编译、网页和运行状态，不把改名成功当作实际运行验收。

## 远端与大文件

用户选择 GitHub 私有仓库 `pangzero/lulu-farm`。创建、认证和实际推送状态将记入 Git 交付文档，不能把配置了 remote 当成已上传。

Unity 缓存、Editor 安装、node_modules、生成的网站 dist、游戏包、历史交付和原始 Profiler 数据保留本地，不进入普通 Git。需要版本管理的二进制由 Git LFS 管理。远端初次素材范围正在按用户选择整理；本地所有原件与历史文件均保留。

本机原有 Git SSH 身份是 harveyPang，而连接器身份是 pangzero。不得为推送本项目改掉公司项目的 SSH 配置；使用项目自己的已授权认证。

## Claude 接续

先 `cd /Users/haowen/GameProject/farm-game`，读取本目录 AGENTS.md 和两子工程 AGENTS.md，再读 r07 分工与交接索引。以实际文件核对 Opus 进度。不要因路径变化重新生成整套资产，也不要把旧路径的兼容软链接当成另一份工程。
