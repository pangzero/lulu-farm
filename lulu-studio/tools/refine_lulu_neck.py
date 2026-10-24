"""Replace only the overlapping neck ends with a boundary-constrained bridge.
Source attribute bytes of untouched components are retained. Existing triangles
fully outside the two cut fields are retained with their original attributes.
"""
from pathlib import Path
import argparse,copy,hashlib,json,math,struct
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-neck-junction-20261023'
ap=argparse.ArgumentParser();ap.add_argument('--rev',default='neck-r01');ap.add_argument('--upper',type=float,default=.510);ap.add_argument('--lower',type=float,default=.425);ap.add_argument('--side',type=float,default=.035);args=ap.parse_args();O=D/args.rev
if O.exists():raise RuntimeError('Preserve revisions')
O.mkdir()
source=D/'baseline/review/lulu-hybrid-assembly-20261023/hybrid-r02/lulu-hybrid.glb'
b=source.read_bytes();sz=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+sz]);binary=bytearray(b[28+sz:]);before=copy.deepcopy(g)
types={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt=np.dtype(types[a['componentType']]);k=dims[a['type']];return np.ndarray((a['count'],k),dt,buffer=b[28+sz:],offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()
def trs(n):
 if 'matrix' in n:return np.array(n['matrix']).reshape(4,4).T
 x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4);m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
world={}
def visit(i,m):
 m=m@trs(g['nodes'][i]);world[i]=m
 for j in g['nodes'][i].get('children',[]):visit(j,m)
for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i,np.eye(4))
C=np.array([0.,-.015])
def theta(p):return np.arctan2(p[...,2]-C[1],p[...,0]-C[0])
def limit(p):return args.lower+args.side*np.cos(theta(p))**2

def addacc(a,typ,component=5126):
 dt=np.dtype(types[component]);a=np.ascontiguousarray(a,dtype=dt)
 while len(binary)%4:binary.append(0)
 offset=len(binary);raw=a.tobytes();binary.extend(raw);vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw)})
 ac={'bufferView':vi,'componentType':component,'count':len(a),'type':typ}
 if typ=='VEC3':ac.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 ix=len(g['accessors']);g['accessors'].append(ac);return ix

def writeprimitive(rows,keys,slices,material):
 rows=np.ascontiguousarray(rows.reshape(-1,rows.shape[-1]),dtype=np.float32)
 unique,idx=np.unique(rows,axis=0,return_inverse=True);attrs={}
 for k in keys:
  ar=unique[:,slices[k]];attrs[k]=addacc(ar,'SCALAR' if ar.shape[1]==1 else 'VEC'+str(ar.shape[1]))
 return {'attributes':attrs,'indices':addacc(idx.reshape(-1,1),'SCALAR',5125),'material':material,'mode':4}

def cutpart(name,keep_above):
 ni=next(i for i,n in enumerate(g['nodes']) if n.get('name')==name);node=g['nodes'][ni];mat=world[ni];nmat=np.linalg.inv(mat[:3,:3]).T;newpr=[];segments=[];stats={'name':name,'kept_triangles':0,'cut_triangles':0,'removed_triangles':0};proof=[]
 for pr in copy.deepcopy(g['meshes'][node['mesh']]['primitives']):
  keys=list(pr['attributes']);arrays=[acc(pr['attributes'][k]) for k in keys];ends=np.cumsum([0]+[a.shape[1] for a in arrays]);sl={k:slice(ends[i],ends[i+1]) for i,k in enumerate(keys)};v=np.concatenate(arrays,axis=1);faces=acc(pr['indices']).reshape(-1,3);t=v[faces];p=t[:,:,sl['POSITION']].astype(float)@mat[:3,:3].T+mat[:3,3]
  d=p[:,:,1]-args.upper if keep_above else limit(p)-p[:,:,1]
  inside=d>=0;whole=inside.all(1);none=~inside.any(1);cuts=np.where(~whole&~none)[0]
  stats['kept_triangles']+=int(whole.sum());stats['removed_triangles']+=int(none.sum());stats['cut_triangles']+=len(cuts)
  added=[]
  for ix in cuts:
   poly=[];inter=[]
   for j in range(3):
    k=(j+1)%3;va,vb=t[ix,j],t[ix,k];da,db=d[ix,j],d[ix,k]
    if da>=0:poly.append(va)
    if (da>=0)!=(db>=0):
     h=da/(da-db);vnew=va.astype(float)+(vb-va).astype(float)*h;poly.append(vnew);inter.append(vnew)
   for j in range(1,len(poly)-1):added.append(np.array([poly[0],poly[j],poly[j+1]]))
   if len(inter)==2:
    out=[]
    for q in inter:
     pos=q[sl['POSITION']]@mat[:3,:3].T+mat[:3,3];n=q[sl['NORMAL']]@nmat.T;n/=max(np.linalg.norm(n),1e-12);out.append(np.r_[pos,n])
    segments.append(out)
  retained=t[whole];proof.append(hashlib.sha256(retained.tobytes()).hexdigest())
  out=np.concatenate([retained,np.array(added)]) if len(added) else retained
  if len(out):newpr.append(writeprimitive(out,keys,sl,pr.get('material',0)))
 g['meshes'][node['mesh']]['primitives']=newpr
 stats['retained_triangle_attributes_sha256']=proof
 # Build the exact intersection boundary, independent of UV/material splits.
 segs=np.array(segments);key=lambda p:tuple(np.round(p[:3],7));points={};adj={}
 for a,c in segs:
  ka,kc=key(a),key(c)
  if ka==kc:continue
  points[ka]=a;points[kc]=c;adj.setdefault(ka,set()).add(kc);adj.setdefault(kc,set()).add(ka)
 # Coincident material/UV seams can differ below float32 precision.
 ends=[k for k,v in adj.items() if len(v)==1]
 while ends:
  a=ends.pop();dist=[(np.linalg.norm(np.array(a)-np.array(c)),c) for c in ends]
  if not dist:break
  dd,c=min(dist)
  if dd>2e-6:break
  ends.remove(c)
  for nei in list(adj[c]):
   adj[nei].discard(c);adj[nei].add(a);adj[a].add(nei)
  del adj[c]
 bad={k:len(v) for k,v in adj.items() if len(v)!=2}
 if bad:raise RuntimeError(f'{name} bad boundary degrees {len(bad)} {list(bad.items())[:5]}')
 loops=[];remaining=set(adj)
 while remaining:
  start=next(iter(remaining));seq=[];prev=None;cur=start
  while True:
   seq.append(cur);remaining.discard(cur);opts=adj[cur]-({prev} if prev is not None else set());nxt=next(iter(opts));prev,cur=cur,nxt
   if cur==start:break
  loops.append(np.array([points[k] for k in seq]))
 loops.sort(key=len,reverse=True);print(name,'loops',[len(x) for x in loops],flush=True)
 if len(loops)!=1:raise RuntimeError('Need one explicit neck boundary; do not guess')
 ring=loops[0];q=ring[:,[0,2]]-C
 if np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))<0:ring=ring[::-1]
 angles=theta(ring[:,:3]);start=np.argmin((angles+2*np.pi)%(2*np.pi));ring=np.roll(ring,-start,axis=0);ang=np.unwrap(theta(ring[:,:3]));ang-=math.floor(ang[0]/(2*np.pi))*2*np.pi
 if ang[-1]-ang[0]<6:raise RuntimeError('Non full boundary')
 inversions=int(np.sum(np.diff(ang)<=0));print(name,'angular inversions',inversions,flush=True)
 # Tiny source edges can reverse ray angle: arc-length parameter is used only
 # if necessary. Positions remain the exact original intersection locations.
 if inversions:
  ds=np.linalg.norm(np.roll(ring[:,:3],-1,axis=0)-ring[:,:3],axis=1);ang=ang[0]+np.r_[0,np.cumsum(ds[:-1])]/ds.sum()*2*np.pi
 stats['boundary_vertices']=len(ring);stats['boundary_y_range']=[float(ring[:,1].min()),float(ring[:,1].max())];stats['parameter_fallback']=bool(inversions)
 return ring,ang,stats
head,ht,hs=cutpart('Lulu_Head_Mirrored',True);body,bt,bs=cutpart('Body',False)

def interp(ring,t,ang):
 t=np.r_[t[-1]-2*np.pi,t,t[0]+2*np.pi];v=np.vstack([ring[-1],ring,ring[0]]);aa=(ang-t[1])%(2*np.pi)+t[1];return np.stack([np.interp(aa,t,v[:,k]) for k in range(v.shape[1])],axis=-1)

def slopes(ring,t):
 n=ring[:,3:6];rad=np.c_[np.cos(t),np.zeros(len(t)),np.sin(t)];nr=np.einsum('ij,ij->i',n,rad);s=np.clip(-n[:,1]/np.maximum(nr,.15),-2.3,2.3);A=np.stack([np.ones_like(t)]+[f(k*t) for k in range(1,9) for f in (np.cos,np.sin)],axis=1);coef=np.linalg.lstsq(A,s,rcond=None)[0]
 def fn(a):return np.stack([np.ones_like(a)]+[f(k*a) for k in range(1,9) for f in (np.cos,np.sin)],axis=-1)@coef
 return fn
hslope,bslope=slopes(head,ht),slopes(body,bt)
def surface(u,t):
 H=interp(head,ht,t)[:,:3];B=interp(body,bt,t)[:,:3];dy=H[:,1]-B[:,1];rad=np.c_[np.cos(t),np.zeros(len(t)),np.sin(t)];T0=rad*bslope(t)[:,None];T1=rad*hslope(t)[:,None];T0[:,1]=1;T1[:,1]=1
 return (2*u**3-3*u*u+1)*B+(u**3-2*u*u+u)*dy[:,None]*T0+(-2*u**3+3*u*u)*H+(u**3-u*u)*dy[:,None]*T1

def normals(u,t):
 e=.0001;ds=surface(u,t+e)-surface(u,t-e);du=surface(u+e,t)-surface(u-e,t);n=np.cross(du,ds);n/=np.maximum(np.linalg.norm(n,axis=1),1e-12)[:,None];rad=np.c_[np.cos(t),np.zeros(len(t)),np.sin(t)];n[np.einsum('ij,ij->i',n,rad)<0]*=-1;return n

# Rings are joined by an angular zipper; exact endpoint vertices are used.
N=512;ts=np.linspace(0,2*np.pi,N,endpoint=False);rows=[];angles=[];rows.append(body);angles.append(bt)
for u in np.linspace(0,1,25)[1:-1]:rows.append(np.c_[surface(u,ts),normals(u,ts)]);angles.append(ts)
rows.append(head);angles.append(ht)
verts=np.concatenate(rows);faces=[];offsets=np.cumsum([0]+[len(r) for r in rows])
def zipper(i):
 a,b=angles[i],angles[i+1];na,nb=len(a),len(b);ia=ib=0
 # Use a shared zero-crossing seam. Both boundary arrays start just above zero.
 while ia<na or ib<nb:
  aa=a[(ia+1)%na]+(2*np.pi if ia+1>=na else 0);bb=b[(ib+1)%nb]+(2*np.pi if ib+1>=nb else 0)
  va=offsets[i]+ia%na;vb=offsets[i+1]+ib%nb
  if ib>=nb or (ia<na and aa<bb):faces.append((va,offsets[i]+(ia+1)%na,vb));ia+=1
  else:faces.append((va,offsets[i+1]+(ib+1)%nb,vb));ib+=1
for i in range(len(rows)-1):zipper(i)
faces=np.array(faces);p=verts[:,:3];cr=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]]);nn=verts[faces,3:6].mean(1);flip=np.einsum('ij,ij->i',cr,nn)<0;faces[flip]=faces[flip][:,::-1]
mat=len(g['materials']);g['materials'].append({'name':'Neck transition neutral gray','pbrMetallicRoughness':{'baseColorFactor':[.47,.47,.47,1],'roughnessFactor':.85,'metallicFactor':0}})
pr={'attributes':{'POSITION':addacc(verts[:,:3],'VEC3'),'NORMAL':addacc(verts[:,3:6],'VEC3')},'indices':addacc(faces.reshape(-1,1),'SCALAR',5125),'material':mat};mi=len(g['meshes']);g['meshes'].append({'name':'Neck_Transition','primitives':[pr]});ni=len(g['nodes']);g['nodes'].append({'name':'Neck_Transition','mesh':mi,'extras':{'scope':'Local neck only; exact source edge positions, constrained transition. No rig.'}});g['scenes'][g.get('scene',0)]['nodes'].append(ni)
while len(binary)%4:binary.append(0)
g['buffers']=[{'byteLength':len(binary)}];js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);(O/'lulu-neck.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
np.savez_compressed(O/'neck-boundaries.npz',head=head,head_t=ht,body=body,body_t=bt,bridge=verts,triangles=faces)
report={'revision':args.rev,'base':'hybrid-r02','head_keep_y_min':args.upper,'body_keep_y_max':'lower + side*cos(theta)^2','lower':args.lower,'side':args.side,'head':hs,'body':bs,'bridge_vertices':len(verts),'bridge_triangles':len(faces),'other_six_parts_unchanged':True,'transform_changes':0,'bones':0,'status':'INTERNAL_VISUAL_REVIEW','note':'Three abutting surfaces with coincident endpoint positions/normals. Head/Body/Neck are individually open at exact seam loops; assembly continuity must be checked.'}
(O/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
