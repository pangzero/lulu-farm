"""Collect measured evidence and explicit review decisions; never creates models."""
from pathlib import Path
import json,hashlib,struct,io,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/crop-two-stage-20261018'
CAT=json.loads((ROOT/'public/models/crops-meshy/manifest.json').read_text())['crops']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def textures(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:];result=[]
 for item in doc.get('images',[]):
  v=doc['bufferViews'][item['bufferView']];b=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];im=Image.open(io.BytesIO(b));size=im.size;im.verify();result.append({'name':item.get('name'),'size':size,'encoded_bytes':len(b),'decoded':True})
 vertices=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for m in doc.get('meshes',[]) for p in m['primitives'])
 return {'images':result,'exported_vertices':vertices,'cameras_in_glb':len(doc.get('cameras',[]))}

settings=json.loads((ROOT/'review/farm-assets/B01/review-settings.json').read_text())
settings.update({'task':'two-stage-20261018','reference_only':'B01 r03 accepted baseline remains unchanged','seedling_camera':{'target':[0,0,.2],'height':.55},'mature_cameras':'Per crop source-reopen.json; same across original/toon/game','planting':{'cell':1.2,'near_3x3_blender_ortho':6.2,'near_3x3_web_ortho':5.5,'farm_ortho_height':14.1,'farm_canvas':[1280,720],'dpr':1,'farm_azimuth':45,'farm_elevation':50,'field_cells':[12,8],'plants':9,'farm_plant_offset':[.6,.6],'lulu_scale':.6313689262131015},'web_shadow':'B01 PCFSoft, 2048, normalBias .02; final browser screenshots are suffixed baseline','source_coordinates':'Z-up','glb_coordinates':'Y-up','seedling_world_scale':1,'mature_original_instance_scale':.47,'mature_derivative_scale_baked':True})
write(R/'review-settings.json',settings)
allmetrics=[];public=json.loads((ROOT/'public/models/crop-two-stage/manifest.json').read_text())
for c in public['crops']:
 if c['id'] not in ['cabbage','tomato','corn']:c['mature']['original']['height']=None
 for stage in ['seedling','mature']:
  for p in sorted((R/c['id']/stage).glob('*/metrics.json')):
   m=json.loads(p.read_text());m.update(textures(ROOT/m['glb']));m['sha256']=sha(ROOT/m['glb']);m['source_sha256']=sha(ROOT/m['source']);write(p,m);allmetrics.append(m)
   src=ROOT/m['source'];dst=ROOT/m['glb'];dst=dst.parent/'source'/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
   if not dst.exists() or sha(src)!=sha(dst):shutil.copy2(src,dst)
   if p.parent.name=='game-r02':
    c[stage]['game-r02']={'file':'/'+m['glb'].removeprefix('public/'),'source':'/'+str(dst.relative_to(ROOT/'public')),'scale':1,'label':'资源候选 game-r02 · 2K','triangles':m['triangles'],'bytes':m['bytes'],'height':m['size'][2],'reviewStatus':'优化候选／用户未认可／设备未测'}
write(ROOT/'public/models/crop-two-stage/manifest.json',public)
write(R/'metrics.json',allmetrics)

issues={
 'cabbage':'两轮后宽叶仍有规则勺状鼓包、中央新叶像贴上的小片；侧背面的叶柄与根冠过渡不自然，与成熟包叶的塑形和叶脉层次差距明显。',
 'tomato':'两轮后裂叶虽变圆，但仍是同一参数轮廓的重复；真叶与茎的接口呈狭长硬接片，部分叶尖偏硬，叶面起伏与成熟复叶不连续。',
 'corn':'中心新叶由平口改成收尖卷片，但外叶侧面仍像连续竖壁，叶鞘下端呈硬边叠片；缺少成熟株的柔和厚卷与自然过渡。'}
assets=[]
for c in CAT:
 if not c.get('file'):continue
 for stage in ['seedling','mature']:
  built=c['id'] in issues;batch=('B08' if int(c['code'][1:])<=8 else 'B09') if stage=='seedling' else c['batch'];rev='r03' if stage=='seedling' or c['id']=='tomato' else 'r02'
  item={'id':c['id'],'code':c['code'],'name':c['name'],'stage':stage,'batch':batch,'status':'candidate_needs_rework' if built and stage=='seedling' else 'candidate_pending_user' if built else 'not_completed_pair_gate','technical':'需返修' if built and stage=='seedling' else '通过（源／GLB回读、贴图、有限数值及焊接后拓扑）' if built else '未完成／未检查','visual_initial':'未通过' if built and stage=='seedling' else '材质方向基本成立，叶脉与整体配对风格仍有保留' if built else '未完成／未检查','user_art':'未验收','optimization':'未执行（造型未过关）' if stage=='seedling' and built else 'game-r02 初步资源复核通过（同条件画面与回读）；终版设备预算未定；game-r01接缝开裂已弃用' if built else '未执行','device_test':'未测试','formal_completed':False}
  if built:
   p=R/c['id']/stage/rev;m=json.loads((p/'metrics.json').read_text());item.update({'version':m['version'],'source':m['source'],'glb':m['glb'],'metrics':str((p/'metrics.json').relative_to(ROOT)),'evidence':str(p.relative_to(ROOT)),'notes':issues[c['id']] if stage=='seedling' else '保留Meshy主要轮廓、UV与花果连接；高模版只改独立贴图及PBR。卷心菜/玉米toon-r02，番茄toon-r03单独恢复果实柔和高光。'})
   if stage=='seedling':
    topo=json.loads((p/'roundtrip-topology.json').read_text());item['technical_findings']={'welded_boundary_edges':sum(i['welded_boundary_edges'] for i in topo),'nonmanifold_edges':sum(i['nonmanifold_edges'] for i in topo),'zero_area_faces_after_weld':sum(i['zero_area_faces'] for i in topo)}
   else:item['original']={'file':c['file'],'original_name':c['original_name'],'sha256':c['sha256'],'import_source':c['source']}
   write(p/'review-settings.json',settings);write(p/'acceptance.json',item)
  else:item['notes']='首组三种配对质量关卡未通过，依本次执行顺序没有扩展。现有成熟Meshy原件继续保留，不计作本次卡通化完成。'
  assets.append(item)
acceptance={'scope':'14 species × seedling/mature, B08/B09 and B01/B04/B05/B06','overall':'INCOMPLETE — first paired quality gate failed; await user feedback per explicit two-repair rule','native_seedling_candidates':3,'mature_cartoon_candidates':3,'remaining_stage_models_not_made':22,'user_approved_new_assets':0,'seedling_rework_rounds':[{'revision':'r01','role':'initial','finding':'扁平、机械叶缘与直切茎尖'},{'revision':'r02','role':'repair 1','finding':'增厚及弯叶后仍呈正面扇形，侧面薄片，玉米中心平口'},{'revision':'r03','role':'repair 2','finding':'转向/收尖改善但核心模板化塑形与叶柄硬接仍存；导出拓扑异常；停止此方法'}],'failed_route':'当前整片参数曲面、叶柄与叶面同网格的制作/导出方法。不是取消Blender路线或取消剩余授权。','blocked_expansion_reason':'用户明确要求前三组配对技术和视觉初审通过后才扩展；未通过，不能复制到剩余十一组。','assets':assets}
write(R/'acceptance.json',acceptance)
for batch in ['B01','B04','B05','B06','B08','B09']:
 d=ROOT/f'review/farm-assets/{batch}/two-stage-20261018';subset=[i for i in assets if i['batch']==batch];write(d/'acceptance.json',{'batch':batch,'task_acceptance':'review/crop-two-stage-20261018/acceptance.json','assets':subset});write(d/'review-settings.json',settings);write(d/'metrics.json',[m for m in allmetrics if m['batch']==batch]);(d/'README.md').write_text(f'# {batch} · 两阶段任务索引\n\n本次未完成完整14组；状态见 [总记录](../../../crop-two-stage-20261018/README.md)。本目录不覆盖本批旧验收。\n\n'+ '\n'.join(f'- {i["name"]} {i["stage"]}：{i["status"]}' for i in subset)+'\n')
print('PACKAGED',len(assets),'stage states,',len(allmetrics),'measured revisions')
