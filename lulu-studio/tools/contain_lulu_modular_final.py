"""Constrain authored under-clothing surfaces to the original visible volume.
Only hidden closure vertices change. Existing exterior and seam positions stay.
"""
from pathlib import Path
import json,struct,copy,numpy as np,hashlib,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];src=R/'public/models/modular/m09';out=R/'public/models/modular/parts-v1';report=R/'review/lulu-modular-20261018/parts-v1';out.mkdir(parents=True,exist_ok=True);report.mkdir(parents=True,exist_ok=True)
assert not (out/'lulu-assembled.glb').exists()
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),bytearray(b[28+n:])
def acc(g,raw,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
def key(p):return tuple(np.rint(p*1e6).astype(np.int64))
g,b=read(R/'public/models/lulu-official-v1.glb');pr=g['meshes'][0]['primitives'];p=acc(g,b,pr[0]['attributes']['POSITION']);f=np.concatenate([acc(g,b,q['indices']).reshape(-1,3) for q in pr]);bvh=BVHTree.FromPolygons([Vector(x) for x in p],f.tolist(),all_triangles=True)
records=[]
for file in sorted(src.glob('*.glb')):
 g,raw=read(file);stats=[]
 for mesh in g['meshes']:
  name=mesh.get('name','')
  if name not in ['Body','Leg_R','Leg_L']:continue
  original=set()
  for pr in mesh['primitives']:
   if pr.get('material')!=2:original.update(key(v) for v in acc(g,raw,pr['attributes']['POSITION']))
  for pr in mesh['primitives']:
   if pr.get('material')!=2:continue
   ai=pr['attributes']['POSITION'];p=acc(g,raw,ai);old=p.copy();norm=acc(g,raw,pr['attributes']['NORMAL']);f=acc(g,raw,pr['indices']).reshape(-1,3)
   for i,v in enumerate(p):
    if key(v) in original:continue
    if name=='Body' and v[1]>-.445:continue
    if name.startswith('Leg') and v[1]<-.85:continue
    center=Vector((0 if name=='Body' else (-.26 if name=='Leg_R' else .26),float(v[1]),-.09));delta=Vector(v)-center;dist=delta.length
    if dist<1e-7:continue
    direction=delta.normalized();hit,normal,index,d=bvh.ray_cast(center,direction,2.)
    if hit is not None and dist>d-.004:
     p[i]=center+direction*max(.001,d-.004)
   moved=np.linalg.norm(p-old,axis=1)>1e-8
   if moved.any():
    tri=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);ns=np.zeros_like(p)
    for j in range(3):np.add.at(ns,f[:,j],tri)
    ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-12);norm[moved]=ns[moved]
    for idx,a in [(ai,p),(pr['attributes']['NORMAL'],norm)]:
     av=g['accessors'][idx];vv=g['bufferViews'][av['bufferView']];off=vv.get('byteOffset',0)+av.get('byteOffset',0);raw[off:off+a.nbytes]=a.astype('<f4').tobytes()
     av['min']=a.min(0).tolist();av['max']=a.max(0).tolist()
   stats.append({'part':name,'authored_vertices_moved':int(moved.sum()),'max_displacement':float(np.linalg.norm(p-old,axis=1).max()),'retained_exterior_and_seams':'unchanged'})
 g.setdefault('extras',{})['lulu']['revision']='parts-v1';g['extras']['lulu']['hidden_surface_containment']='Authored under-clothing surfaces constrained inside official-v1 shell; all existing exterior/seam vertices fixed'
 j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4);dest=out/file.name;dest.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw)
 records.append({'file':file.name,'changes':stats,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(report/'containment.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(json.dumps(records,ensure_ascii=False))
