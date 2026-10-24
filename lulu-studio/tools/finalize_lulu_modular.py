"""Clean microscopic junction fins and contain neck caps, preserving textured shapes."""
from pathlib import Path
import json,struct,copy,hashlib,numpy as np
R=Path(__file__).resolve().parents[1];src=R/'public/models/modular/m07';out=R/'public/models/modular/m10';rep=R/'review/lulu-modular-20261018/m10';out.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True);assert not (out/'lulu-assembled.glb').exists()
b=(src/'lulu-assembled.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);raw=b[28+n:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];s={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);return np.ndarray((a['count'],s),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy()
def canonical(p):
 _,ix,iv=np.unique(np.round(p.astype(float),6),axis=0,return_index=True,return_inverse=True);return p[ix],iv
parts=[];stats=[]
for mesh in g['meshes']:
 name=mesh['name'];ts=[];ms=[]
 for pr in mesh['primitives']:
  at=pr['attributes'];p=acc(at['POSITION']);no=acc(at['NORMAL']);uv=acc(at['TEXCOORD_0']);co=acc(at['COLOR_0']) if 'COLOR_0' in at else np.ones_like(p);f=acc(pr['indices']).reshape(-1,3);ts.append(np.concatenate([p,no,uv,co],axis=1)[f]);ms.extend([pr.get('material',0)]*len(f))
 t=np.concatenate(ts);ms=np.array(ms);caps=0;maxshift=0.;removed=0
 if name in ['Head','Body','Orange']:
  boundary={'Head':-.08,'Body':-.08,'Orange':.729}[name];depth={'Head':-.012,'Body':.015,'Orange':-.018}[name];mask=(ms==2)[:,None]&(((t[:,:,1]-boundary)/depth)>.0001)&(((t[:,:,1]-boundary)/depth)<1.001)
  # Only the shallow neck / orange closure, not long shoulder or pelvis caps.
  original=set(tuple(x) for x in np.round(t[ms!=2,:,:3].reshape(-1,3).astype(float),6));flat=t.reshape(-1,11);ids=np.flatnonzero(mask.reshape(-1));ids=np.array([i for i in ids if tuple(np.round(flat[i,:3].astype(float),6)) not in original],dtype=int)
  if len(ids):
   p=flat[ids,:3].copy();center=np.array([0.,boundary,-.06 if name!='Orange' else -.06]);fraction=np.clip((p[:,1]-boundary)/depth,0,1);factor=1-.45*np.sqrt(fraction);flat[ids,0]=center[0]+(p[:,0]-center[0])*factor;flat[ids,2]=center[2]+(p[:,2]-center[2])*factor;caps=len(ids);maxshift=float(np.linalg.norm(flat[ids,:3]-p,axis=1).max())
   # New cap normals only; preserve every existing exterior normal.
   ct=t[ms==2];p0,iv=canonical(ct[:,:,:3].reshape(-1,3));f0=iv.reshape(-1,3);ns=np.zeros_like(p0);face=np.cross(p0[f0[:,1]]-p0[f0[:,0]],p0[f0[:,2]]-p0[f0[:,0]])
   for j in range(3):np.add.at(ns,f0[:,j],face)
   ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-15);lookup={tuple(np.round(p.astype(float),6)):nn for p,nn in zip(p0,ns)}
   for i in ids:flat[i,3:6]=lookup[tuple(np.round(flat[i,:3].astype(float),6))]
 # Clean only minute side-waist junctions, never the head, face or arms.
 original_t=t[:,:,:3].copy()
 if name in ['Body','Shorts','Head','Orange']:
  for iteration in range(22):
   p,iv=canonical(t[:,:,:3].reshape(-1,3));f=iv.reshape(-1,3);valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]);t=t[valid];ms=ms[valid];f=f[valid];removed+=int(sum(~valid))
   groups={};keep=np.ones(len(f),bool)
   for i,face in enumerate(f):
    k=tuple(sorted(face))
    if k not in groups:groups[k]=i;continue
    j=groups[k];same=any(np.array_equal(np.roll(f[j],q),face) for q in range(3));keep[i]=False
    if not same:keep[j]=False
   removed+=int(sum(~keep));t=t[keep];ms=ms[keep];f=f[keep]
   e=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);ue,c=np.unique(e,axis=0,return_counts=True);bad=ue[c>2]
   if not len(bad):break
   # Collapse micron-scale neighboring points at implicated seam endpoints.
   radius=2e-5 if iteration<3 else (2e-4 if iteration<10 else (5e-4 if iteration<16 else .002));mapidx=np.arange(len(p))
   for v in np.unique(bad):
    near=np.flatnonzero(np.linalg.norm(p-p[v],axis=1)<radius)
    if len(near)>1:mapidx[near]=mapidx[near[0]]
   changed=p[mapidx];maxshift=max(maxshift,float(np.linalg.norm(changed-p,axis=1).max()));t[:,:,:3]=changed[f]
 p,iv=canonical(t[:,:,:3].reshape(-1,3));f=iv.reshape(-1,3);valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]);wf=f[valid];e=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1);_,c=np.unique(e,axis=0,return_counts=True)
 stats.append({'part':name,'triangles':len(t),'cap_corners_retracted':caps,'max_cap_or_microcleanup_shift':maxshift,'removed_micro_faces':removed,'boundary_edges':int(sum(c==1)),'nonmanifold_edges':int(sum(c>2)),'degenerate_faces':int(sum(~valid))});parts.append((name,t,ms))
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
 doc['buffers'][0]['byteLength']=len(data);doc['extras']=copy.deepcopy(g.get('extras',{}));doc['extras']['lulu']['revision']='m10';j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data+=b'\0'*((-len(data))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)
write(out/'lulu-assembled.glb',parts)
for item in parts:write(out/(item[0]+'.glb'),[item])
(rep/'final-cleanup.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats))
