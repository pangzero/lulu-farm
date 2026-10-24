# 本机历史 Profiler 无损归档

用户授权：历史 `.data` 无损压缩到本机，核对解压 SHA256 后释放未压缩副本。

385 件原始数据归档在 `/Users/haowen/GameProject/local-evidence-archives/r07-profiler-20261025/`。原始字节 53,755,540,402；gzip 字节 15,072,357,811。逐件先解压流读取、核对字节数和 SHA256，再删除冗余未压缩副本，记录在 `archive-ledger.jsonl`。这些 gzip 不上传仓库。本轮 O6 原始 Profiler `.data` 仍在其各自会话目录，没有用归档覆盖。

恢复时按 ledger 的原路径和压缩路径解压到一个新临时文件，核对原始字节数与 `originalSha256`，确认目标路径不存在或内容完全相同后再放回；不要直接覆盖不同内容。使用同一锁定 Unity 编辑器读取。不要删除已核验归档。

这是存储整理记录，不是性能或美术验收。
