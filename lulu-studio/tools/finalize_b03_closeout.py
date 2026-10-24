"""Package only verified B03 closeout evidence; does not change production assets."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'review/farm-assets/B03';Q=B/'closeout-20261018'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert 'B03_CLOSEOUT_NATIVE_COMPLETE' in (Q/'native-recheck.log').read_text()
metrics=read(Q/'metrics.json');sources=read(Q/'source-reopen.json');normal=read(Q/'glb-normal-texture-audit.json')
web=read(Q/'browser/checks.json');downloads=read(Q/'browser/download-validation.json');resources=read(Q/'browser/resource-cycles.json')
assert len(web)==63 and len(downloads)==8 and all(d['identical'] for d in downloads)
assert all(x['geometries']=='16' and x['textures']=='1' for x in resources['results'])
assert read(Q/'preservation-check.json')['all_unchanged']
names={'e01':'E01 空田格','e05':'E05 水岸直段','e07':'E07 水面格','e13':'E13 石头组'}
observations={
 'e01':['单件材质/灰模正侧背/3⁄4/俯视轮廓完整，土面、木边与四角为可编辑分件；r03不再有r01/r02导出黑色缺口。','1.2间距下方形底面连续；每格保留完整木边，相邻双轨约0.16宽，交点双柱较粗，这是保留项，须用户确认。','土面中心为约Z=-0.00226、浅耕痕略低；Z=0是种植/陆地约定。不能把全资产最低点归一到0。'],
 'e05':['草岸、实体岸芯和五颗岸石分件，侧背面闭合；后侧平地面Z=0。','沿X每1.2连续三段，端截面一致；当前实际三段图中未见透底缝，岸石大小有节奏但重复排列明显。','当前仅直岸，两端截面仍暴露用于接口检查；未做岸角或封闭池塘。'],
 'e07':['实际GLB为Z=-0.105的水平开放片，边界48条、厚度0属于明确设计；材质不透明，不把它判断为意外开口。','512×512颜色贴图已嵌入且解码正常；连续水面视觉无明显开裂，纹样仍呈多边形网格，连续铺设有重复感。','网页波纹只调制世界坐标明暗，无顶点位移；透明、水下鱼可见性、流体和波浪几何不在已完成范围。'],
 'e13':['三颗不对称圆石有前后层次，正侧背无翻面或黑面；三颗仍独立可编辑。','官方Z=0检查地面上足部接触正常；最低点0.000126为微小几何误差，未为此改动原模型。','保持柔和灰绿和细微色差；网页照明下比原生渲染对比更强，仍沿用固定B01网页灯光。']}
assets=[]
for a,n in names.items():
 m=metrics[a];assert sources[a]['reopened'] and m['zero_area_faces']==0 and m['duplicate_index_faces']==0 and m['nonfinite_vertices']==0
 assert normal[a]['finite_normals'] and normal[a]['zero_normals']==0 and not m['external_uris'] and not m['export_contains_qa']
 base='review/farm-assets/B03/closeout-20261018/'
 imgs=[base+f'{a}-r03-{kind}-{view}.png' for kind in ['material','clay'] for view in ['front','side','back','quarter','top']]
 assert all((ROOT/p).exists() for p in imgs)
 assets.append({'asset':a,'name':n,'revision':'r03','source_kind':'native_blender_editable_parts','source':m['source'],'glb':m['file'],'source_sha256':m['source_sha256'],'glb_sha256':m['sha256'],
 'technical_status':'通过（E07开放水平水片为设计例外）' if a=='e07' else '通过',
 'visual_review_status':'初审通过，有保留项','user_art_status':'待用户验收','optimization_status':'未新增模型优化版本；r03开销如实登记','device_performance_status':'未测试目标设备或帧率预算',
 'checks':[{'criterion':'制作源重开、可编辑分件和颜色管理','result':'通过','evidence':[base+'source-reopen.json',base+'native-recheck.log'],'observation':f"已重开原r03，{len(sources[a]['objects'])}个生产网格分件；未保存覆盖。"},
 {'criterion':'GLB实际读回、法线和纹理','result':'通过','evidence':[base+'metrics.json',base+'glb-normal-texture-audit.json'],'observation':'非有限坐标/零面积面/重复索引面/零法线均0，无外部纹理引用，无QA对象；UV/法线分裂顶点仅在诊断副本焊合。'},
 {'criterion':'材质与灰模五视图及局部','result':'初审通过，有保留项','evidence':imgs+[base+f'{a}-r03-detail.png',base+f'{a}-native-board.jpg'],'observation':observations[a][0]},
 {'criterion':'尺寸、着地和拼接接口','result':'通过，设计保留项待用户','evidence':[base+'metrics.json',base+'empty-tiles-r03-1280x720.png',base+'shore-r03-1280x720.png',base+'shore-r03-section.png',base+'shore-r03-seam-detail.png'],'observation':observations[a][1]},
 {'criterion':'新旧版本同条件对照','result':'通过','evidence':[base+'versions-controlled-board.jpg'],'observation':'r01/r02/r03实际GLB共同相机/曝光/背景/灯光/比例；未修改候选以制造改善。'},
 {'criterion':'实际网页、下载和资源切换','result':'通过','evidence':[base+'browser/checks.json',base+'browser/download-validation.json',base+'browser/resource-cycles.json'],'observation':'已实际切换并看网页；当前4份GLB与4份源实际下载SHA相同，三次农场切回E01资源恢复16 geometry/1 texture。'},
 {'criterion':'农场距离与Lulu只读比例','result':'通过（布局和可见性）','evidence':[base+'farm-r03-1280x720.png',base+'browser/farm-quarter.png',base+'review-settings.json'],'observation':'1280×720、DPR1、45度方位/50度俯角、约12×8格；Lulu正式v1只读，缩放0.6313689262131015，展示高度1.2。'},
 {'criterion':'最终用户美术与设备性能','result':'未验证','evidence':[],'observation':'等待用户明确反馈；未进行目标设备或完整农场性能测试。'}],
 'retained_limitations':observations[a][1:]})
acceptance={'batch':'B03','date':'2026-10-18','status':'收尾复核完成，待用户验收','current_revision':'r03','production_assets_modified':False,'new_revision_created':False,'scope':['E01','E05','E07','E13'],'assets':assets,'out_of_scope':['E06岸角','E03正式草地','完整封闭池塘','水下透明/鱼游动','B14建筑','Lulu及动物修改']}
dump(Q/'acceptance.json',acceptance);dump(B/'acceptance.json',acceptance)
validation={'date':'2026-10-18','batch':'B03','revision':'r03','url':'http://127.0.0.1:5173/b03.html?asset=e05&revision=r03&layout=shore&material=color&water=static&view=quarter','status':'实际网页复核通过','functional_capture_cases':len(web),'matrix':'4资产×2材质×5视角=40；4资产×3版本=12；拼接/田格/农场/水面模式10；view链接重开1',
 'canvas':[1280,720],'pixel_ratio':1,'native_five_view_images':40,'download_sha_identical':8,'errors':read(Q/'browser/console.json'),'resource_cycles':resources,
 'changes':['切换时释放上一个场景的几何/材质/贴图，旧异步请求可取消','只按需读取当前单件或有限拼接组，取消永久全版本缓存','Lulu引用改为正式v1只读实例','视角写入URL并可恢复','E13单件检查地面置于Z=0','组合场景锁定下载对应的当前组件，标为当前单件下载'],
 'evidence':['browser/checks.json','browser/download-validation.json','browser/resource-cycles.json','browser/final-delivery.png'],'build':'npm run build passed; web-build-final.log','performance_claim':'仅功能和资源回收复核，不承诺目标设备流畅'}
dump(Q/'browser-validation.json',validation);dump(B/'browser-validation.json',validation)
dump(B/'preservation-check.json',read(Q/'preservation-check.json'))
dump(Q/'visual-review.json',{'date':'2026-10-18','actual_review_method':'工具实际打开参考板、B01及B03图板、768关键局部、当前浏览器截图；非仅保存截图','baseline':['../B01/B01-r03-candidates.jpg','../B01/cabbage-r03-review-board.jpg','../B01/tomato-r03-review-board.jpg','../B01/corn-r03-review-board.jpg','../../../../../art-concepts/04-environment.png'],'assets':observations,'user_art':'pending','native_web_difference':'相同色彩区块和轮廓，网页方向光的阴影/对比更强，未改曝光或增灯掩盖缺陷。'})
rows=[]
for a,n in names.items():
 m=metrics[a];rows.append(f"| {n} | {m['triangles']:,} | {m['mesh_nodes']} / {m['materials']} | {m['bytes']/1e6:.3f} MB | 技术通过；初审通过有保留；用户待验收 |")
text='''# B03 r03 收尾复核 · 2026-10-18

保留原有 E01 空田格、E05 水岸直段、E07 水面格、E13 石头组 r03。此次没有重建模型、没有创建 r04，四份制作源及 GLB 保持原始 SHA256。新增本次原生复核与实际网页证据，补齐交接记录。用户美术认可、目标设备性能仍待验收。

[打开实际预览](http://127.0.0.1:5173/b03.html?asset=e05&revision=r03&layout=shore&material=color&water=static&view=quarter)。

| 资产 | 三角面 | 网格 / 材质 | GLB 体积 | 状态 |
|---|---:|---:|---:|---|
'''+ '\n'.join(rows)+'''

## 实际完成的复核

- 原源四份重开，生产分件15/7/1/3；真实GLB重新导入，有限坐标、法线、零面积和外部引用检查完成。除E07有意开放水片外，诊断焊合后的生产网格没有开放边。
- 本次重渲染40张768×768材质/灰模五视图、4张局部和12张r01/r02/r03同条件GLB对照；实看图板和关键原尺寸视图。
- 本次重新保存检查场景，渲染空九格、种植九格、三段直岸/水面、接缝特写/侧剖、官方Lulu农场距离。农场1280×720，约12×8格，45°方位、50°俯角；未逐件统一高度。
- 网页63个状态截图；四件GLB和制作源实际下载均与项目SHA256一致。视角链接恢复成功，静态/网页明暗波纹可切换，控制台无告警/错误。修复切换资源累积，三次农场切回E01都恢复16个渲染几何和1个纹理（包含检查台/阴影），不代表帧率预算验证。
- 保全38个B03历史源/GLB/贴图/清单、B01认可源/GLB及固定设置、官方Lulu源/GLB，哈希均未变化。

## 必须保留的边界

E01 单格宽1.2，内部地面约Z=-0.00226；木轨约0.08宽，相邻格双轨约0.16，交叉处双柱更粗。此样式仍需要用户确认，没有擅自做隐藏边/合并边派生。

E05 沿X以1.2重复，端截面匹配，数值拼接误差小于0.000001。后侧陆地Z=0；岸坡底Z=-0.28，是需要埋入地面/水下的实体，不应整体抬到0。岸石独立；只有直岸，没有岸角或封闭池塘。

E07 为Z=-0.105、零厚度的水平水片，48条外边为有意开放边界。512×512贴图已嵌入，材质不透明；当前网格水纹及重复感保留。网页波纹仅改变明暗，不位移几何；未交付水下鱼可视、流体、透明和波浪几何。

E13 三颗独立石头，最低点约0.000126，固定Z=0地面下接触正常。颜色柔和；网页对比比原生略强，沿用B01既有检查灯光。

未新增模型优化版本，未测试目标设备或帧率。所有“通过”是实际执行范围内的技术/视觉初审，不能替代用户美术采用。B14主屋由并行任务单独交付。

## 证据入口

- `acceptance.json`、`metrics.json`、`review-settings.json`、`source-reopen.json`、`glb-normal-texture-audit.json`
- `e01-native-board.jpg`、`e05-native-board.jpg`、`e07-native-board.jpg`、`e13-native-board.jpg`、`versions-controlled-board.jpg`
- `empty-tiles-r03-1280x720.png`、`tiles-r03-1280x720.png`、`shore-r03-1280x720.png`、`shore-r03-section.png`、`shore-r03-seam-detail.png`、`farm-r03-1280x720.png`
- `browser-validation.json`、`browser/checks.json`、`browser/download-validation.json`、`browser/resource-cycles.json`、`browser/final-delivery.png`
- `preservation-before.json`、`preservation-check.json`、`native-recheck.log`、`web-build-final.log`

原模型仍在 `assets-source/farm-assets/B03/*-r03.blend` 和 `public/models/farm-assets/B03/*-r03.glb`。本目录下 `check-*-r03.blend` 仅为检查组合场景，不能替代生产源。旧图与旧日志留在上级目录，本次证据独立保存。
'''
(Q/'README.md').write_text(text)
(B/'README.md').write_text('# B03 平地与水岸\n\n当前四件 r03 收尾复核已完成，技术及视觉初审通过（有保留项），等待用户美术验收；未测试目标设备。原源和 GLB 未修改。\n\n完整交接：[2026-10-18 收尾记录](closeout-20261018/README.md)。当前逐项状态见本目录 `acceptance.json`，网页复核见 `browser-validation.json`，保全核对见 `preservation-check.json`。\n\n[打开实际三段直岸预览](http://127.0.0.1:5173/b03.html?asset=e05&revision=r03&layout=shore&material=color&water=static&view=quarter)。\n')
print('B03 CLOSEOUT PACKAGE READY')
