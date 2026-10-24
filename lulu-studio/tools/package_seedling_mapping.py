from pathlib import Path
import json,shutil,hashlib,struct,io
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018';mp=R/'public/models/crop-two-stage/manifest.json';m=json.loads(mp.read_text());metrics=[]
for row in json.loads((O/'mapping.json').read_text()):
 slug=row['id'];v=row.get('current_version','meshy-toon-r01');stat=O/slug/v/'metrics.json'
 if not stat.exists():continue
 metric=json.loads(stat.read_text());source=R/metric['source'];file=R/metric['glb'];dest=file.parent/'source'/source.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(source,dest);assert hashlib.sha256(dest.read_bytes()).hexdigest()==metric['source_sha256']
 raw=file.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);binary=raw[28+n:];ims=[]
 for image in d['images']:
  b=d['bufferViews'][image['bufferView']];start=b.get('byteOffset',0);im=Image.open(io.BytesIO(binary[start:start+b['byteLength']]));size=im.size;im.verify();ims.append(list(size))
 metric['texture_sizes']=ims;stat.write_text(json.dumps(metric,ensure_ascii=False,indent=2));metrics.append(metric)
 c=next(c for c in m['crops'] if c['id']==slug);c['defaultSeedlingVersion']=v;
 if v=='meshy-toon-r02':c['seedling']['meshy-toon-r01']['reviewStatus']='历史 r01：背面叶脉退化，已停用';
 settings=json.loads((O/slug/'review-settings.json').read_text());c['seedlingCamera']={'target':settings['target'],'height':settings['height']}
 c['seedling']['meshy-original']={'file':row['input']['file'],'source':None,'scale':row['height']/row['input']['raw_height'],'label':'Meshy共享原型 · 原件适配尺度','family':row['family_label'],'mappingNote':row['mapping_note'],'triangles':row['input']['triangles'],'bytes':row['input']['bytes'],'height':row['height'],'reviewStatus':'用户原件；尚未经美术验收','originalFile':row['input']['file']}
 c['seedling'][v]={'file':'/'+str(file.relative_to(R/'public')),'source':'/'+str(dest.relative_to(R/'public')),'scale':1,'label':'Meshy映射 · 微改卡通 '+v.split('-')[-1],'family':row['family_label'],'mappingNote':row['mapping_note'],'triangles':metric['triangles'],'bytes':metric['bytes'],'height':metric['size'][2],'reviewStatus':'制作检查中／用户未认可／设备未测','originalFile':row['input']['file']}
m['note']='成熟14种卡通／优化候选保留；幼苗以用户4个Meshy原型映射14种，逐项微改和卡通化，共享关系明确标注。C12/C16继续暂缓；新幼苗待用户验收，设备未测。'
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2));(O/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));print('Registered',len(metrics),'seedling derivatives; mature entries preserved')
