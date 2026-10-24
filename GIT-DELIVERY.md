# Git 交付状态

日期：2026-10-24。

- 目标：`https://github.com/pangzero/lulu-farm`，必须为私有仓库。
- 本地仓库：`/Users/haowen/GameProject/farm-game`，分支 main。
- 当前状态：本地 Git/LFS 已建立；远端私有仓库已创建，连接器核实 visibility=private、push=true。首次推送尚未执行：GitHub CLI 登录页面列出覆盖全部私有仓库、公钥、Gist 和组织信息的既有权限，自动审批拒绝代点授权，等待用户明确选择授权范围。
- 首次内容：约 2.1GB 工作树；776 个 LFS 文件，去重后 766 个对象、1,613,152,049 字节。包含完整 Unity 已暂存运行资产、代码、文档和参考图。
- 本机 165GB 工作区的历史原件、网页模型库、82GB Evidence、编辑器和缓存不在此首次上传范围；本地未删除。完整远端素材范围若调整，另做容量清单。
- GitHub 连接器账号为 pangzero；现有 SSH 账号为 harveyPang。仓库使用 HTTPS 独立认证，不改公司项目 SSH。
- Git LFS 和 gh 便携工具位于 `/Users/haowen/GameProject/.tools/bin`。本机可运行 `./Scripts/git-local.sh status`；其他机器按 README 安装 Git LFS。
- 凭据保存目录在农场仓库之外，未暂存。拟提交代码经过常见私钥／GitHub token／AWS access key 模式检查，未发现匹配；这不是完整安全审计。

## 迁移验证

新目录下 npm build 已实际完成；Unity 6000.3.16f1 实际打开、编译并正常退出；三份当前资产清单共 994 个新根目录引用均存在。403 个保护文件实际 SHA256 无变化。浏览器已加载 B01 r03，源文件下载链接指向 GameProject。迁移后的现有 macOS 开发包已实际运行并正常退出，正常／调试界面截图已打开。LFS 对象核验完成，655 个 Unity glTF 外部依赖均已跟踪。

完整日志、路径备份和本机检查结果在 migration/20261024-080422/（不提交）。历史验收结论没有因迁移而提升。
