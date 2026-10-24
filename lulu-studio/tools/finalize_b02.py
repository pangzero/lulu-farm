"""Historical B02 r04 packager; refuses to overwrite accepted user approval."""
import json,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'review/farm-assets/B02';OUT=ROOT/'public/models/farm-assets/B02';REV='r04'
if (QA/'acceptance.json').exists() and json.loads((QA/'acceptance.json').read_text()).get('user_art_status')=='用户通过':
    raise RuntimeError('B02 art already accepted; do not overwrite approval metadata.')
metrics=json.loads((QA/'metrics.json').read_text())
for key in ['s01','s05_repeat','s05_endcap']:
    v=metrics[key]
    for field in ['zero_area_faces','nonfinite_vertices','invalid_face_normals','duplicate_index_faces','welded_boundary_edges','welded_nonmanifold_edges','exported_cameras','exported_lights']:
        assert v[field]==0,(key,field,v[field])
    assert not v['negative_transform_objects'] and not v['negative_signed_volume_meshes'] and not v['external_uris']
    assert REV in v['file'] and v['readback']=='success'
assert all(abs(c['left_gap'])<c['tolerance'] and abs(c['right_gap'])<c['tolerance'] for c in metrics['three_segment_assembly']['joint_checks'])
assert json.loads((QA/'preservation-check.json').read_text())['result']=='pass'
for a in ['s01','s05']:
    for m in ['material','clay']:
        for v in ['front','side','back','quarter','top']:assert (QA/f'{a}-{REV}-{m}-{v}.png').exists()

settings=json.loads((QA/'review-settings.json').read_text())
settings['note']='B02 current candidate is r04. Initial images are preflight evidence; s01-r01-controlled-quarter and r04-glb-quarter share final native camera/light/exposure. Browser controlled r02/r04 back views preserve the camera across version changes.'
settings['web']['close_cameras']={'facade':{'orthographic_height':4.6,'target_y_up':[0,1.45,0]},'fence':{'orthographic_height':1.85,'target_y_up':[0,.46,0]},'three':{'orthographic_height':2.8,'target_y_up':[0,.46,0]},'scale':{'orthographic_height':5.25,'target_y_up':[0,1.35,0]}}
settings['web']['scale_layout']={'facade_position_y_up':[-2,0,-.3],'fence_row_centre_y_up':[2.25,0,.5],'fence_repeat_step':1.2,'lulu_position_xz':[0,1.5],'lulu_height':1.2}
settings['web']['browser']='Codex In-app Browser (IAB), local macOS ARM64; exact Chromium version not collected'
settings['performance']={'target_devices':'未测试','fps':'未测试','scope':'Visual/technical asset validation only; no mobile performance acceptance.'}
(QA/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2))

def check(criterion,observation,evidence,result='通过'):
    for p in evidence:assert (ROOT/p).exists(),p
    return {'criterion':criterion,'result':result,'evidence':evidence,'observation':observation}
q='review/farm-assets/B02/'
shared=[check('可编辑源文件重新打开、实际GLB回读、几何与材质可携带','两份源重新打开并渲染；三份GLB回读成功，零面积/重复索引面/非法顶点/无效法线均为0；焊接诊断后边界与非流形边为0；无外部贴图，无相机灯光地台混入。部件内部装配接合不等同意外穿插。',[q+'metrics.json',q+'review-r04.log']),check('真实网页加载、显示和视角切换','已从crops.html入口打开；实际选择S01/S05、r01/r02/r03/r04、材质/灰模/线框、五视角、三段场景、Lulu比例、农场距离与自动旋转。实际画布与CSS均1280×720，DPR设为1，验收视口1330×1100。',[q+'browser-validation.json',q+'browser-scale-r04.jpg',q+'browser-farm-r04.jpg',q+'web-build.log']),check('同世界尺度与只读基准保护','Lulu高1.2，实例scale=.6313689262131015；B02保持制作尺寸。B01 r03源/GLB、Lulu和参考板哈希均未变化。',[q+'preservation-check.json',q+'browser-scale-r04.jpg'])]
assets=[{'asset':'S01','name':'主屋门窗墙面屋檐立面样段','scope':'Facade sample ONLY; not a complete house; no interior navigation/collision/gameplay.','stage':'facade-sample','revision':REV,'source':'assets-source/farm-assets/B02/s01-facade-sample-r04.blend','glb':'public/models/farm-assets/B02/s01-facade-sample-r04.glb','checks':[
check('门窗具有真实进深与实体厚度','340mm墙体切出实际拱洞，木门/玻璃退入墙体；完整木衬圈和实心门背板阻挡板缝透白。深色门饰是镶片，不宣称雕刻凹槽。',[q+'s01-r04-detail-door.png',q+'s01-r04-detail-window_eave.png',q+'s01-r04-material-side.png',q+'browser-controlled-back-r04.jpg']),
check('屋檐与木梁有厚度、柔和倒角且连接合理','弧形瓦檐有连续底层和实体瓦片、180mm木梁与托木；r03补曲线墙顶收口，背面不再有贯穿空隙；r04小饰件倒角修正消除64个退化三角面。',[q+'s01-r04-review-board.jpg',q+'s01-r04-material-back.png',q+'s01-r04-clay-back.png',q+'s01-controlled-repairs-r04.jpg']),
check('灰模轮廓、前侧背俯及使用距离可读','实际打开两组五视图、局部与网页；暖奶油墙、蜂蜜木构、橙瓦和蓝窗与建筑板及B01柔和哑光方向协调。网页更暗且阴影更硬，此差异保留记录。',[q+'s01-r04-review-board.jpg',q+'s01-r04-glb-quarter.png',q+'browser-farm-r04.jpg'])]+shared,'technical_status':'通过','visual_review_status':'通过（助手初审）','user_art_status':'待用户验收'},
{'asset':'S05','name':'围栏直段与末端柱附件','stage':'straight-module','revision':REV,'source':'assets-source/farm-assets/B02/s05-fence-r04.blend','glb':'public/models/farm-assets/B02/s05-fence-repeat-r04.glb','accessory_glb':'public/models/farm-assets/B02/s05-fence-endcap-r04.glb','checks':[
check('横档与柱体有实体厚度及柔和倒角','柱体.22×.24×.94，含木钉外包深.252；两横档.98×.11×.15，中心Z=.32/.67。横档YZ截面圆角，X端面保持平面对接，木纹稀疏。',[q+'s05-r04-review-board.jpg',q+'metrics.json']),
check('明确接头，三段连续无可见缝隙、重复柱或实体穿插','重复段仅拥有左柱和两横档，步长1.2；实例X=0/1.2/2.4，末柱X=3.6，形成四柱六横档。GLB顶点实测最大端面误差2.48e-7，低于1e-6容差；相邻段实体位于共用接触面的两侧。',[q+'s05-r04-three-quarter.png',q+'s05-r04-three-front.png',q+'s05-r04-three-back.png',q+'s05-r04-three-top.png',q+'s05-r04-joint-1.2.png',q+'s05-r04-joint-2.4.png',q+'metrics.json',q+'browser-fence-three-r04.jpg']),
check('前后侧和网页尺度一致','实际查看材质/灰模五视图及网页三段/比例；无缺面或黑面，栏高低于Lulu头部。网页细木纹有少量亚像素断续，未遮盖结构。',[q+'s05-r04-review-board.jpg',q+'s05-r04-glb-quarter.png',q+'browser-scale-r04.jpg'])]+shared,'technical_status':'通过','visual_review_status':'通过（助手初审）','user_art_status':'待用户验收'}]

record={'batch':'B02','revision':REV,'review_date':'2026-10-18','timezone':'Asia/Shanghai','status':'待用户验收','baseline':'B01 mature r03 accepted by user on 2026-10-18','assets':assets,'revision_history':[{'revision':'r01','status':'历史候选，已替代','issues':['墙脚侧面与窗格交叉处重合面产生黑斑']},{'revision':'r02','status':'历史候选，已替代','resolved':['重合面黑斑'],'issues':['灰模背面暴露檐墙空隙和门板缝透背景']},{'revision':'r03','status':'历史候选，已替代','resolved':['曲线墙顶收口、门背板及门窗深衬圈'],'issues':['两件薄门饰倒角产生64个退化三角面']},{'revision':'r04','status':'当前候选，待用户验收','resolved':['两门饰倒角宽度改为.006，导出前和回读均为零退化面']}],'remaining_differences':['网页沿用B01光照，整体比原生偏暗、阴影更硬；不逐像素匹配。','网页细木纹线略有亚像素断续；木纹保持从简。','样段背面、墙端、浅屋檐收口和围栏接口归属是基于参考的建模推导。'],'not_verified':[{'criterion':'移动端与目标设备性能','result':'未验证','reason':'本批未进行设备性能验收，不由本机可显示推断手机流畅。'},{'criterion':'用户最终美术认可','result':'未验证','reason':'等待用户明确反馈。'}],'next_step':'等待用户验收；不自动执行任何下一批。'}
(QA/'acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
manifest=json.loads((OUT/'manifest.json').read_text());manifest['status']='待用户验收';manifest['revision_history']=['r01','r02','r03','r04']
for a in manifest['assets']:
    a['revision']=REV;a['user_art_status']='待用户验收'
    k='s01' if a['id']=='S01' else 's05_repeat';a['sha256']=metrics[k]['sha256'];a['bytes']=metrics[k]['bytes'];a['triangles']=metrics[k]['triangles'];a['source_sha256']=metrics['sources']['s01' if a['id']=='S01' else 's05']['sha256']
    if a['id']=='S05':a['endcap_sha256']=metrics['s05_endcap']['sha256'];a['endcap_triangles']=metrics['s05_endcap']['triangles']
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

summary='''# B02 r04 验收包

状态：**待用户验收**。技术检查与助手视觉初审通过；不代表用户已认可。只完成 B02，不启动下一批。

- S01：门、窗、墙面和浅屋檐的立面样段，**非完整主屋**。没有室内、碰撞或玩法。
- S05：1.2 单位直栏重复模块，加一个同源末端柱附件。三段是四柱六横档。

## 打开实际预览

[B02 比例预览](http://127.0.0.1:5173/b02.html?asset=facade&revision=r04&layout=scale&material=color&view=quarter) · [三段围栏](http://127.0.0.1:5173/b02.html?asset=fence&revision=r04&layout=three&material=color&view=quarter) · [农场距离](http://127.0.0.1:5173/b02.html?asset=facade&revision=r04&layout=farm&material=color&view=quarter)

已从 crops.html 的 B02 链接进入并实际检查。可切换 r01–r04；旧版保留为历史对照。`npm run build` 通过，保留原有 Three vendor chunk 体积提示。

## 当前源文件与 GLB

| 资产 | 可编辑源 | 实际 GLB |
|---|---|---|
| S01 立面样段 | [s01-facade-sample-r04.blend](../../../assets-source/farm-assets/B02/s01-facade-sample-r04.blend) | [s01-facade-sample-r04.glb](../../../public/models/farm-assets/B02/s01-facade-sample-r04.glb) |
| S05 直栏 | [s05-fence-r04.blend](../../../assets-source/farm-assets/B02/s05-fence-r04.blend) | [重复段](../../../public/models/farm-assets/B02/s05-fence-repeat-r04.glb) · [末端柱](../../../public/models/farm-assets/B02/s05-fence-endcap-r04.glb) |

重复段原点在左柱地面中心；沿 X 放 0、1.2、2.4，末端柱放 3.6。单段则末柱放 1.2。不要把完整双柱栏段重复叠放。横档接触面 X=.11/1.09；柱体 .22×.24×.94，横档 .98×.11×.15。实测最大接触误差约 2.48e-7，容差 1e-6。

## 检查证据

- [逐项验收](acceptance.json)、[几何与哈希](metrics.json)、[固定条件](review-settings.json)、[网页验证](browser-validation.json)、[基准保护](preservation-check.json)。
- [S01 材质/灰模五视图板](s01-r04-review-board.jpg)、[S05 五视图板](s05-r04-review-board.jpg)。所有单张原图为 768×768。
- [门局部](s01-r04-detail-door.png)、[窗檐局部](s01-r04-detail-window_eave.png)、[三段拼接](s05-r04-three-quarter.png)、[接头1](s05-r04-joint-1.2.png)、[接头2](s05-r04-joint-2.4.png)。
- [同条件返修对照](s01-controlled-repairs-r04.jpg)、[网页 r02 背面](browser-controlled-back-r02.jpg)、[网页 r04 背面](browser-controlled-back-r04.jpg)。
- [实际网页比例图](browser-scale-r04.jpg)、[实际网页农场距离](browser-farm-r04.jpg)。

S01 25,406 三角面 / 575,520 字节；S05 重复段 3,048 三角面 / 85,940 字节，末柱 2,104 三角面 / 58,700 字节。均使用可导出的 Principled 哑光材质，无贴图依赖、无 QA 相机灯光地台；回读零面积面、非法顶点、重复索引面和无效法线均为 0。

实际查看了两件各材质/灰模五视图、局部、真实 GLB 回读图及网页；三段连续无可见缝或重复柱。r02 的背面贯穿空隙与门缝透白已修复；r04 清除门饰件退化三角面。门上的深色条是装饰镶片，不是雕刻槽。

保留差距：网页比 Blender 原生偏暗、阴影硬，细木纹少量亚像素断续。样段背面与接口为合理设计推导。Lulu 高 1.2，保持原件；B01 r03 及 Lulu 原件哈希不变。移动端/目标设备性能未测试；最终美术状态等待用户确认。

脚本：`tools/build_b02.py`（不可覆盖已存在版本）、`tools/review_b02.py`、`tools/finalize_b02.py`。历史模型、源文件与返修证据均保留。
'''
(QA/'README.md').write_text(summary)
print('B02 r04 packaged; user acceptance pending')
