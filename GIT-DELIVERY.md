# Git 交付状态

日期：2026-10-24。

- 目标：`https://github.com/pangzero/lulu-farm`，必须为私有仓库。
- 本地仓库：`/Users/haowen/GameProject/farm-game`，分支 main。
- 当前状态：Private remote delivery completed, including current Opus Lulu work and user-approved r07 non-raw evidence. See the supplement and R07-REMOTE-DELIVERY-CHECK-20261024.json for actual verification; the initial commit totals below are historical.
- 首次内容：约 2.1GB 工作树；913 个 LFS 文件，去重后 766 个对象、1,613,152,049 字节。包含完整 Unity 已暂存运行资产、代码、文档和参考图。
- 本机 165GB 工作区的历史原件、网页模型库、82GB Evidence、编辑器和缓存不在此首次上传范围；本地未删除。完整远端素材范围若调整，另做容量清单。
- GitHub 连接器账号为 pangzero；现有 SSH 账号为 harveyPang。仓库使用 HTTPS 独立认证，不改公司项目 SSH。
- Git LFS 和 gh 便携工具位于 `/Users/haowen/GameProject/.tools/bin`。本机可运行 `./Scripts/git-local.sh status`；其他机器按 README 安装 Git LFS。
- 用户已明确同意 GitHub CLI 授权；本机实测登录为 pangzero。HTTPS 凭据助手仅配置在本仓库。凭据保存目录在农场仓库之外，未暂存。拟提交代码经过常见私钥／GitHub token／AWS access key 模式检查，未发现匹配；这不是完整安全审计。

## 迁移验证

新目录下 npm build 已实际完成；Unity 6000.3.16f1 实际打开、编译并正常退出；三份当前资产清单共 994 个新根目录引用均存在。403 个保护文件实际 SHA256 无变化。浏览器已加载 B01 r03，源文件下载链接指向 GameProject。迁移后的现有 macOS 开发包已实际运行并正常退出，正常／调试界面截图已打开。LFS 对象核验完成，655 个 Unity glTF 外部依赖均已跟踪。

完整日志、路径备份和本机检查结果在 migration/20261024-080422/（不提交）。历史验收结论没有因迁移而提升。

## 远端实际核验

从远端新建无工作树的隔离部分克隆，核对提交 SHA；另从 Git LFS 下载总览参考图与 E01 模型几何，分别核对 SHA256 和字节数，均一致。此项验证资源可下载，不等于在另一台电脑完成 Unity 构建。

- 总览图：2,272,242 字节，SHA256 `961574bbfb3f32c50a3fdc4c04d9b0190e4478231506c9f660ee395b58ba3a44`。
- E01/model.bin：321,408 字节，SHA256 `dd1c46e04b8c2c0cb98dea77cfbc3d93f97ecafdb891a4e866a1251f335051c8`。
- 首次大文件上传后普通 Git 请求出现 HTTP 401/Broken pipe；改用 HTTP/1.1 与 50MiB 请求缓冲后，同一分支推送成功，没有强推或重写历史。这两项网络配置只在本仓库保存。
- 证据：本机 `migration/20261024-080422/remote-verification.json`、`git-push-http1.log` 和网页截图。

## Current Opus work supplement (2026-10-24)

New Lulu was omitted from the initial scope. Commit `8417f26` has now been pushed with 60 exact existing work files (460,789,639 bytes), including source, portable/clay versions, patches, WIP, all existing O1 tools, comparisons, polish baseline, original references, locomotion master and wardrobe textures. SHA256 is recorded per file; no preserved source was edited.

User separately approved the r07 evidence supplement: 3,811 existing files / 2,578,979,254 bytes, excluding 554 binary Profiler files / 80,346,057,052 bytes that remain local. Reports identify valid sessions and failure attempts. Filtered timelines do not replace full binary Profiler captures. The original initial-scope totals above are historical, not current repository totals.

Use `lulu-farm-unity/Docs/R07-OPUS-CONTINUE-20261024.md` and both remote manifests for the updated scope and continuation.

Supplement verification completed: all 60 Lulu files were downloaded from a fresh remote clone and matched SHA256. All 3,811 r07 paths were checked; 1,259 regular file hashes and 2,552 LFS pointer hashes/sizes matched. An actual D6 screenshot and compressed valid-session timeline were downloaded, hash-checked and decoded. All 3,871 local source/evidence file hashes were rechecked unchanged. No model, scene or art state was promoted by this transfer. Current LFS content: 2,796 unique objects / 4,128,680,840 bytes.
