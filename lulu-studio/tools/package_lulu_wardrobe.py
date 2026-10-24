"""Produce actual separate base/shorts assets, pruning unrelated geometry buffers."""
from pathlib import Path
import sys,json,copy,struct,hashlib,zipfile,shutil
sys.path.insert(0,str(Path(__file__).parent));from lulu_patch_io import read_glb
R=Path(__file__).resolve().parents[1];out=R/'public/models/wardrobe-rig/full-r02';g,raw=read_glb(out/'lulu-rig.glb')
def pack(names,file):
 d=copy.deepcopy(g);mis=[i for i,m in enumerate(d['meshes']) if m['name'] in names];mm={old:i for i,old in enumerate(mis)};ids=[i for i,n in enumerate(d['nodes']) if ('mesh' in n and n['mesh'] in mis) or i in d['skins'][0]['joints']];nm={old:i for i,old in enumerate(ids)};d['nodes']=[d['nodes'][i] for i in ids]
 for n in d['nodes']:
  if 'mesh' in n:n['mesh']=mm[n['mesh']]
  if 'children' in n:n['children']=[nm[i] for i in n['children'] if i in nm]
 d['meshes']=[d['meshes'][i] for i in mis]
 for scene in d['scenes']:scene['nodes']=[nm[i] for i in scene['nodes'] if i in nm]
 for skin in d['skins']:skin['joints']=[nm[i] for i in skin['joints']];skin['skeleton']=nm[skin['skeleton']]
 for anim in d.get('animations',[]):
  for c in anim['channels']:c['target']['node']=nm[c['target']['node']]
 used=set()
 for mesh in d['meshes']:
  for p in mesh['primitives']:used.update(p['attributes'].values());used.add(p['indices'])
 for skin in d['skins']:used.add(skin['inverseBindMatrices'])
 for anim in d.get('animations',[]):
  for s in anim['samplers']:used.update([s['input'],s['output']])
 ids=sorted(used);am={old:i for i,old in enumerate(ids)};d['accessors']=[d['accessors'][i] for i in ids]
 for mesh in d['meshes']:
  for p in mesh['primitives']:p['attributes']={k:am[v] for k,v in p['attributes'].items()};p['indices']=am[p['indices']]
 for skin in d['skins']:skin['inverseBindMatrices']=am[skin['inverseBindMatrices']]
 for anim in d.get('animations',[]):
  for s in anim['samplers']:s['input']=am[s['input']];s['output']=am[s['output']]
 views={a['bufferView'] for a in d['accessors']}|{im['bufferView'] for im in d['images']};views=sorted(views);vm={old:i for i,old in enumerate(views)};data=bytearray();newviews=[]
 for vi in views:
  v=copy.deepcopy(d['bufferViews'][vi]);offset=v.get('byteOffset',0);bb=raw[offset:offset+v['byteLength']];data.extend(b'\0'*((-len(data))%4));v['byteOffset']=len(data);data.extend(bb);newviews.append(v)
 d['bufferViews']=newviews
 for a in d['accessors']:a['bufferView']=vm[a['bufferView']]
 for im in d['images']:im['bufferView']=vm[im['bufferView']]
 d['buffers']=[{'byteLength':len(data)}];d['extras']['lulu']['modular_rig']['active_parts']=[m['name'] for m in d['meshes']];d['extras']['lulu']['modular_rig']['separate_asset']=file;j=json.dumps(d,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data+=b'\0'*((-len(data))%4);(out/file).write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)
pack({m['name'] for m in g['meshes'] if m['name']!='Shorts'},'lulu-base.glb');pack({'Shorts'},'shorts-template.glb')
report=[]
for name in ['lulu-rig.glb','lulu-base.glb','shorts-template.glb']:
 p=out/name;doc,_=read_glb(p);report.append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'parts':[m['name'] for m in doc['meshes']],'bones':len(doc['skins'][0]['joints'])})
(R/'review/lulu-wardrobe-rig-20261018/full-r02/package.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
