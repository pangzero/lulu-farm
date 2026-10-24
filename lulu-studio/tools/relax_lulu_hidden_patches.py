"""Relax only newly authored inner-arm / body-side patch interiors, seams fixed."""
from pathlib import Path
import json,struct,numpy as np,hashlib
R=Path(__file__).resolve().parents[1];src=R/'public/models/modular/parts-v1';out=R/'public/models/modular/parts-v2';rep=R/'review/lulu-modular-20261018/parts-v2';out.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True);assert not (out/'lulu-assembled.glb').exists()
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),bytearray(b[28+n:])
def acc(g,raw,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
def key(p):return tuple(np.round(p.astype(float),6))
records=[]
for file in src.glob('*.glb'):
 g,raw=read(file);changes=[]
 for mesh in g['meshes']:
  name=mesh['name']
  if name not in ['Arm_R','Arm_L','Body']:continue
  fixed=set()
  for pr in mesh['primitives']:
   if pr.get('material')!=2:fixed.update(key(p) for p in acc(g,raw,pr['attributes']['POSITION']))
  for pr in mesh['primitives']:
   if pr.get('material')!=2:continue
   p=acc(g,raw,pr['attributes']['POSITION']);n=acc(g,raw,pr['attributes']['NORMAL']);f=acc(g,raw,pr['indices']).reshape(-1,3);_,first,iv=np.unique(np.round(p.astype(float),6),axis=0,return_index=True,return_inverse=True);v=p[first].copy();old=v.copy();wf=iv[f];edge=np.unique(np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1),axis=0);edge=edge[edge[:,0]!=edge[:,1]]
   pinned=np.array([key(q) in fixed for q in v]);weight=(~pinned).astype(float)
   if name=='Body':
    weight*=np.clip((v[:,1]+.445)/.03,0,1)*np.clip((-.12-v[:,1])/.035,0,1)
   count=np.bincount(edge.reshape(-1),minlength=len(v));count=np.maximum(count,1)
   # Iteration is limited to additional inner patches; source exterior is fixed.
   for _ in range(32):
    sums=np.zeros_like(v);np.add.at(sums,edge[:,0],v[edge[:,1]]);np.add.at(sums,edge[:,1],v[edge[:,0]]);mean=sums/count[:,None];v+=(mean-v)*(.45*weight[:,None])
   p=v[iv];norm=np.zeros_like(v);fn=np.cross(v[wf[:,1]]-v[wf[:,0]],v[wf[:,2]]-v[wf[:,0]])
   for j in range(3):np.add.at(norm,wf[:,j],fn)
   norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12);moving=weight[iv]>.000001;n[moving]=norm[iv[moving]]
   for ai,value in [(pr['attributes']['POSITION'],p),(pr['attributes']['NORMAL'],n)]:
    a=g['accessors'][ai];bv=g['bufferViews'][a['bufferView']];off=bv.get('byteOffset',0)+a.get('byteOffset',0);raw[off:off+value.nbytes]=value.astype('<f4').tobytes();a['min']=value.min(0).tolist();a['max']=value.max(0).tolist()
   changes.append({'part':name,'max_new_surface_displacement':float(np.linalg.norm(v-old,axis=1).max()),'original_exterior_and_boundary':'fixed'})
 g['extras']['lulu']['revision']='parts-v2';j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4);dest=out/file.name;dest.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw);records.append({'file':file.name,'changes':changes,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(rep/'hidden-patch-cleanup.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps(records))
