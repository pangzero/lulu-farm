from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018'
read=lambda p:json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
rows=read(O/'mapping.json');tech=read(O/'technical-validation.json');assert all(not r['missing'] for r in tech),'Finish evidence before acceptance'
assert read(O/'preservation-check.json')['protected_unchanged']
items=[];metrics=read(O/'metrics.json');manifest_path=R/'public/models/crop-two-stage/manifest.json';manifest=read(manifest_path)
observations={
'cabbage':'宽圆叶、中央小幼叶、叶柄与根部连接保持；r02恢复连续背脉。株型仍偏扇形、侧背浅，叶柄细灰绿痕保留，未重建包心结构。',
'bokchoy':'宽厚卵叶与奶绿叶柄保留，根部连续；r02背面主脉恢复。细小灰绿柄痕、较浅扇形深度仍属保留项。',
'cauliflower':'偏冷绿的宽圆叶代表苗，未携带成熟花球；r02背脉连续。不是专属幼苗叶序重建，柄部细痕与扇形结构保留。',
'lettuce':'更低、更展开的嫩绿宽叶代表苗，r02保持背面脉线及叶面厚度。没有新增卷缘真叶，不声称精确复现原生菜概念；柄部细痕保留。',
'tomato':'较高窄的双子叶代表苗，保留低子叶、上拱叶与中央小叶；连接和叶厚完整。没有重建番茄后续羽状复叶，部分浅亮主脉仍明显。',
'cucumber':'双子叶早苗，较短株与上拱宽叶，叶柄/根部完整；表面细碎反光收敛。未加入花、果或卷须来强行区别。',
'pumpkin':'较矮宽的双子叶代表苗，上叶对展与低子叶完整。未做南瓜掌裂真叶重建，远景只代表早期阶段与叶形族群。',
'sunflower':'较高直立的双子叶代表苗，中央幼叶和前后叶体积保留；浅亮主脉仍可见，不称完全去脉。',
'rose':'共享双子叶早苗，稍窄、轻扭转；无花苞/花朵。未复现玫瑰复叶，成熟玫瑰已有串色问题仍独立待返修。',
'strawberry':'较低、更展开的双子叶代表苗，叶厚和根冠连续；不是三出真叶重建，不携带白花或红果。',
'watermelon':'低宽双子叶代表苗，完整幼叶与根部；未重建掌裂真叶，不携带条纹瓜果，映射关系明确标注。',
'corn':'较高且相对宽的窄带叶苗，叶片弧面、空隙及基部连接保持，无玉米棒；原件前方短叶鞘较平口与细尖叶端保留。',
'wheat':'比玉米低、窄的带叶苗，保留纵向叶片和基部，无穗；只做共享草叶苗派生，不宣称新增分蘖细节。',
'tulip':'基生披针叶片围合，中央叶与前后叶保持厚度、间隙；无盛开花或花茎。中叶细痕/小斑点保留，不声称表面完全无瑕。'}
for row in rows:
 s=row['id'];v=row['current_version'];m=next(x for x in metrics if x['crop']==s);c=next(x for x in manifest['crops'] if x['id']==s)
 c['seedling'][v]['reviewStatus']='共享代表苗：技术与视觉初审通过（有保留项）／用户未认可／设备未测'
 if row['family']=='broad':c['seedling']['meshy-toon-r01']['reviewStatus']='历史失败：减面后背面叶脉退化；当前采用 r02'
 item={'crop':s,'name':row['name'],'code':row['code'],'batch':row['batch'],'stage':'seedling','version':v,'family':row['family'],'family_label':row['family_label'],'mapping_note':row['mapping_note'],'source':m['source'],'glb':m['glb'],'source_kind':'User Meshy imported derivative;4shared prototypes,14mapped microedited variants','technical':'passed','visual_initial':'passed_as_shared_representative_with_recorded_limits','botanical_species_reconstruction':'not_claimed','user_art':'pending','target_device':'not_tested','resource_optimization':'retain original geometry after UV/vein regression; no mesh budget pass' if row['family']=='broad' else 'relative reduction reviewed; not device/game budget certification','observation':observations[s],'evidence_dir':str((O/s).relative_to(R)),'review_checks':[{'criterion':'Source reopen and exportedGLBroundtrip/topology/textures/worldscale','status':'passed','evidence':[f'{s}/{v}/source-reopen.json',f'{s}/{v}/metrics.json']},{'criterion':'Material/clay5views and matchedoriginalcomparison','status':'passed_with_limits','evidence':[f'{s}/material-comparison.jpg',f'{s}/clay-comparison.jpg']},{'criterion':'3x3/farm/Lulu and maturepair scale','status':'passed_stage_and_family_readability','evidence':[f'{s}/{v}/planting-3x3-lulu.png',f'{s}/{v}/farm-distance.png',f'{s}/stage-pair.png']}]}
 items.append(item);save(O/s/v/'acceptance.json',item)
manifest['note']='14种成熟作物均已映射幼苗：4份用户Meshy原型→14个微改卡通派生。宽叶四种采用保留原网格的r02，其余十种r01；共享代表关系明确标注。待用户验收，设备未测；C12/C16仍暂缓。'
save(manifest_path,manifest);save(O/'acceptance.json',{'scope':'4 user Meshy inputs ->14shared-family microedited cartoon seedlings','current_count':14,'version_counts':{'meshy-toon-r01':10,'meshy-toon-r02':4},'user_art':'pending','device':'not_tested','items':items,'rejected_history':{'crops':['cabbage','bokchoy','cauliflower','lettuce'],'version':'meshy-toon-r01','reason':'35kcollapse introduced wavy/discontinuous paintedbackveins; r02retainsoriginalgeometry'}})
settings=read(R/'review/farm-assets/B01/review-settings.json');settings['revision']='seedling-meshy-mapping-20261018';settings['cameras']={x['id']:read(O/x['id']/'review-settings.json') for x in rows};settings['seedling_heights']={x['id']:x['height'] for x in rows};settings['lulu']['file']='public/models/lulu-official-v1.glb';settings['notes']='Original/candidate same per-crop camera. Native Cycles and web three.js use separate fixed pipelines. Seedling scale baked into geometry; root worldorigin groundedcenter; soil/Lulu not exported. Nineplants on1.2cells; farm12x8 at1280x720,DPR1,no full-field/deviceFPS claim.';save(O/'review-settings.json',settings)
prov=[]
for r in rows:
 m=next(x for x in metrics if x['crop']==r['id']);prov.append({'crop':r['id'],'original_filename':r['input']['original_filename'],'original_download':r['input']['original_download'],'original_sha256':r['input']['sha256'],'project_original':r['input']['file'],'family_import_source':r['input']['source'],'family_import_source_sha256':r['input']['source_sha256'],'current_source':m['source'],'current_source_sha256':m['source_sha256'],'current_glb':m['glb'],'current_glb_sha256':m['sha256'],'microedit':{k:r[k] for k in ['height','width','depth','twist','tint']},'texture_recipe':f"{r['id']}/{r['current_version']}/texture-recipe.json"})
save(O/'provenance.json',prov)
cur=read(O/'browser/checks.json');by={}
for x in cur:
 s=x['canvas']['crop'];v=next(r['current_version'] for r in rows if r['id']==s)
 if x['canvas']['version'] not in ['meshy-original',v]:continue
 from urllib.parse import urlparse,parse_qs
 q=parse_qs(urlparse(x['url']).query);key=(s,x['canvas']['version'],q['material'][0],q['view'][0],q['layout'][0]);by[key]=x
assert len(by)==126;save(O/'browser/current-checks.json',list(by.values()));save(O/'browser-validation.json',{'captured_states':len(cur),'current_cases':len(by),'cases':'browser/current-checks.json','all_history':'browser/checks.json','visual':'browser/visual-review.json','original_downloads':'browser/download-validation.json','http_links':'browser/http-links.json','canvas':[1280,720],'dpr':1,'device_performance':'not_tested','final_console':'browser/console-final.json','build':'build.log','redirect_check':'browser/entry-redirect.json'})
lines=['#4个Meshy幼苗原型→14种作物映射（微改卡通候选）',
       '',
       '当前14种成熟作物均有对应幼苗。采用用户4份Meshy原型，保存14个有株高/展开度/前后姿态/色彩微调的派生；明确共享代表苗关系，不声称14种独立原生建模或精确复现各自真叶。',
       '',
       '[打开实际预览](http://127.0.0.1:5173/crops-two-stage.html?crop=cabbage&stage=seedling&version=meshy-toon-r02&material=color&view=quarter&layout=single) · [映射JSON](mapping.json) · [逐项验收](acceptance.json) · [指标](metrics.json) · [来源SHA](provenance.json) · [两阶段状态](status-14x2.md)',
       '',
       '##映射与当前版本',
       '',
       '|原型|对应作物|微改方向|',
       '|---|---|---|',
       '|宽圆叶菜苗|卷心菜、小白菜、花椰菜、生菜|0.16–0.20高，轻调展开/前后错位/色温；r02保留原网格|',
       '|双子叶早苗|番茄、黄瓜、南瓜、向日葵、粉玫瑰、草莓、西瓜|0.16–0.23高，番茄较高窄、草莓/瓜类较低宽，轻调姿态|',
       '|窄带叶苗|玉米、小麦|0.30/0.22高，玉米相对宽、小麦窄，不加穗|',
       '|基生披针叶苗|橙色郁金香|0.20高，保留杯状基生叶与前后间隙，不加花|',
       '',
       '![同尺度两阶段](stage-pair-board.jpg)',
       '',
       '##实际制作和检查',
       '',
       '原始GLB字节、原名、SHA256和四份独立Blender导入源保留。导入网格仍为Meshy合并网格，微改通过连续空间形变和独立贴图完成，保留源修改器；没有使用旧程序幼苗充数。卡通处理柔化高频亮脉、正常保留主脉与叶色层次，降低法线与反光，纹理1024²。',
       '',
       '初版14项尝试约3.5万面；完整768背视发现宽叶四项脉线断续，已退回r01。四项r02取消减面、保留约24.3万面原几何，复查背脉连续恢复。其余十项r01约3.5万面。该结果不是最终设备预算认证；宽叶网格优化尚未通过。',
       '',
       '技术：当前14份源均真实回开，GLB实际重新导入，有限坐标/法线、无零面积面、焊接位置后边界与非流形均0，内嵌贴图可解码，无导出相机/土格/Lulu。指标逐件记录。',
       '',
       '原件/候选五视图材质+灰模各768²、茎叶连接局部、3×3种植、1280×720农场远景和只读Lulu、14张共享世界尺度的幼苗/成熟配对均生成并实际复核。全场固定1.2格，幼苗0.16–0.30高，未逐株归一到同高。远景只读出幼苗阶段/叶族，不能据此宣称14种无标签逐种辨识。',
       '',
       '实际浏览器原件/当前候选、五角度、灰模、3×3与农场等当前126例检查。r02复检增加36条历史记录，总162。来源族型、微改说明、当前GLB、当前Blender源和对应原件链接均明确。32个唯一当前模型/源链接HTTP200并文件大小匹配；当前GLB和源已实际下载并验证SHA。旧成熟入口的幼苗选择跳到该检查页。',
       '',
       '85份受保护成熟模型/源/Lulu文件及成熟清单保持不变；四份下载与项目原件哈希相同。未执行B03、B14–B22，C12/C16仍暂缓。',
       '',
       '##保留项与验收',
       '',
       '技术与共享代表苗视觉初审通过，用户美术待验收，设备未测。宽圆叶苗仍较扇形/侧背浅，白绿叶柄有细灰绿线痕；部分浅亮主脉仍明显。玉米短叶鞘口、郁金香中叶细痕属保留项。番茄/玫瑰/草莓没有新增复叶，西瓜没有掌裂真叶；生菜未新增卷缘幼叶。这些由共享早期代表苗路线覆盖，不能冒充原14张概念的精确建模。成熟玫瑰的既有串色仍独立需返修。',
       '',
       '|作物|版本|高|三角面|GLB MB|证据与具体观察|',
       '|---|---|---:|---:|---:|---|']
for r in rows:
 m=next(x for x in metrics if x['crop']==r['id']);s=r['id'];lines.append(f"|{r['name']}|{r['current_version']}|{m['size'][2]:.2f}|{m['triangles']:,}|{m['bytes']/1e6:.2f}|[五视图]({s}/material-comparison.jpg) · [灰模]({s}/clay-comparison.jpg) · [阶段配对]({s}/stage-pair.png)；{observations[s]}|")
lines+=['', '##文件位置','', '- 原型原件：`public/models/seedling-meshy/originals/`；4份导入源：`assets-source/seedling-meshy/{family}/meshy-r01/`。','- 14份当前源/GLB：`assets-source/farm-assets/B08|B09/meshy-toon-r01|r02/` 和 `public/models/farm-assets/` 对应目录。','- 本目录每种 `original/`、`meshy-toon-r01/`、宽叶新增 `meshy-toon-r02/` 保留全部检查。','- 宽叶r01失败证据、首次stage-pair-r01、旧原生幼苗均保留。','- B08/B09批次索引见 `review/farm-assets/B08|B09/meshy-mapping-20261018/`。']
(O/'README.md').write_text('\n'.join(lines).replace('#4个','# 4个').replace('##映射','## 映射').replace('##实际','## 实际').replace('##保留','## 保留').replace('##文件','## 文件')+'\n')
status=['#14种×2阶段当前状态','','幼苗按本次4原型共享映射授权交付；成熟状态沿用前次，未修改成熟文件。用户美术均待验收，目标设备均未测试。','','|作物|幼苗版本/技术/视觉|成熟版本/技术/视觉|资源状态|用户/设备|','|---|---|---|---|---|']
for r in rows:
 s=r['id'];maturetoon='toon-r03' if s in ['tomato','rose'] else 'toon-r02' if s in ['cabbage','corn'] else 'toon-r01';game='game-r02' if s in ['cabbage','tomato','corn','rose'] else 'game-r01';mv='需返修：串色' if s=='rose' else '有保留，沿用前次' if s in ['cabbage','tomato','corn'] else '初审通过，有保留';res='幼苗保留原网格，减面待重做' if r['family']=='broad' else '幼苗相对减量复核通过，预算未定';status.append(f"|{r['code']} {r['name']}|{r['current_version']}；技术通过/共享代表苗初审通过|{maturetoon}/{game}；技术通过/{mv}|{res}；成熟沿用前次|待验收/未测|")
status+=['','C12西葫芦和C16葱两个阶段继续暂缓。历史失败原生幼苗与宽叶meshy-toon-r01不计当前候选。']
(O/'status-14x2.md').write_text('\n'.join(status)+'\n')
for batch in ['B08','B09']:
 d=R/'review/farm-assets'/batch/'meshy-mapping-20261018';d.mkdir(parents=True,exist_ok=True);save(d/'acceptance.json',[x for x in items if x['batch']==batch]);save(d/'metrics.json',[x for x in metrics if x['batch']==batch]);save(d/'review-settings.json',settings);(d/'README.md').write_text(f'# {batch} Meshy共享幼苗映射\n\n[完整报告](../../../seedling-meshy-mapping-20261018/README.md) · [本批验收](acceptance.json)\n\n14种范围内本批候选，共享代表苗，用户美术待验收、设备未测；宽叶r01退回，采用r02。\n')
print('Finalized14mapped seedlings,18revisions retained')
