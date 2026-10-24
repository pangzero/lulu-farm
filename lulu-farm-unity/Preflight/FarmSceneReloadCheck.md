# FarmWorld 重入／资源生命周期检查

实现：`Assets/Farm/Scripts/Runtime/FarmSceneReloadCheck.cs`。已在 r06 macOS Player 实际执行：基线加三次重入，全部对象／静态注册表判断通过。证据为 `Evidence/mac-player-reload-r06/reload-check-20261023-030328-039/reload-check.json`；内存另行记录，不据三次循环推断永久无泄漏。

普通启动没有 `--farm-reload-check` 时，不创建检查对象、不执行协程、不重载场景。启用时仅观察器使用 `DontDestroyOnLoad`，保留默认场景和所有角色／资产源。先记录初始化基线，再通过 `SceneManager.LoadSceneAsync(currentBuildIndex, LoadSceneMode.Single)` 对同一 FarmWorld 正常重入三次。

每轮等待 bootstrap 的玩家、相机、诊断和 UI 初始化完成，再等待至少 3 秒，执行 `Resources.UnloadUnusedAssets`、完整 GC 与一帧等待，然后记录实际值。没有瞬移、截图、相机驱动、模型／材质修改或手工复制场景对象。

## 执行

主流程将新代码编入 macOS 开发包后，在没有其他该包进程时启动：

```bash
cd /Users/haowen/GameProject/farm-game/lulu-farm-unity
open "Builds/macOS/LuluFarm.app" --args \
  --farm-reload-check \
  --farm-evidence "$PWD/Evidence/macos-reload-check" \
  --farm-quit-after 120
```

`--farm-quit-after 120` 保留现有 bootstrap 的总时限；检查器完成后也会主动退出（对象检查通过返回 0，失败返回 1）。不传该参数时，完成后保留农场运行供查看。若总时限先到，记录 `failed_or_incomplete`，不能以进程正常关闭判定通过。不要同时使用 `--farm-route`、`--farm-performance-route` 或 `--farm-record-frames`；检查器会拒绝这种混用。

## 结果

输出到指定证据根目录下的 `reload-check-<UTC>/reload-check.json`，每一轮写入一次，保存初始化基线加三次重入共四个样本。主要记录：

- 活跃场景路径／build index、已加载场景数、根对象及局部／全局 Renderer 数量。
- runtime、玩家控制器、输入、HUD、EventSystem、诊断器和检查器实例数量。
- 场景中启用的 occluder 数量、静态注册集合数量、已销毁引用和异场景残留数。
- Mono 使用／保留、`GC.GetTotalMemory`、Unity 分配／保留／未使用保留字节，以及可用时的进程 working set。

期望只有一个正常 FarmWorld 与一个初始化 runtime；重入后 Renderer／根对象／静态 occluder 数应回到初始基线，静态集合应没有销毁引用和异场景条目。每个判断保存 `expected`、`observed`、`passed`。总状态 `object_lifecycle_checks_pass_memory_recorded` 只表示这些对象与注册表检查通过，**不表示全面无内存泄漏、画面通过或性能达标**。

Unity allocator 总量并非独立 native-only 内存；进程 working set 也包含托管、原生及映射内存。三个循环的内存增长需要结合缓存与资源生命周期分析，脚本不凭任意增长阈值宣告泄漏或清零。强制 GC／UnloadUnusedAssets 会扰动帧时，该会话不能进入性能热测统计；性能需单独重新启动、固定画质与分辨率运行。

最终需由实际执行者检查报告有四个样本、`completedReloads=3`、状态与每项判断一致，并查看 Player 日志有无加载／销毁异常，再填写设备和执行结论。
