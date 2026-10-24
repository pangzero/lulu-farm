# 噜噜农场 Unity 电脑版整合候选 r06

日期：2026-10-23。完整 FarmWorld 与 macOS 可运行候选 r06 已具备，实际路线、人工界面、场景重入与 15 分钟持续测试已执行。偶发长帧和透明遮挡外观仍有保留项，不能将本候选称为所有 M0–M6 项目及平台均已验收。用户美术待确认。机器可读记录：`Evidence/final-acceptance-r06-20261023.json`。

## 范围与采用

- 原总图：左侧 20 块田、后方单栋中央主屋与农产摊位、前方牧场、右侧池塘／码头／渔产摊位，土路连接，树灌木与白花布置边缘。
- 73 项主资源已登记并导入：14 成熟作物、14 共享原型幼苗、15 动物、21 新设施环境、8 复用接口、1 Lulu。141 个主／LOD模型 payload。场景引用59种ID；未摆放库资源、E03/E04/E07连续场景面、未选E06均在逐项清单解释。
- 只摆总图对应的5种代表动物；其他10种在库内可替换，不增加动物AI。
- Lulu 原模型冻结，使用用户允许暂用的 locomotion-r08。现有模型外观缺陷继续保留；不接入拒绝版本。

## 检查结果

| 维度 | 结果 | 证据 |
|---|---|---|
| Unity／包版本 | 6000.3.16f1；URP17.3.0；Cinemachine3.1.5；Input1.14.2；glTFast6.20.0 | Packages/manifest.json、packages-lock.json、实际缓存版本 |
| macOS 构建 | r06成功，0错误0警告，775,768,784字节；Universal arm64+x86_64；本机只测arm64 | Evidence/full-world-mac-r06-20261023.log、build-macOS.json |
| 场景／接口 | 单主屋、20块1.2×1.2田格、根部着地、闭合池岸、牧场门口与码头探针通过 | Evidence/scene-contact-audit.json、acceptance/20261023-015045-937/ |
| 实际路线 | r06自动InputSystem事件驱动，31/31点，绕码头和屋后旋转并返回；没有瞬移 | Evidence/mac-player-route-r06-final/20261023-030424-380/automated-route.json |
| 实际界面／鼠标 | 聚焦的mac窗口内观察到走动、拖动旋转、UI起点隔离、暂停阻断、恢复、阶段／材质／画质切换和保存图像 | Evidence/manual-ui-r06-final-review-20261023.json |
| 田地阶段几何 | 同相机实际点击混合／幼苗／成熟并查看3图，20格植物实际变化 | Evidence/field-stage-manual-r06-review-20261023.json |
| 场景重载 | 正常Single模式重载3次；每次1281渲染对象、1 runtime、15遮挡对象，无重复累积；内存值单列，不据三次推断永久无泄漏 | Evidence/mac-player-reload-r06/reload-check-20261023-030328-039/reload-check.json |
| 固定图／视觉初审 | r06固定12张＋路线25张逐张实际复核；透明树／房屋叠层保留 | Evidence/world-review-20261023-015045/ |
| 录像 | 1277实际帧已编码，视频187.549秒；6个解码关键帧已打开核对，未声称逐帧完整观看 | Evidence/mac-player-route-r06-final/20261023-030424-380/walkthrough-r06.mp4 |
| 电脑性能 | M5／1280×720／全成熟20格／电脑档：有效917.684秒，7圈，逐帧均值8.393ms、P95 8.367ms；有8个窗口含>100ms长帧，其中3个>1秒，最长1859.271ms，卡顿验收未通过 | Evidence/mac-performance-r06-analysis-20261023/、performance-long-frames-r06-20261023.json |
| 用户美术 | 待用户验收 | 技术／助手初审均不代替用户认可 |

## 明确的检查限制

- Batch Editor 鼠标回归未通过并已停止该测试路线。真实Mac窗口的拖动／UI隔离另有实际操作证据，不能把失败的自动检查写成通过。
- 本轮原生窗口记录确认WASD步行；自动路线确认Run运动。CUA的Shift组合键未独立确认等同实体键盘长按，因此这一人工组合按键项仍待用户复核。
- 15分钟测试只对本机和当前场景密度作结论；CPU/GPU可用采样与不可用计数器分别列，不拿0冒充有效计时。温度没有测量。
- Android真机按用户要求暂缓，Windows／iOS未构建实测；通用触控代码及手机质量档不等于手机验收。
- 本地开发候选为ad-hoc签名，未公证、未商店上架。构建含Intel架构不代表Intel Mac已测试。

## 交付入口

完整工程：`/Users/haowen/GameProject/farm-game/lulu-farm-unity`。
主场景：`Assets/Farm/Scenes/FarmWorld.unity`。
可运行应用：`Builds/macOS/LuluFarm.app`。
操作与重建：`Docs/MACOS-交付与操作说明.md`、`Scripts/rebuild-macos.sh`。
逐件采用与来源：`Docs/ASSET-INTEGRATION-STATUS-20261023.md`和同名JSON。
保留问题：`Docs/KNOWN-ISSUES.md`。

播种收获、交易背包、动物AI、室内、开船和游泳是后续玩法。本轮保留S02、C12、C16暂缓；不继续其他资产批次。

## 可直接查看

- 电脑包：`Delivery/r06-20261023/LuluFarm-macOS-r06.zip`，解压双击应用。
- Unity源快照：`Delivery/r06-20261023/LuluFarm-Unity-source-r06.zip`；不含Library缓存，Blender源在相邻资产工程，完整索引已附。
- 实际录像：`Delivery/r06-20261023/LuluFarm-walkthrough-r06.mp4`。
- 选定验收证据：`Delivery/r06-20261023/LuluFarm-evidence-r06.zip`；原始1277帧保留工作区。
- 文件SHA256、解压逐文件核对与签名检查：`Delivery/r06-20261023/delivery-manifest.json`。

## 性能解释

低频CPU FrameTiming均值8.37ms、P95 8.71ms，GPU均值4.68ms、P95 6.09ms，不等于逐帧线程耗时。Unity分配内存首尾60秒均值变化约+0.16MiB，Mono+3.29MiB；不是RSS/显存测量。长帧位置分散，当前证据无法确认是渲染、GC、记录器或系统调度造成，未据平均值宣布无卡顿。需要独立Profiler Timeline定位，保留当前实际候选供视觉／功能验收。
