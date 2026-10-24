"""Package actual B04 evidence, retaining visual FAIL states and immutable models."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'review/farm-assets/B04';OUT=ROOT/'public/models/farm-assets/B04';REV='r02'
metrics=json.loads((QA/'metrics.json').read_text());assets=metrics['assets'];crops=['bokchoy','lettuce','cauliflower']
names={'bokchoy':'小白菜','lettuce':'生菜','cauliflower':'花椰菜'}
issues={'bokchoy':'浅色叶柄已变饱满，但绿叶仍有尖角、削切直边；俯视像T形横板，上展叶身不够圆润完整。','lettuce':'三层同心碗、中央规则孔和等高环壁明显；卷曲主要集中叶缘，叶身仍像整齐厚板，未形成疏松错落卷叶簇。','cauliflower':'花球仍为整体白块上的锥瘤和尖峰，缺少圆钝花冠簇、副簇及簇间浅沟。'}
directions={'bokchoy':'保留饱满实体叶柄，单独重设圆钝匙形叶身轮廓和弯曲；修正叶尖宽度函数，避免smoothstep收敛成尖刺。','lettuce':'打破等角、等高同心排布；逐片设计不等长宽与高低、扭转和叶身折卷，以错落内叶填补规则中央孔。','cauliflower':'用8–10个不等大的宽圆瓣母簇，每簇3–5个扁圆钝顶副簇，再局部融合成连续面，保留浅沟；不再用高斯径向位移制造尖峰。'}
for c,v in assets.items():
    assert v['source_reopened'] and v['native_review_completed']
    for key in ['zero_area_faces','duplicate_index_faces','nonfinite_vertices','invalid_face_normals','welded_boundary_edges','welded_nonmanifold_edges','exported_cameras','exported_lights']:assert v[key]==0,(c,key)
    assert not v['negative_transform_objects'] and not v['negative_signed_volume_meshes'] and not v['external_uris']
    assert hashlib.sha256((ROOT/v['file']).read_bytes()).hexdigest()==v['sha256']
    for m in ['material','clay']:
        for view in ['front','side','back','quarter','top']:assert (QA/f'{c}-{REV}-{m}-{view}.png').exists()

def check(criterion,result,evidence,observation):
    for p in evidence:assert (ROOT/p).exists(),p
    return {'criterion':criterion,'result':result,'evidence':evidence,'observation':observation}
q='review/farm-assets/B04/'
records=[]
for c in crops:
    v=assets[c]
    records.append({'asset':c,'name':names[c],'stage':'mature','revision':REV,'source':v['source'],'glb':v['file'],'technical_status':'通过','visual_review_status':'需返修','user_art_status':'待用户验收','checks':[
        check('专属成熟态结构达到参考与B01认可基准','不通过',[q+f'{c}-r02-review-board.jpg',q+f'{c}-r02-detail.png',q+f'{c}-controlled-comparison.jpg'],issues[c]),
        check('源文件重新打开、编辑分件与实际GLB回读','通过',[q+'metrics.json',q+'review-r02.log'],f"源已重新打开并实际渲染；{len(v['editable_components'])}个可编辑分件，GLB回读成功。"),
        check('几何数值、法线、材质与外部引用','通过',[q+'metrics.json'],f"{v['triangles']}三角面，{v['materials']}材质，{v['bytes']}字节；零面积面/重复索引面/非法坐标/无效法线为0；临时焊接诊断后边界及非流形边为0，无缺失外链。数值有效不代表造型合格。"),
        check('原生与真实GLB/网页保持相应几何','通过',[q+f'{c}-r02-material-quarter.png',q+f'{c}-r02-glb-quarter.png',q+f'browser-{c}-r02.jpg'],"真实导出保留结构与色彩分区，原生中的造型缺陷在GLB与网页中仍存在。网页更暗、阴影更硬，不宣称逐像素一致。"),
        check('1.2间距3×3布局与固定农场距离','通过（仅布局检查）',[q+f'{c}-r02-field.png',q+f'browser-{c}-field-r02.jpg',q+'browser-farm-r02.jpg'],"九株保持原始尺度、没有互占相邻中心；12×8固定镜头与只读Lulu比例已实际查看。这些是诊断实例，不是扩展生产批次，也不证明美术达标。"),
        check('灰模无标签辨识与物种结构达标','不通过',[q+'B04-r02-types-clay.png',q+'browser-types-clay-r02.jpg'],"三种大轮廓有差异，但差异本身不能证明物种专属结构达标；须解决上述叶形、环壁和花球问题。"),
        check('目标设备性能','未验证',[q+'metrics.json'],"未测手机或其他目标设备；高面数/细分不作为质量或性能通过依据。")],
        'next_design_direction':directions[c]})

record={'batch':'B04','revision':REV,'date':'2026-10-18','timezone':'Asia/Shanghai','status':'需返修','technical_status':'通过','visual_review_status':'三项均需返修','user_art_status':'待用户验收','baseline':'B01 r03 用户认可美术基准；B02 r04 本轮已明确获用户认可，模型保持只读','scope':'Only three mature plants. No sprouts/growing stages; no other batch production.','assets':records,'rounds':[{'revision':'r01','status':'历史失败候选','bokchoy':'尖底花苞感，浅色叶柄不足饱满','lettuce':'初图可辨，但完整复查不支持通过','cauliflower':'平滑白蛋，缺花簇层次'},{'revision':'r02','status':'需返修','changes':['小白菜改为闭合实体匙柄到叶身连续截面；白柄改善但绿叶轮廓失真','花椰菜加强主副起伏，仍成锥瘤而非圆钝花簇','生菜几何沿用r01，仅统一版本重导；完整五视图揭露同心套碗问题']}],
    'stop_reason':{'source':'用户指定执行计划第4节','quote':'连续两轮仍存在同一核心问题时，提交失败证据和可选修改方向，状态保持需返修','application':'花椰菜两轮仍未形成圆钝花簇；小白菜返修后出现新的叶身轮廓缺陷；生菜完整检查亦不达标。停止当前建模做法并提交全部失败证据，不扩大其他批次，不降低标准。'},
    'actual_visual_evidence_reviewed':['Three r02 material/clay five-view boards (30 original images) and 3 details','v1/r01/r02 same-camera actual GLB comparisons','Three complete-frame native 3×3 diagnostics and unlabelled types clay','Actual web single, field, farm, grey-back/top, wire and old-version controls'],
    'remaining_render_difference':'网页沿用B01设置，比Cycles偏暗、阴影较硬；模型问题没有通过换光或曝光掩盖。',
    'next_step':'等待用户反馈与返修方向；不自动执行下一批。'}
(QA/'acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
manifest=json.loads((OUT/'manifest.json').read_text());manifest['status']='需返修';manifest['art_accepted']=False
for a in manifest['crops']:
    c=a['id'];v=assets[c];a.update({'name':names[c],'status':'需返修','visual_review_status':'需返修','user_art_status':'待用户验收','triangles':v['triangles'],'bytes':v['bytes'],'sha256':v['sha256'],'source_sha256':v['source_sha256'],'issue':issues[c]})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))

rows='\n'.join(f"| {names[c]} | {assets[c]['triangles']:,} | {assets[c]['bytes']:,} | [源](../../../assets-source/farm-assets/B04/{c}-mature-r02.blend) · [GLB](../../../public/models/farm-assets/B04/{c}-mature-r02.glb) | 需返修 |" for c in crops)
text=f'''# B04 r02 执行与失败证据包

**技术检查通过；三项视觉初审均需返修，未获用户美术认可。** 本批未达到美术验收线，不能称三个成熟态已完成定稿。B02 r04 已按本轮明确反馈「r04通过」记录为用户通过；其模型未变。

[实际网页：三种并排](http://127.0.0.1:5173/b04.html?crop=lettuce&revision=r02&layout=types&material=color&view=quarter) · [固定农场镜头](http://127.0.0.1:5173/b04.html?crop=lettuce&revision=r02&layout=farm&material=color&view=quarter) · [逐项验收](acceptance.json)

## 交付与状态

| 资产 | 三角面 | GLB 字节 | 当前文件 | 美术状态 |
|---|---:|---:|---|---|
{rows}

仅成熟态。r01/r02源文件、真实GLB和历史初版v1选择均保留；没有扩展幼苗、成长态或其他批次。根部地面中心原点、1.2单位格、Lulu高1.2，不逐株归一化。

## 具体失败点与后续方向

1. **小白菜**：{issues['bokchoy']} 后续方向：{directions['bokchoy']}
2. **生菜**：{issues['lettuce']} 后续方向：{directions['lettuce']}
3. **花椰菜**：{issues['cauliflower']} 后续方向：{directions['cauliflower']}

按计划第4节的两轮失败规则，停止当前做法，提交证据与方向，状态保持需返修。没有把文件生成、面数增加、能区分大轮廓或网页加载成功当成美术通过。生菜r02沿用r01几何，完整五视图推翻了首轮3/4初图的暂定判断。

## 已实际查看的证据

- [小白菜五视图板](bokchoy-r02-review-board.jpg) · [生菜五视图板](lettuce-r02-review-board.jpg) · [花椰菜五视图板](cauliflower-r02-review-board.jpg)。材质与灰模各五视图，原始单张均768×768。
- [小白菜v1/r01/r02固定对照](bokchoy-controlled-comparison.jpg) · [生菜对照](lettuce-controlled-comparison.jpg) · [花椰菜对照](cauliflower-controlled-comparison.jpg)。共用相机、灯光、曝光和世界尺度。
- [三种灰模无标签诊断](B04-r02-types-clay.png) · [实际网页三种](browser-types-r02.jpg) · [实际网页生菜俯视](browser-lettuce-top-r02.jpg)。
- [小白菜3×3](bokchoy-r02-field.png) · [生菜3×3](lettuce-r02-field.png) · [花椰菜3×3](cauliflower-r02-field.png) · [固定网页农场距离](browser-farm-r02.jpg)。均为检查实例，非生产扩展。
- [测量与源重开](metrics.json) · [固定条件](review-settings.json) · [网页记录](browser-validation.json) · [基准原件哈希保护](preservation-check.json) · [两轮候选总图](B04-r02-candidates.jpg)。

三份当前GLB实际回读，零面积面、重复索引面、非法顶点、无效法线均为0；无外部纹理依赖，无QA相机灯光地台混入生产GLB。源文件重新打开，编辑分件及修改器保留。`npm run build`通过；Three共用vendor体积提示保留。布局未互占相邻中心，但不代表物种结构或美术合格。

原生横向诊断图曾有取景裁切，现已按真实宽高比补正并重新渲染；没有改模型、灯光或曝光。网页比原生偏暗且阴影硬，这一真实渲染差异保留。目标设备性能未测试。

脚本：`tools/build_b04.py`、`tools/b04_common.py`、`tools/b04_cauliflower.py`、`tools/review_b04.py`、`tools/package_b04_review.py`。不直接运行B01生成器，不覆盖已认可文件。后续等待用户反馈，不自动开始下一批。
'''
(QA/'README.md').write_text(text)
print('B04 packaged: technical pass, art FAIL for all 3; user approval pending.')
