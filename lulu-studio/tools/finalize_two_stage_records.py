from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/crop-two-stage-20261018'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=read(R/'acceptance.json');settings=read(R/'review-settings.json');catalog=read(ROOT/'public/models/crops-meshy/manifest.json')['crops']
provenance=[]
for c in catalog:
 if not c.get('file'):continue
 concept=ROOT.parent/f'art-concepts/seedling-concepts-20261018/{"B08" if int(c["code"][1:])<=8 else "B09"}/{c["code"]}-{c["id"]}-seedling.png'
 source=ROOT/c['source'];provenance.append({'id':c['id'],'original_name':c['original_name'],'original_glb':c['file'],'original_sha256':c['sha256'],'import_source':c['source'],'import_source_sha256':sha(source),'seedling_concept':str(concept),'concept_sha256':sha(concept),'mature_edits':'only three first-gate species; original never overwritten' if c['id'] in ['cabbage','tomato','corn'] else 'none in this task'})
write(R/'provenance.json',provenance)
for crop in ['cabbage','tomato','corn']:
 for rev in ['game-r01','game-r02']:
  d=R/crop/'mature'/rev;m=read(d/'metrics.json');record={'crop':crop,'stage':'mature','version':rev,'technical':'不通过：减面导致贴图接缝几何裂开' if rev=='game-r01' else '通过：回读、零面积、焊接后边界与非流形检查','visual':'未采用；技术缺陷已足以退回' if rev=='game-r01' else '同条件材质／灰模五视图、种植及网页初审通过；细小叶脉变软，主要轮廓和间隙保留','user_art':'未验收','optimization':'失败保留' if rev=='game-r01' else '初步资源候选，未定最终设备预算','device_test':'未测试','metrics':str((d/'metrics.json').relative_to(ROOT)),'parent_source':m['parent_source'],'parent_sha256':m['parent_sha256']};write(d/'acceptance.json',record);write(d/'review-settings.json',settings)
checks=read(R/'browser/checks.json');links=read(R/'browser/download-links.json')
browser={'page':'http://127.0.0.1:5173/crops-two-stage.html','existing_5173_service_reused':True,'new_duplicate_server_started':False,'build':'passed, see build-final.log','actual_browser_records':len(checks),'all_recorded_downloads_match_displayed_glb':all(i['download']==i['canvas']['file'] for i in checks),'head_links_checked':len(links),'all_head_lengths_match':all(i['http_status']==200 and i['byte_length_match'] for i in links),'actual_download':'browser/actual-download.json (corn seedling GLB SHA matched)','unmade_seedling_test':'lettuce: no model, download/source hidden, metrics cleared','rapid_version_switch':'cabbage r01 -> r02 -> r03; final r03 loaded','errors_in_final_browser_console':[],'final_evidence_suffix':'baseline, with original B01 shadow settings; earlier captures retained as intermediate evidence','camera_and_material_switches':'front, side, back, quarter, top; color and clay; original/toon/game versions','planting':'all six current stages; 3×3 and 12×8 field, 1280×720 DPR1; optional read-only Lulu','performance':'Measured geometry/resources only; no timed device FPS certification','records':'browser/checks.json'}
write(R/'browser-validation.json',browser)
viewed=[]
for crop in ['cabbage','tomato','corn']:
 viewed.extend([f'{crop}/seedling/r02/five-view-board.jpg',f'{crop}/seedling/r03/five-view-board.jpg',f'{crop}/mature/original/five-view-board.jpg',f'{crop}/mature/r02/five-view-board.jpg',f'{crop}/mature/game-r02/five-view-board.jpg',f'{crop}/detail-planting-board.jpg',f'{crop}/pair-material-quarter.png'])
viewed+=['tomato/mature/r03/five-view-board.jpg','mature-ab.jpg','browser-ab.jpg','browser-planting.jpg','optimization-ab.jpg','final-browser-ab.jpg','game-planting.jpg','browser/cabbage-seedling-final.png']
write(R/'visual-review.json',{'actually_opened_boards_and_images':viewed,'method':'工具实际打开图板并查看其中五视图；另查看局部、配对、种植和实际网页截图。单视图源PNG均768×768，农场PNG1280×720。','seedling_conclusion':'失败；第二轮返修仍有同一核心造型问题，不扩大复制','mature_conclusion':'三种材质候选保留主轮廓、叶片间隙与花果连接；番茄r03修正r02过平果实。叶脉色线仍较强，整体两阶段连续性未通过。','optimization_conclusion':'game-r02同条件对照保留主要结构；game-r01因接缝拓扑异常弃用','user_art_approval':False})

table=['| 作物 | 幼苗：技术／视觉 | 成熟派生：技术／视觉 | 用户美术 | 优化 | 设备测试 |','|---|---|---|---|---|---|']
for c in catalog:
 if not c.get('file'):continue
 built=c['id'] in ['cabbage','tomato','corn'];table.append(f'| {c["code"]} {c["name"]} | '+('r03：需返修／未通过' if built else '未完成／未检查')+' | '+(('toon-r03' if c['id']=='tomato' else 'toon-r02')+'：通过／有保留' if built else '未完成／未检查')+' | 未验收 | '+('成熟 game-r02 初步复核通过；幼苗未做' if built else '未执行')+' | 未测试 |')
(R/'status-14x2.md').write_text('# 14种 × 两阶段实际状态\n\n本次没有完成28项。已制作首组三种的6个阶段候选；幼苗关卡失败，其余22项未展开。成熟原始Meshy的已回传状态不计本次卡通化完成。\n\n'+'\n'.join(table)+'\n\n“有保留”：材质哑光方向成立，主要结构保持；叶脉亮线仍强，与未通过的幼苗尚未形成一致配对风格。资源复核只说明相对高模的画面与结构保留，不代表设备性能或用户认可。\n')
summary='''# 作物两阶段统一制作 · 首组质量关卡结果

**整体未完成，等待用户反馈。**已实际制作卷心菜、番茄、玉米三组“幼苗＋成熟卡通候选”；幼苗 r02、r03 两轮返修后仍有同一核心造型问题，按本次用户第5节及执行计划第4节停止该失败方法。其余十一组（22个阶段项）没有展开，不用旧模型或概念图充数。

[实际预览](http://127.0.0.1:5173/crops-two-stage.html?crop=cabbage&stage=seedling&version=r03&material=color&view=quarter&layout=single) · [14×2状态表](status-14x2.md) · [逐项验收](acceptance.json) · [全部测量](metrics.json) · [检查设置](review-settings.json) · [来源及哈希](provenance.json) · [网页记录](browser-validation.json)

## 已保留的真实候选

幼苗三种均为 B08/native-r03 的独立原生 Blender 制作源与 GLB。r01 是初版，r02 是第一次定向返修，r03 是第二次。它们不是旧研究小样改名，也不是正式通过成品。宽叶正面展开、前后体积和玉米中心收尖有改善，但叶面仍有规则勺状鼓包、叶柄硬接和侧面竖壁。GLB焊接后的叶缘边界分别20／4／18条；番茄还有1个极小退化面，技术与视觉均未过关。

成熟版来自用户 Meshy 原件，原轮廓、UV、花果连接均保留。卷心菜、玉米为 B01/toon-r02；番茄为 B01/toon-r03，单独调整红色果实粗糙度，避免统一哑光后变平。三份源如实属于 Meshy 导入后的派生编辑工程，仍为原合并网格，不宣称手工分件源。高模版只改独立颜色贴图和PBR，未推倒重建。

三种另存 B01/game-r02 资源候选：按物种分别减面、贴图上限2K；保留高模和源修改器。game-r01因UV接缝分裂导致几何裂边而弃用，game-r02先焊接重合几何再减面，回读无零面积、焊接后边界或非流形异常。五视图、灰模、种植和实际网页对照没有发现主要轮廓、间隙、果梗与穗粒层次损坏，细小叶脉略软。此为初步资源复核，未定最终设备预算，未测手机或其他目标设备。

## 当前资源

| 作物 | 幼苗 r03 三角面／MB | 成熟高模三角面／MB | game-r02 三角面／MB |
|---|---:|---:|---:|
'''
for crop in ['cabbage','tomato','corn']:
 c=next(x for x in catalog if x['id']==crop);parts=[]
 for stage,rev in [('seedling','r03'),('mature','r03' if crop=='tomato' else 'r02'),('mature','game-r02')]:
  m=read(R/crop/stage/rev/'metrics.json');parts.append(f'{m["triangles"]:,}／{m["bytes"]/1e6:.2f}')
 summary+='| '+c['name']+' | '+' | '.join(parts)+' |\n'
summary+='''
## 查看与复查

- [幼苗三轮同相机对照](seedling-rounds.jpg)：展示失败路线，不能当成验收通过。
- [成熟原版与材质候选](mature-ab.jpg)：此板番茄为r02历史对照，当前r03见对应五视图和网页。
- [成熟资源优化前后](optimization-ab.jpg)：左为当前高模，中为弃用game-r01，右为game-r02。
- [最终网页三版本对照](final-browser-ab.jpg)与[优化后种植](game-planting.jpg)。
- 各物种目录包含材质／灰模正、侧、背、3/4、俯视原图、关键局部、两阶段共同比例、3×3种植、1280×720农场距离和回读报告。单视图768×768；农场1.2田格、DPR1、45°方位／50°俯角。Lulu只读缩放实例高1.2。
- `browser/*-baseline.png` 是最终B01网页阴影设置的证据。早期无阴影截图及半格错位图只作中间记录，最终对照不混用它们。各新旧版本共用相机、灯光、曝光和显示比例。
- 复用了原5173服务；完成构建。真实操作验证版本、视角、材质、种植、Lulu比例、快速切换与未制作项清空；51个下载地址HTTP200且长度相符，实际下载的玉米幼苗GLB与当前显示文件SHA一致。没有同时加载全部高模。
- [保留核对](preservation-check.json)：14份成熟原件与27份已有受保护源／GLB哈希不变。未执行B03、B14–B22，未修改Lulu或动物文件。

## 继续前需要的反馈

建议保留这三份成熟派生与资源候选，幼苗另选逐叶重塑方法：先解决宽叶的非规则曲率、叶柄圆截面到叶面的过渡和根冠融合，再做番茄裂叶与玉米叶鞘。先验证一株宽叶完整五视图，不沿用当前整片参数模板扩量。本次已触发明确的两轮停止规则，等待用户反馈后再恢复该路线；未自动执行其他批次。

## 源文件和GLB索引

'''
for crop in ['cabbage','tomato','corn']:
 summary+=f'### {next(c["name"] for c in catalog if c["id"]==crop)}\n\n'
 for stage,rev in [('seedling','r03'),('mature','r03' if crop=='tomato' else 'r02'),('mature','game-r02')]:
  m=read(R/crop/stage/rev/'metrics.json');summary+=f'- {stage} {m["version"]}：[Blender源]({ROOT/m["source"]}) · [GLB]({ROOT/m["glb"]}) · [验收]({crop}/{stage}/{rev}/acceptance.json)\n'
 summary+='\n'
(R/'README.md').write_text(summary)
print('FINAL RECORDS WRITTEN')
