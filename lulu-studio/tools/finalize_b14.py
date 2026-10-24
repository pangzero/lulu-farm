"""Package already inspected B14 r02; no modeling/rendering and no art approval."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];Q=R/'review/farm-assets/B14';D=Q/'r02'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(D/'metrics.json');g=m['glb'];s=m['source'];clear=read(D/'entrance-clearance.json')
assert all(not d[k] for d in g['modules'] for k in ['zero_area','duplicate_index_faces','invalid_vertices','invalid_normals','welded_boundary_edges','welded_nonmanifold_edges'])
assert clear['result']=='pass'
preserve=[{'file':p,'before':h,'after':sha(Path(p)),'unchanged':h==sha(Path(p))} for p,h in read(Q/'preservation-before.json').items()]
assert all(x['unchanged'] for x in preserve)
write(Q/'preservation-check.json',{'all_unchanged':True,'files':preserve,'scope':'B01/B02 accepted production files, official Lulu, revised animals and cow, crop manifests, structure reference board. B03 has separate38-file closeout protection.'})
write(Q/'metrics.json',m)
settings=read(D/'review-settings.json')
for key in ['fence_interface','native_three_camera','native_detail_cameras','sample_design_inference','crop_scale']:
    settings.pop(key,None)
settings['note']='B14 r02 complete central-house exterior. Source and GLB share authored units. r01 retained as visible wall-corner seam history. Native/source vs GLB comparisons use fixed cameras. Web and native lighting/color are inherited B01 settings, not pixel-identical.'
settings['web']['close_cameras']={'house':{'target_y_up':[0,2.5,0],'orthographic_height':7.3},'scale':{'target_y_up':[0,2.25,0],'orthographic_height':8.5},'door':{'target_y_up':[0,1.2,1.8],'orthographic_height':3},'roof':{'target_y_up':[0,4.2,0],'orthographic_height':5.8}}
settings['web']['scale_layout']={'house_position_y_up':[0,0,0],'lulu_position_y_up':[3.3,0,2.4],'lulu_height':1.2}
settings['web']['browser']='Chrome live QA; additional Codex In-app Browser final inspection. See browser-validation.json.'
settings['web']['qa_viewport']='Actual browser viewport/CSS and canvas are recorded by browser checks; canvas1280x720 DPR1.'
write(D/'review-settings.json',settings);write(Q/'review-settings.json',settings)
views=['front','side','back','quarter','top','left']
native=[str((D/f'{mode}-{v}.png').relative_to(R)) for mode in ['material','clay'] for v in views]
extras=['detail-door','detail-window','detail-chimney','detail-corner','lulu-entrance','lulu-scale','entrance-clearance','farm-distance','glb-quarter','glb-side','glb-back','r01-controlled-quarter','r01-controlled-side','r01-controlled-back']
native += [str((D/(f+'.png')).relative_to(R)) for f in extras]
for p in native:assert (R/p).is_file(),p
observations=[
 {'criterion':'完整主屋四面、整体比例与屋顶','result':'初审通过','evidence':native[:12],
  'observation':'实际查看材质/灰模六视图含额外左侧；完整弧形双坡屋顶、连续厚墙、前后三扇和左右各两扇拱窗。所有立面有同类窗框厚度与收口。r02连续厚壳消除r01侧墙角细缝。'},
 {'criterion':'门窗进深、真实厚度与局部连接','result':'通过','evidence':['review/farm-assets/B14/r02/detail-door.png','review/farm-assets/B14/r02/detail-window.png','review/farm-assets/B14/r02/detail-corner.png'],
  'observation':'墙体名义厚.34；门窗为真实开孔与深衬圈，玻璃面退入墙厚，十字框分段避免叠面；窗台/托木为实体。门板有连续背板，板缝不透背景。'},
 {'criterion':'屋瓦层次、烟囱厚壁与屋面接触','result':'初审通过，有保留项','evidence':['review/farm-assets/B14/r02/material-top.png','review/farm-assets/B14/r02/detail-chimney.png','review/farm-assets/B14/r02/clay-quarter.png'],
  'observation':'完整连续底层承托独立瓦片、屋脊帽和木梁托木；烟囱有厚壁、开口和下沉喉口，斜面泛水与屋顶落座。瓦片规则网格和烟囱组装缝保留，未声称概念图的装饰绿植和附属摊棚已制作。'},
 {'criterion':'Lulu入口净空、世界比例及着地','result':'通过（静态造型）','evidence':['review/farm-assets/B14/r02/entrance-clearance.json','review/farm-assets/B14/r02/entrance-clearance.png','review/farm-assets/B14/r02/lulu-scale.png','review/farm-assets/B14/r02/farm-distance.png'],
  'observation':'官方Lulu只读实例高1.2、宽约.7587；木框净宽1.11、两侧最小余量约.175，中央顶部余量.615，正面投影全部顶点在拱门净空内。仅QA内隐藏门扇，不代表动画/通行功能。主屋GLB最低Z=0，台阶实体相接；农场12×8格/1.2间距固定相机。'},
 {'criterion':'可编辑源重开、GLB实际回读与几何','result':'通过','evidence':['review/farm-assets/B14/r02/source-reopen.json','review/farm-assets/B14/metrics.json','review/farm-assets/B14/review-r02.log'],
  'observation':'269原生分件归为8类；导出8个glTF网格、22材质primitive、13材质，无贴图和外部引用。回读零面积、重复索引面、无效坐标/法线、诊断焊合后开放边/非流形均0，无相机/灯/QA地台导出。'},
 {'criterion':'新旧同条件与基准保护','result':'通过','evidence':['review/farm-assets/B14/r02/controlled-r01-r02.jpg','review/farm-assets/B14/baseline-reopen.json','review/farm-assets/B14/preservation-check.json'],
  'observation':'r01/r02真实GLB同相机、灯光、曝光和比例；实际重开B01三个r03与B02立面r04源/GLB，只读保留。32个开工保护文件哈希不变。'},
 {'criterion':'真实网页加载、版本/模块/材质切换与下载','result':'见实际网页记录','evidence':['review/farm-assets/B14/browser-validation.json'],
  'observation':'独立网页按需加载，支持8模块隔离、材质/灰模/线框、六方向、局部、Lulu和农场。浏览器执行结果和下载SHA另记，不由渲染成功代替。'},
 {'criterion':'用户最终美术、游戏预算与目标设备','result':'未验证','evidence':[],
  'observation':'等待用户美术采用。仅按模块合并导出与按需释放资源；未制作额外LOD，未测试目标设备性能。'}]
limits=['网页沿用B01固定灯光，背面比原生更暗、投影更硬；两种渲染器未做逐像素匹配。',
 '屋瓦分格和烟囱拼接缝较规则；细门纹在农场距离不作主要识别点。',
 '窗下木箱为空的建筑部件；花草、灯具、附属摊位与室内/动画/碰撞不属于本次交付。',
 '本候选待用户美术验收；106314三角面已如实记录，未由本机可显示推断目标设备流畅。']
write(Q/'acceptance.json',{'batch':'B14','asset':'S01','revision':'r02','date':'2026-10-18','status':'制作与技术/视觉初审完成，待用户验收',
 'scope':'One complete central-house exterior, native Blender editable modules. B02 remains facade-only.',
 'source':s['file'],'source_sha256':s['sha256'],'glb':g['file'],'glb_sha256':g['sha256'],
 'technical_status':'通过','visual_review_status':'通过（助手初审，有保留项）','user_art_status':'待用户验收',
 'optimization_status':'按模块合并导出及页面按需释放已完成；无独立LOD/预算验收','device_performance_status':'未测试',
 'checks':observations,'remaining_limitations':limits,
 'history':[{'revision':'r01','status':'保留失败候选','issue':'分墙倒角接缝在侧面明显；另存r02连续厚壳修正'},
 {'revision':'r02','status':'当前待用户验收','repair':'墙角接缝修正；早期验收比例图裁切另修相机，不改模型和灯光'}]})
write(Q/'visual-review.json',{'reviewer':'assistant actual image inspection','date':'2026-10-18','status':'初审通过，有保留项','opened_views':native,
 'boards':['r02/material-six-views.jpg','r02/clay-six-views.jpg','r02/details.jpg','r02/controlled-r01-r02.jpg','browser/color-board.jpg','browser/clay-board.jpg'],
 'full_size_focus':['r02/clay-back.png','r02/clay-side.png','r02/detail-chimney.png','r02/detail-door.png','r02/entrance-clearance.png','r02/lulu-scale.png','r02/farm-distance.png'],
 'observations':observations[:4],'limitations':limits})
write(Q/'provenance.json',{'kind':'native Blender authored construction; B02 helper functions and accepted palette retained',
 'reference':{'path':str(R.parent/'art-concepts/03-structures.png'),'sha256':sha(R.parent/'art-concepts/03-structures.png')},
 'accepted_baselines':read(Q/'baseline-reopen.json'),'current_source_sha256':s['sha256'],'current_glb_sha256':g['sha256'],
 'production_script':'tools/build_b14.py','r01_script_snapshot':'review/farm-assets/B14/backups/build_b14-r01.py',
 'protected_originals':'review/farm-assets/B14/preservation-check.json','revisions_kept':['r01','r02']})
p=R/'public/models/farm-assets/B14/manifest.json';d=read(p);d['status']='技术与视觉初审通过（有保留项），待用户验收';d['checks']={'technical':'通过','visual':'通过（有保留项）','user':'待验收','device':'未测试'}
d['assets'][0].update({'triangles':g['triangles'],'bytes':g['bytes'],'revision':'r02'})
d['versions']['r02'].update({'triangles':g['triangles'],'bytes':g['bytes']})
write(p,d)
README='''# B14 · S01 完整中央主屋 r02

沿用已认可 B02 r04 的奶油灰泥、蜜色木构、蓝窗与橙瓦，已完成一栋中央主屋外观。技术与助手视觉初审通过，有下述保留项；用户美术待验收，目标设备未测试。B02 仍是独立立面样段。

[打开实际预览](http://127.0.0.1:5173/b14.html?asset=house&revision=r02&module=all&layout=single&material=color&view=quarter) · [Lulu 比例](http://127.0.0.1:5173/b14.html?asset=house&revision=r02&module=all&layout=scale&material=color&view=quarter) · [B03 收尾](../B03/closeout-20261018/README.md)

| 交付 | 当前文件 |
|---|---|
| 原生可编辑制作源 | [s01-main-house.blend](../../../assets-source/farm-assets/B14/r02/s01-main-house.blend) |
| 当前 GLB | [s01-main-house.glb](../../../public/models/farm-assets/B14/r02/s01-main-house.glb) |
| 材质／灰模六视图 | [材质图板](r02/material-six-views.jpg) · [灰模图板](r02/clay-six-views.jpg)；各单张768×768独立保留 |
| 局部与比例 | [局部图板](r02/details.jpg) · [入口静态净空](r02/entrance-clearance.png) · [Lulu 全身比例](r02/lulu-scale.png) · [农场距离1280×720](r02/farm-distance.png) |
| 版本对照 | [r01／r02 同条件](r02/controlled-r01-r02.jpg) |
| 测量与验收 | [metrics.json](metrics.json) · [review-settings.json](review-settings.json) · [acceptance.json](acceptance.json) · [网页记录](browser-validation.json) |

源中269个可编辑分件归为8类：地基/台阶、连续墙壳、拱门、深框窗、空窗下木箱、木梁托木、曲面屋顶/瓦片、厚壁烟囱。GLB保留8个语义网格，22个材质primitive，13种材质，无贴图；106,314三角面、2,236,032字节。整体包围尺寸约5.460×4.750×5.280（宽×深×高），最低Z=0。

墙厚约0.34。入口结构洞宽1.18，木框净宽1.11。只读官方Lulu展示高1.2、宽约0.7587，静态投影最小单侧净余量0.175，中央顶余量0.615；0个投影顶点越出拱门。QA图临时隐藏门扇，仅说明静态尺寸，生产源和GLB仍为关闭门扇外观。门槛台阶顶Z=.30、木衬底Z=.31，未实现室内、开门动画、导航或碰撞。

r01的独立墙件倒角在墙角形成明显细缝；r02改连续厚壳并保留其他模块。r01源/GLB和同条件证据保留。两次导出前几何诊断发现重合倒角端点，已用源中可编辑的1微单位焊合修正；最终源/GLB回读没有退化面、非法坐标/法线或诊断开放/非流形边。

已实际查看材质/灰模六视图、局部、背面/侧面GLB回读、入口、Lulu和固定农场图，另做实际网页切换和下载检查。B01三个r03及B02 r04源/GLB已只读重开；32个保护文件哈希保持不变。B03另外保存38文件保全记录。

保留项：瓦片和烟囱分格较规则；网页沿用B01照明，背面比原生更暗、影子更硬。空窗下箱属于建筑部件，未添加花草、灯具或摊位。仅做按模块合并和网页资源释放，没有独立LOD或设备性能通过结论。

本次 B14 与 B03 收尾并行完成后等待用户验收，不启动 B15–B22。
'''
(Q/'README.md').write_text(README)
print('B14 evidence finalized; user acceptance pending')
