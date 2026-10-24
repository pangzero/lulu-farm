"""Remove orange donor color from newly authored body skin only."""
from pathlib import Path
import json,struct,hashlib,numpy as np
R=Path(__file__).resolve().parents[1];src=R/'public/models/modular/m05';out=R/'public/models/modular/m06';rep=R/'review/lulu-modular-20261018/m06';out.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True)
assert not (out/'lulu-assembled.glb').exists()
def acc(g,raw,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];return np.ndarray((a['count'],3),dtype='<f4',buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
records=[]
for file in sorted(src.glob('*.glb')):
 blob=file.read_bytes();n=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+n]);raw=bytearray(blob[28+n:]);changed=0
 for mesh in g['meshes']:
  if mesh.get('name')!='Body':continue
  for pr in mesh['primitives']:
   if pr.get('material')!=2:continue
   p=acc(g,raw,pr['attributes']['POSITION']);ai=pr['attributes']['COLOR_0'];c=acc(g,raw,ai);mask=p[:,1]<-.38;rgb=np.array([1.,.91,.34]);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);c[mask]=linear;changed+=int(mask.sum());a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];off=v.get('byteOffset',0)+a.get('byteOffset',0);raw[off:off+c.nbytes]=c.tobytes();a['min']=c.min(0).tolist();a['max']=c.max(0).tolist()
 g['extras']['lulu']['revision']='m06';g['extras']['lulu']['body_cap_color']='Only newly authored body closure skin colored yellow; original textures and exterior materials unchanged'
 j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4);dest=out/file.name;dest.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw);records.append({'file':file.name,'new_body_color_vertices':changed,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(rep/'material-cleanup.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps(records,ensure_ascii=False))
