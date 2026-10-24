from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1]
p=Path('/Users/haowen/Documents/Obsidian Vault/04 project/Farm/Lulu 资产说明.md')
backup=r/'review/lulu-rig-20261018/baseline/Lulu 资产说明.md'
if not backup.exists():shutil.copy2(p,backup)
if 'Lulu 基础绑定副本 r04' in p.read_text():
 print('Current formal and rig registration already present.');raise SystemExit(0)
s=p.read_text().replace('更新：2026-10-17。','更新：2026-10-18。')
s=s.replace('**当前默认预览**；已去掉尾巴','上一正式外观基线；保留历史文件')
line='| Lulu 正式版 v1 `official` | `public/models/lulu-official-v1.glb` | `assets-source/lulu-official-v1.blend` | **当前默认，用户已确认 cheekfix-r4**；静态外观与获批文件一致 |\n| Lulu 基础绑定副本 r04 | `public/models/rig/lulu-rig-r04.glb` | `assets-source/rig/lulu-rig-r04.blend` | 23 根骨骼与蒙皮；独立副本，肩腋动态仍需精修 |\n'
s=s.replace('| Meshy 原始版 `original`',line+'| Meshy 原始版 `original`')
s=s.replace('：无尾版。','：Lulu 正式版 v1。').replace('Lulu 当前无尾版、牛、羊、鸭','Lulu 正式版 v1 与动物资产')
s=s.replace('- 当前无尾 Meshy 版是静态模型，约 19.7 万三角面；**没有骨骼、蒙皮权重或动画片段**。早期程序模型中的动作不属于这份模型。','- 正式外观 v1 为约 19.7 万三角面的静态模型。独立 r04 绑定副本在 Blender 中创建骨架与权重；当前没有 Mixamo 动作或正式走跑片段。早期程序模型中的动作不属于这份模型。')
s=s.replace('- 后续骨骼绑定先用副本验证待机、行走、抬臂，检查肩腋、裤裆和脚底。绑定结果需在浏览器中实际播放后判断。','- 独立绑定副本含根骨、骨盆、脊柱、头颈、双侧肩臂、手掌与腿脚，共 23 根骨骼；无手指骨。头脸、五官、耳朵和橘子整体跟随头骨，每顶点最多 4 个影响。静止形体、UV 和贴图保留正式外观。\n- [骨骼绑定对比预览](http://127.0.0.1:5173/rig.html)：同机位对照正式静态版，提供骨骼显示、灰模、正侧背和转头/摆臂/屈膝检查。肩腋与腕旁相连网格在摆臂时仍有牵拉，尚未通过完整动作验收。接 Mixamo 前需处理连接与权重；不要宣称已能直接做成熟游戏动作。')
s=s.replace('## 5. 原件校验','正式版 v1 SHA-256：`5f770f539c3927b9e4d26a73bf96070e86e6b6cdd04e9710074b4c6645207e7d`。来源 `lulu-meshy-cheekfix.glb` 保留原名供追溯；正式 GLB 与它字节一致。绑定记录见项目 `review/lulu-rig-20261018/`。\n\n## 5. 原件校验')
p.write_text(s)
print('Updated existing Lulu asset note; previous note backed up in project.')
