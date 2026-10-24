"""Collect existing derivatives without changing original or historical stage states."""
from pathlib import Path
import json,shutil,struct,io,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
entries=json.loads((O/'scope.json').read_text());mp=R/'public/models/crop-two-stage/manifest.json';manifest=json.loads(mp.read_text());refs=json.loads((R.parent/'art-concepts/crop-meshy-pack-20261018/manifest.json').read_text())['entries'];allstats=[]
for e in entries:
 slug=e['id'];c=next(x for x in manifest['crops'] if x['id']==slug)
 ref=next(x for x in refs if x['id']==slug);refsrc=R.parent/'art-concepts/crop-meshy-pack-20261018'/ref['file'];refdest=R/'public/reference/crop-mature-concepts'/refsrc.name;refdest.parent.mkdir(exist_ok=True);shutil.copy2(refsrc,refdest);c['matureConcept']='/'+str(refdest.relative_to(R/'public'))
 settings=O/slug/'review-settings.json'
 if settings.exists():
  s=json.loads(settings.read_text());c['matureCamera']={'target':s['camera_target'],'height':s['ortho_scale']}
 for v in (['toon-r01','game-r01','toon-r02','toon-r03','game-r02'] if slug=='rose' else ['toon-r01','game-r01']):
  stat=O/slug/v/'metrics.json'
  if not stat.exists():continue
  m=json.loads(stat.read_text());file=R/m['glb'];data=file.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:];imgs=[]
  for i,img in enumerate(doc.get('images',[])):
   bv=doc['bufferViews'][img['bufferView']];off=bv.get('byteOffset',0);im=Image.open(io.BytesIO(binary[off:off+bv['byteLength']]));size=im.size;im.verify();imgs.append({'index':i,'width':size[0],'height':size[1],'mime':img.get('mimeType'),'bytes':bv['byteLength'],'decode':'passed'})
  m['images']=imgs;m['vertices_exported']=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for mesh in doc['meshes'] for p in mesh['primitives']);m['exported_cameras']=len(doc.get('cameras',[]));m['exported_nodes']=len(doc.get('nodes',[]));m['original_source_name']=e['original_name'];m['original_import_source']=e['source'];m['original_import_source_sha256']=hashlib.sha256((R/e['source']).read_bytes()).hexdigest()
  stat.write_text(json.dumps(m,ensure_ascii=False,indent=2));allstats.append(m)
  source=R/m['source'];dest=file.parent/'source'/source.name;dest.parent.mkdir(exist_ok=True)
  if not dest.exists():shutil.copy2(source,dest)
  assert hashlib.sha256(dest.read_bytes()).hexdigest()==m['source_sha256']
  inspection=O/slug/v/'inspection-source.json'
  if inspection.exists():
   inspection_data=json.loads(inspection.read_text());source=R/inspection_data['source'];dest=file.parent/'source'/source.name;shutil.copy2(source,dest);m['inspection_source']=inspection_data;stat.write_text(json.dumps(m,ensure_ascii=False,indent=2))
  c['mature'][v]={'file':'/'+str(file.relative_to(R/'public')),'source':'/'+str(dest.relative_to(R/'public')),'scale':1,'label':('卡通候选 '+v) if v.startswith('toon') else ('优化候选 '+v+' · 2K'),'triangles':m['triangles'],'bytes':m['bytes'],'height':m['size'][2],'reviewStatus':'制作检查中／待用户美术验收／设备未测'}
manifest['note']='14 种成熟作物保留原始 Meshy。B01 三种候选沿用，新增 B04／B05／B06 十一种卡通与优化候选；用户美术认可和设备测试待完成。幼苗改由用户 Meshy 制作，历史失败候选仅供对照。'
mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'metrics.json').write_text(json.dumps(allstats,ensure_ascii=False,indent=2));print('Packaged',len(allstats),'derivatives')
