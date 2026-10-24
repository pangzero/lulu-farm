"""Triangulate concave arm closure boundaries; preserve every original exterior face."""
from pathlib import Path
import json,struct,copy,hashlib,numpy as np,bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1];src=R/'public/models/modular/parts-v1';out=R/'public/models/modular/parts-v3';rep=R/'review/lulu-modular-20261018/parts-v3';out.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True);assert not (out/'lulu-assembled.glb').exists()
b=(src/'lulu-assembled.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);raw=b[28+n:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
def key(p):return tuple(np.round(p.astype(float),6))
parts=[];stats=[]
for mesh in g['meshes']:
 name=mesh['name'];ts=[];ms=[]
 for pr in mesh['primitives']:
  at=pr['attributes'];p=acc(at['POSITION']);no=acc(at['NORMAL']);uv=acc(at['TEXCOORD_0']);co=acc(at['COLOR_0']) if 'COLOR_0' in at else np.ones_like(p);f=acc(pr['indices']).reshape(-1,3);ts.append(np.concatenate([p,no,uv,co],axis=1)[f]);ms.extend([pr.get('material',0)]*len(f))
 t=np.concatenate(ts);ms=np.array(ms)
 if name!='Arm_R':parts.append((name,t,ms));continue
 exterior=t[ms!=2];em=ms[ms!=2];edges={};vdict={}
 for tri in exterior:
  ks=[key(v[:3]) for v in tri]
  for k,v in zip(ks,tri):vdict[k]=v
  for j in range(3):edges.setdefault(tuple(sorted([ks[j],ks[(j+1)%3]])),[]).append((ks[j],ks[(j+1)%3]))
 nxt={a:b for es in edges.values() if len(es)==1 for a,b in es};start=next(iter(nxt));cur=start;loop=[]
 while cur in nxt:
  loop.append(vdict[cur]);cur=nxt.pop(cur)
  if cur==start:break
 assert not nxt and cur==start
 ring=np.array(loop[::-1]);N=len(ring);poly=[Vector((float(v[1]),float(v[2]),0)) for v in ring];idx={tuple(v):i for i,v in enumerate(poly)};tri2=tessellate_polygon([poly]);assert len(tri2)>N-10
 bm=bmesh.new();vv=[bm.verts.new(tuple(v[:3])) for v in ring];bm.verts.ensure_lookup_table()
 for tri in tri2:
  try:bm.faces.new([vv[v if isinstance(v,int) else idx[tuple(v)]] for v in tri])
  except ValueError:pass
 inneredges=[e for e in bm.edges if len(e.link_faces)==2]
 bmesh.ops.subdivide_edges(bm,edges=inneredges,cuts=3,use_grid_fill=True)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table()
 p=np.array([v.co[:] for v in bm.verts],dtype=float);f=np.array([[v.index for v in face.verts] for face in bm.faces]);bm.free()
 # Fixed original seam, harmonic interior in projected YZ domain.
 boundary={key(v[:3]):v for v in ring};fixed=np.array([key(v) in boundary for v in p]);edge=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);w=1/np.maximum(np.linalg.norm(p[edge[:,0],1:3]-p[edge[:,1],1:3],axis=1),1e-5);w=np.minimum(w,2000);den=np.bincount(edge[:,0],weights=w,minlength=len(p))+np.bincount(edge[:,1],weights=w,minlength=len(p));den=np.maximum(den,1e-12)
 for _ in range(160):
  sums=np.bincount(edge[:,0],weights=p[edge[:,1],0]*w,minlength=len(p))+np.bincount(edge[:,1],weights=p[edge[:,0],0]*w,minlength=len(p));q=sums/den;p[~fixed,0]=p[~fixed,0]*.3+q[~fixed]*.7
 kd=KDTree(N)
 for i,v in enumerate(ring):kd.insert(Vector((float(v[1]),float(v[2]),0)),i)
 kd.balance();d=np.array([kd.find(Vector((float(v[1]),float(v[2]),0)))[2] for v in p]);sign=-1 if name=='Arm_R' else 1;p[:,0]+=-sign*.028*np.tanh(d/.035);p[fixed]=np.array([boundary[key(v)][:3] for v in p[fixed]]) if False else p[fixed]
 # Ensure closure winding opposes source boundary and points into the armpit.
 fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
 if fn[:,0].sum()*(-sign)<0:f=f[:,::-1];fn=-fn
 no=np.zeros_like(p)
 for j in range(3):np.add.at(no,f[:,j],fn)
 no/=np.maximum(np.linalg.norm(no,axis=1,keepdims=True),1e-12)
 rgb=np.array([1.,.91,.34]);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);attrs=np.concatenate([p,no,np.zeros((len(p),2)),np.tile(linear,(len(p),1))],axis=1)
 for i in np.flatnonzero(fixed):
  donor=boundary[key(attrs[i,:3])];attrs[i,:3]=donor[:3];attrs[i,3:6]=donor[3:6]
 cap=attrs[f];t=np.concatenate([exterior,cap]);ms=np.concatenate([em,np.full(len(cap),2)]);parts.append((name,t,ms));stats.append({'part':name,'boundary_vertices':N,'new_cap_triangles':len(cap),'fixed_original_exterior_triangles':len(exterior),'method':'concave polygon tessellation, interior edge subdivision, harmonic X field, small convex inward bulge'})
 print(name,len(exterior),len(cap),flush=True)
def write(path,items):
 doc={k:copy.deepcopy(g[k]) for k in ['asset','materials','textures','samplers','extensionsUsed','extensionsRequired'] if k in g};data=bytearray();doc.update(bufferViews=[],accessors=[],images=[],meshes=[],nodes=[],scenes=[{'nodes':[]}],scene=0,buffers=[{}])
 def buf(bb):
  data.extend(b'\0'*((-len(data))%4));i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(bb)});data.extend(bb);return i
 for img in g['images']:
  v=g['bufferViews'][img['bufferView']];q=copy.deepcopy(img);q['bufferView']=buf(raw[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);doc['images'].append(q)
 def add(a,typ,component):
  i=len(doc['accessors']);q={'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
  if typ=='VEC3':q.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  doc['accessors'].append(q);return i
 for name,t,ms in items:
  prim=[]
  for mi in np.unique(ms):
   a=t[ms==mi].reshape(-1,11).astype('<f4');a,inv=np.unique(a,axis=0,return_inverse=True);at={}
   for label,sl,typ in [('POSITION',slice(0,3),'VEC3'),('NORMAL',slice(3,6),'VEC3'),('TEXCOORD_0',slice(6,8),'VEC2')]:at[label]=add(a[:,sl].copy(),typ,5126)
   if mi==2:at['COLOR_0']=add(a[:,8:11].copy(),'VEC3',5126)
   prim.append({'attributes':at,'indices':add(inv.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':int(mi),'mode':4})
  i=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':prim});doc['nodes'].append({'name':name,'mesh':i,'extras':{'part':name,'static_only':True}});doc['scenes'][0]['nodes'].append(i)
 doc['buffers'][0]['byteLength']=len(data);doc['extras']=copy.deepcopy(g.get('extras',{}));doc['extras']['lulu']['revision']='parts-v3';j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data+=b'\0'*((-len(data))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)
write(out/'lulu-assembled.glb',parts)
for item in parts:write(out/(item[0]+'.glb'),[item])
(rep/'arm-cap-rebuild.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats))
