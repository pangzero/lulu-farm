"""Static, additive modular reconstruction from immutable Lulu official v1.
Original exterior is retained; the hidden torso-side junction has localized
coordinate/normal reconstruction. Curved closures are authored independently
for torso and arm. Head/face, arm exterior and other silhouette are preserved.
There is no boolean subtraction, armature, skin, or animation in this tool.
"""
from pathlib import Path
import json,struct,hashlib,sys,copy,math
import numpy as np
from PIL import Image
import io
R=Path(__file__).resolve().parents[1]
REV=sys.argv[1] if len(sys.argv)>1 else 'r01'
MODE=sys.argv[2] if len(sys.argv)>2 else 'one-arm'
OUT=R/'public/models/modular'/REV
REPORT=R/'review/lulu-modular-20261018'/REV
assert not (OUT/'lulu-assembled.glb').exists(),'New revision required'
OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
source=R/'review/lulu-modular-20261018/baseline/lulu-official-v1.glb'
b=source.read_bytes();jl=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+jl]);raw=b[28+jl:]
SHA=hashlib.sha256(b).hexdigest()
assert SHA=='5f770f539c3927b9e4d26a73bf96070e86e6b6cdd04e9710074b4c6645207e7d'
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];s={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);return np.ndarray((a['count'],s),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',s*dt.itemsize),dt.itemsize)).copy()
# Each corner stores P,N,UV and linear vertex color for newly authored surfaces.
T=[];M=[]
for pr in g['meshes'][0]['primitives']:
 p=acc(pr['attributes']['POSITION']);n=acc(pr['attributes']['NORMAL']);u=acc(pr['attributes']['TEXCOORD_0']);f=acc(pr['indices']).reshape(-1,3)
 v=np.concatenate([p,n,u,np.ones((len(p),3))],axis=1);T.append(v[f]);M.extend([pr.get('material',0)]*len(f))
T=np.concatenate(T);M=np.array(M)
original_positions=T[:,:,:3].copy()
pflat=T[:,:,:3].reshape(-1,3);_,first,inverse=np.unique(np.round(pflat,6),axis=0,return_index=True,return_inverse=True)
T[:,:,:3]=pflat[first][inverse].reshape(-1,3,3)
WELD_DELTA=float(np.max(np.abs(T[:,:,:3]-original_positions)))
area=np.linalg.norm(np.cross(T[:,1,:3]-T[:,0,:3],T[:,2,:3]-T[:,0,:3]),axis=1)
T=T[area>1e-15];M=M[area>1e-15]

base_tex=g['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'];iminfo=g['images'][g['textures'][base_tex]['source']];bv=g['bufferViews'][iminfo['bufferView']];im=np.array(Image.open(io.BytesIO(raw[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])).convert('RGB'))/255
# glTF UV 0 is image top; image bytes are sampled without Blender's pixel flip.
def color(uv):
 uv=np.asarray(uv);h,w=im.shape[:2];return im[np.clip((uv[...,1]*(h-1)).astype(int),0,h-1),np.clip((uv[...,0]*(w-1)).astype(int),0,w-1)]
def lin(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
skin_data=np.load(R/'review/lulu-rig-20261018/skin-region-smooth.npz')
skin_lookup={tuple(np.rint(p*1e6).astype(np.int64)):float(w) for p,w in zip(skin_data['p'],skin_data['skin'])}
def arm_cut(y):
 return np.interp(y,[-.67,-.63,-.59,-.54,-.48,-.40,-.32,-.25,-.20,-.16,-.13,-.10],[.64,.54,.488,.46,.433,.405,.395,.393,.394,.40,.43,.55])
def arm_field(v,sign):
 x,y,z=v[...,0]*sign,v[...,1],v[...,2]
 skin=np.array([skin_lookup.get(tuple(np.rint(p*1e6).astype(np.int64)),1.) for p in v[...,:3].reshape(-1,3)]).reshape(y.shape)
 return np.minimum(np.minimum(x-arm_cut(y),-.1-y),np.where(y<-.42,(skin-.5)*.3,1.))
def smooth_interp(x,xs,ys):
 xs=np.asarray(xs);ys=np.asarray(ys);m=np.gradient(ys,xs);x=np.clip(x,xs[0],xs[-1]);i=np.clip(np.searchsorted(xs,x)-1,0,len(xs)-2);h=xs[i+1]-xs[i];t=(x-xs[i])/h
 return (2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h*m[i]+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h*m[i+1]
def body_surface(y,z):
 yc=np.array([-.65,-.54,-.48,-.40,-.32,-.25,-.20,-.13,-.09])
 width=smooth_interp(y,yc,[.47,.49,.475,.457,.445,.435,.43,.44,.45])
 front=smooth_interp(y,yc,[.23,.295,.302,.292,.27,.242,.22,.216,.23]);back=smooth_interp(y,yc,[-.41,-.45,-.447,-.431,-.41,-.39,-.38,-.366,-.36]);center=(front+back)/2;depth=(front-back)/2
 q=np.clip(np.abs((z-center)/depth),0,.9999)
 return width*np.power(1-np.power(q,2.5),1/2.5)
def body_normal(p,sign):
 y,z=p[...,1],p[...,2];e=1e-4;dy=(body_surface(y+e,z)-body_surface(y-e,z))/(2*e);dz=(body_surface(y,z+e)-body_surface(y,z-e))/(2*e)
 n=np.stack([np.ones_like(y)*sign,-dy,-dz],axis=-1);return n/np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-12)
def clip_pair(tris,mats,field):
 values=field(tris); common={}
 for v,value in zip(tris.reshape(-1,11),values.reshape(-1)):common.setdefault(key(v[:3]),float(value))
 values=np.array([common[key(v[:3])] for v in tris.reshape(-1,11)]).reshape(-1,3);intersection_cache={}
 pos=np.all(values>=0,axis=1);neg=np.all(values<=0,axis=1)
 A=list(tris[neg]);AM=list(mats[neg]);B=list(tris[pos&~neg]);BM=list(mats[pos&~neg]);cnt=0
 for t,mt,s in zip(tris[~(pos|neg)],mats[~(pos|neg)],values[~(pos|neg)]):
  for keep,arr,mm in [(False,A,AM),(True,B,BM)]:
   vv=[]
   for j in range(3):
    k=(j+1)%3;a=t[j];b=t[k];sa=s[j];sb=s[k];ia=sa>=0 if keep else sa<=0;ib=sb>=0 if keep else sb<=0
    if ia:vv.append(a)
    if ia!=ib:
     u=float(sa/(sa-sb));v=a+(b-a)*u;edge=tuple(sorted((key(a[:3]),key(b[:3]))));v[:3]=intersection_cache.setdefault(edge,v[:3].copy());v[3:6]/=max(np.linalg.norm(v[3:6]),1e-12);vv.append(v)
   for j in range(1,len(vv)-1):
    tri=np.array([vv[0],vv[j],vv[j+1]])
    if np.linalg.norm(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))>1e-13:arr.append(tri);mm.append(mt)
  cnt+=1
 return (np.array(A),np.array(AM)),(np.array(B),np.array(BM)),cnt

def key(p):return tuple(np.rint(p*1e9).astype(np.int64))
def boundary_loops(tris):
 ed={};verts={}
 for t in tris:
  ks=[key(v[:3]) for v in t]
  for k,v in zip(ks,t):verts[k]=v
  for i in range(3):
   a,b=ks[i],ks[(i+1)%3];ke=tuple(sorted((a,b)))
   if ke in ed:ed[ke]=None
   else:ed[ke]=(a,b)
 edges=[e for e in ed.values() if e is not None];nxt={a:b for a,b in edges};loops=[]
 while nxt:
  start=next(iter(nxt));cur=start;ids=[]
  while cur in nxt:
   ids.append(cur);cur=nxt.pop(cur)
   if cur==start:break
  if cur!=start:raise ValueError('Non-loop boundary: '+str(len(ids)))
  if len(ids)>2:loops.append(np.array([verts[k] for k in ids]))
 return loops

def cap_arm(tris,mats,sign,body):
 loops=boundary_loops(tris);caps=[];meta=[]
 if body:
  tris=tris.copy();border=np.concatenate([l[:,:3] for l in loops]);flat=tris.reshape(-1,11)
  mask=(flat[:,0]*sign>.29)&(flat[:,1]<-.08)&(flat[:,1]>-.66)
  ids=np.flatnonzero(mask);maxshift=0.
  for start in range(0,len(ids),512):
   ix=ids[start:start+512];p=flat[ix,:3];d=np.sqrt(np.min(np.sum((p[:,None,:]-border[None,:,:])**2,axis=2),axis=1));w=(1-ss(.006,.045,d))*(1-ss(-.25,-.18,p[:,1]))
   target=sign*body_surface(p[:,1],p[:,2]);dx=(target-p[:,0])*w;flat[ix,0]+=dx;maxshift=max(maxshift,float(np.max(np.abs(dx))))
  # Recompute normals only in this hidden junction neighborhood.
  sums={}
  for t in tris:
   nn=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])
   for v in t:sums[key(v[:3])]=sums.get(key(v[:3]),np.zeros(3))+nn
  analytic=body_normal(flat[ids,:3],sign)
  for ix,target_n in zip(ids,analytic):
   v=flat[ix];d=np.min(np.linalg.norm(border-v[:3],axis=1))
   if d<.06:
    nn=target_n;w=(1-ss(.015,.06,d))*(1-ss(-.25,-.18,v[1]));v[3:6]=v[3:6]*(1-w)+nn*w;v[3:6]/=max(np.linalg.norm(v[3:6]),1e-12)
  loops=boundary_loops(tris)
  print('local torso junction reconstruction max x shift',maxshift,flush=True)

 for loop in loops:
  # Reverse the existing exterior boundary winding for a closed patch.
  ring=loop[::-1].copy();p=ring[:,:3];center=p.mean(0)
  # Convex body side / full rounded arm underside. They overlap internally
  # rather than removing any volume from the visible body or arm.
  center[0]=sign*(float(arm_cut(center[1]))+(.018 if body else -.058))
  center[1]=float((p[:,1].min()+p[:,1].max())*.5)
  center[2]=float((p[:,2].min()+p[:,2].max())*.5)
  cs=color(ring[:,6:8]);fallback=np.median(cs[(cs[:,1]>.68*cs[:,0])],axis=0) if np.any(cs[:,1]>.68*cs[:,0]) else np.array([1,.87,.25])
  # Original boundary colors; yellow underside never inherits orange shorts.
  if not body:cs=np.where((cs[:,1]>.68*cs[:,0])[:,None],cs,fallback)
  prev=ring.copy();prev[:,8:11]=lin(cs)
  allrings=[prev]
  for k in range(1,17):
   t=k/17;r=1-t;nr=ring.copy();nr[:,:3]=p*r+center*t
   # A shallow domed profile, not a planar cut cap.
   nr[:,0]=sign*(arm_cut(nr[:,1])-.058*(1-r*r))
   nr[:,0]+=r*r*(p[:,0]-sign*arm_cut(p[:,1]))
   if body:nr[:,0]=sign*body_surface(nr[:,1],nr[:,2])+(p[:,0]-sign*body_surface(p[:,1],p[:,2]))*r**4
   target=np.tile(fallback,(len(nr),1))
   if body:
    orange=np.array([.94,.39,.08]);tcol=ss(-.475,-.455,nr[:,1]);target=orange[None,:]*(1-tcol[:,None])+fallback[None,:]*tcol[:,None]
   nc=cs*r+target*(1-r);nr[:,8:11]=lin(nc)
   nr[:,6:8]=0;allrings.append(nr)
  N=len(ring)
  for a,b1 in zip(allrings[:-1],allrings[1:]):
   for j in range(N):
    k=(j+1)%N;caps.extend([np.array([a[j],a[k],b1[k]]),np.array([a[j],b1[k],b1[j]])])
  cv=ring[0].copy();cv[:3]=center;cv[0]=sign*(float(body_surface(center[1],center[2])) if body else float(arm_cut(center[1]))-.058);cv[8:11]=lin(fallback)
  for j in range(N):caps.append(np.array([allrings[-1][j],allrings[-1][(j+1)%N],cv]))
  meta.append({'boundary_vertices':N,'new_center':center.tolist(),'body_side':body,'local_connection_max_shift':maxshift if body else 0.})
 # Smooth patch normals, with source seam normal preserved at its boundary.
 if caps:
  c=np.array(caps);ns={}
  for t in c:
   n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])
   for v in t:ns[key(v[:3])]=ns.get(key(v[:3]),np.zeros(3))+n
  seam={key(v[:3]):v[3:6] for l in loops for v in l}
  analytic=body_normal(c[:,:,:3],sign) if body else np.zeros_like(c[:,:,:3])
  for t,tn in zip(c,analytic):
   for v,vn in zip(t,tn):
    n=vn if body and v[1]<-.23 else seam.get(key(v[:3]),ns[key(v[:3])]);v[3:6]=n/max(np.linalg.norm(n),1e-12)
  tris=np.concatenate([tris,c]);mats=np.concatenate([mats,np.full(len(c),2)])
 return tris,mats,meta

# GLB builder reuses original embedded image bytes and material definitions,
# but prunes obsolete geometry. Independent parts share the exact world frame.
def write_glb(path,parts):
 doc={k:copy.deepcopy(g[k]) for k in ['asset','materials','textures','samplers','extensionsUsed','extensionsRequired'] if k in g};data=bytearray();doc.update(bufferViews=[],accessors=[],images=[],meshes=[],nodes=[],scenes=[{'nodes':[]}],scene=0,buffers=[{}])
 doc['materials'].append({'name':'Authored_hidden_surface','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':.78},'doubleSided':False})
 def buffer(b):
  while len(data)%4:data.append(0)
  i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(b)});data.extend(b);return i
 for img in g.get('images',[]):
  v=g['bufferViews'][img['bufferView']];q=copy.deepcopy(img);q['bufferView']=buffer(raw[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);doc['images'].append(q)
 def add(a,typ,component):
  v=buffer(a.tobytes());i=len(doc['accessors']);q={'bufferView':v,'componentType':component,'count':len(a),'type':typ}
  if typ=='VEC3':q.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  doc['accessors'].append(q);return i
 for name,ts,ms in parts:
  prim=[]
  for mi in np.unique(ms):
   a=ts[ms==mi].reshape(-1,11);unique,ix,inv=np.unique(a.astype('<f4'),axis=0,return_index=True,return_inverse=True);a=a[ix]
   at={}
   for label,sl,typ in [('POSITION',slice(0,3),'VEC3'),('NORMAL',slice(3,6),'VEC3'),('TEXCOORD_0',slice(6,8),'VEC2')]:at[label]=add(a[:,sl].astype('<f4'),typ,5126)
   if mi==2:at['COLOR_0']=add(a[:,8:11].astype('<f4'),'VEC3',5126)
   prim.append({'attributes':at,'indices':add(inv.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':int(mi),'mode':4})
  i=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':prim});doc['nodes'].append({'name':name,'mesh':i,'extras':{'part':name,'static_only':True}});doc['scenes'][0]['nodes'].append(i)
 doc['buffers'][0]['byteLength']=len(data);doc['extras']={'lulu':{'revision':REV,'base':'official-v1','source_sha256':SHA,'status':'Static modular study; no skeleton or animation','method':'Preserved original exterior; independently authored curved hidden surfaces'}}
 j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data+=b'\0'*((-len(data))%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)

def skin_field(v):
 p=v[...,:3];fallback=(v[...,1]>-.465).astype(float);out=[]
 for pp,fb in zip(p.reshape(-1,3),fallback.reshape(-1)):
  out.append(skin_lookup.get(tuple(np.rint(pp*1e6).astype(np.int64)),float(fb)))
 return np.array(out).reshape(fallback.shape)-.5

# Measure a smooth waist interface from the actual orange/yellow transition.
# A single continuous cut curve avoids hundreds of texture-noise holes.
_base=T.reshape(-1,11);_c=color(_base[:,6:8]);_p=_base[:,:3];_sel=(_p[:,1]>-.54)&(_p[:,1]<-.40)&(_c[:,1]<.68*_c[:,0]);_p=_p[_sel];_angles=np.arctan2(_p[:,2]+.08,_p[:,0]);_wa=[];_wy=[]
for j in range(64):
 lo=-math.pi+j*2*math.pi/64;hi=lo+2*math.pi/64;vs=_p[(_angles>=lo)&(_angles<hi),1]
 if len(vs)>3:_wa.append((lo+hi)/2);_wy.append(np.quantile(vs,.96)+.01)
_wa=np.array(_wa);_design=np.stack([np.ones_like(_wa),np.cos(_wa),np.sin(_wa),np.cos(2*_wa),np.sin(2*_wa)],axis=1);WAIST=np.linalg.lstsq(_design,np.array(_wy),rcond=None)[0]
print('measured waist coefficients',WAIST.tolist(),flush=True)
def waist_field(v):
 th=np.arctan2(v[...,2]+.08,v[...,0]);terms=np.stack([np.ones_like(th),np.cos(th),np.sin(th),np.cos(2*th),np.sin(2*th)],axis=-1)
 return v[...,1]-terms@WAIST
def smooth_caps(tris,mats,depth,kind='skin'):
 loops=boundary_loops(tris);new=[]
 for loop in loops:
  ring=loop[::-1].copy();p=ring[:,:3];center=p.mean(0);center[1]+=depth
  cc=color(ring[:,6:8]);fallback=np.median(cc,axis=0)
  if kind=='skin':fallback=np.array([1.,.91,.34]);cc=np.tile(fallback,(len(ring),1))
  prev=ring.copy();prev[:,8:11]=lin(cc);N=len(ring)
  cx=(p[:,0].max()+p[:,0].min())/2;cz=(p[:,2].max()+p[:,2].min())/2;rx=max(np.ptp(p[:,0])/2,.001);rz=max(np.ptp(p[:,2])/2,.001);angles=np.arctan2((p[:,2]-cz)/rz,(p[:,0]-cx)/rx)
  # Preserve cyclic boundary order in hidden ellipsoidal caps. Direct radial
  # angles can double back along a mesh boundary and collapse whole strips.
  q=np.stack([(p[:,0]-cx)/rx,(p[:,2]-cz)/rz],axis=1)
  distance=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
  orientation=1 if np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))>0 else -1
  angles=angles[0]+orientation*2*math.pi*np.concatenate([[0],np.cumsum(distance[:-1])])/max(distance.sum(),1e-12)
  # Full volumetric hidden extensions, tapered towards a rounded pole.
  for k in range(1,21):
   theta=k/21*math.pi/2;r=math.cos(theta);nr=ring.copy();nr[:,:3]=p*r+center*(1-r);nr[:,1]=p[:,1].mean()+(p[:,1]-p[:,1].mean())*r*r+depth*math.sin(theta)
   blend=ss(0,.30,k/21)
   if kind=='skin':
    nr[:,0]=nr[:,0]*(1-blend)+(cx+rx*r*np.cos(angles))*blend;nr[:,2]=nr[:,2]*(1-blend)+(cz+rz*r*np.sin(angles))*blend;nr[:,1]=nr[:,1]*(1-blend)+(p[:,1].mean()+depth*math.sin(theta))*blend
   nr[:,6:8]=0;nr[:,8:11]=lin(cc*r+fallback*(1-r))
   for j in range(N):
    q=(j+1)%N;new.extend([np.array([prev[j],prev[q],nr[q]]),np.array([prev[j],nr[q],nr[j]])])
   prev=nr
  cv=ring[0].copy();cv[:3]=center;cv[8:11]=lin(fallback)
  for j in range(N):new.append(np.array([prev[j],prev[(j+1)%N],cv]))
 if not new:return tris,mats
 new=np.array(new);sums={}
 for t in new:
  n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])
  for v in t:sums[key(v[:3])]=sums.get(key(v[:3]),np.zeros(3))+n
 for t in new:
  for v in t:
   n=sums[key(v[:3])];v[3:6]=n/max(np.linalg.norm(n),1e-12)
 return np.concatenate([tris,new]),np.concatenate([mats,np.full(len(new),2)])

def shorts_shell(tris,mats):
 # Retain the whole visible shorts surface. Add a thin interior lining and
 # rounded-edge bridges at waist / leg openings, instead of solid flat caps.
 loops=boundary_loops(tris);thickness=.009
 normal_map={}
 for v in tris.reshape(-1,11):normal_map[key(v[:3])]=normal_map.get(key(v[:3]),np.zeros(3))+v[3:6]
 for k,n in normal_map.items():normal_map[k]=n/max(np.linalg.norm(n),1e-12)
 inner=tris[:,::-1].copy()
 for v in inner.reshape(-1,11):v[:3]-=normal_map[key(v[:3])]*thickness;v[3:6]*=-1
 bridges=[]
 for loop in loops:
  for i in range(len(loop)):
   a,b=loop[i],loop[(i+1)%len(loop)];ai=a.copy();bi=b.copy();ai[:3]-=normal_map[key(ai[:3])]*thickness;bi[:3]-=normal_map[key(bi[:3])]*thickness
   bridges.extend([np.array([b,a,ai]),np.array([b,ai,bi])])
 bridges=np.array(bridges)
 for t in bridges:
  n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=max(np.linalg.norm(n),1e-12);t[:,3:6]=n
 return np.concatenate([tris,inner,bridges]),np.concatenate([mats,mats,np.full(len(bridges),0)])

def main_components(ts,number):
 parent=np.arange(len(ts));owner={}
 def root(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return int(a)
 for i,t in enumerate(ts):
  for v in t:
   k=key(v[:3])
   if k in owner:
    a,b=root(i),root(owner[k])
    if a!=b:parent[a]=b
   else:owner[k]=i
 labels=np.array([root(i) for i in range(len(ts))]);area=np.linalg.norm(np.cross(ts[:,1,:3]-ts[:,0,:3],ts[:,2,:3]-ts[:,0,:3]),axis=1);totals={}
 for label,a in zip(labels,area):totals[label]=totals.get(label,0.)+a
 largest=sorted(totals,key=totals.get,reverse=True)[:number]
 print('surface component areas',sorted(totals.values(),reverse=True)[:12],flush=True)
 return np.isin(labels,largest)
def decompose_core(core):
 lower,head,_=clip_pair(*core,lambda v:v[...,1]+.08)
 head,orange,_=clip_pair(*head,lambda v:v[...,1]-.729)
 head=smooth_caps(*head,-.012,'skin');orange=smooth_caps(*orange,-.018,'orange')
 # Exact-color contact threshold separates the original feet from the shorts.
 lower,feet,_=clip_pair(*lower,lambda v:np.minimum(skin_field(v),-.69-v[...,1]))
 keep=main_components(feet[0],2);lower=(np.concatenate([lower[0],feet[0][~keep]]),np.concatenate([lower[1],feet[1][~keep]]));feet=(feet[0][keep],feet[1][keep])
 legs=[]
 for sign,name in [(-1,'Leg_R'),(1,'Leg_L')]:
  mask=feet[0][:,:,0].mean(1)*sign>0
  leg=smooth_caps(feet[0][mask],feet[1][mask],.22,'skin');legs.append((name,*leg))
 pants,torso,_=clip_pair(*lower,waist_field)
 keep=main_components(torso[0],1);pants=(np.concatenate([pants[0],torso[0][~keep]]),np.concatenate([pants[1],torso[1][~keep]]));torso=(torso[0][keep],torso[1][keep])
 # Close neck separately with a shallow inward overlap. Complete pelvis below.
 loops=boundary_loops(torso[0]);top=[l for l in loops if l[:,1].mean()>-.2];bottom=[l for l in loops if l[:,1].mean()<=-.2]
 # General cap function can select depth based on each opening's elevation.
 torso=close_torso(torso,top,bottom)
 pants=shorts_shell(*pants)
 return [('Head',*head),('Orange',*orange),('Body',*torso),('Shorts',*pants)]+legs

def close_torso(torso,top,bottom):
 # Close one opening at a time by extracting generated caps from a temporary
 # boundary-only patch. The visible source skin never receives a planar cap.
 tris,mats=torso
 for wanted,depth in [(top,.015),(bottom,-.17)]:
  for loop in wanted:
   # synthetic fan has opposite winding to closure; removed after cap creation
   center=loop[:,:3].mean(0);cv=loop[0].copy();cv[:3]=center;fan=np.array([[loop[j],loop[(j+1)%len(loop)],cv] for j in range(len(loop))])
   filled,fm=smooth_caps(fan,np.zeros(len(fan),dtype=int),depth,'skin')
   caps=filled[len(fan):];cm=fm[len(fan):];tris=np.concatenate([tris,caps]);mats=np.concatenate([mats,cm])
 return tris,mats

def clean_part(ts,ms):
 ts=ts.copy();flat=ts[:,:,:3].reshape(-1,3);_,first,inv=np.unique(np.round(flat,6),axis=0,return_index=True,return_inverse=True);ts[:,:,:3]=flat[first][inv].reshape(-1,3,3);f=inv.reshape(-1,3)
 valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]);ts=ts[valid];ms=ms[valid];f=f[valid]
 groups={};keep=np.ones(len(f),dtype=bool)
 for i,face in enumerate(f):
  k=tuple(sorted(face))
  if k not in groups:groups[k]=i;continue
  j=groups[k];a=f[j];b=face
  same=any(np.array_equal(np.roll(a,n),b) for n in range(3))
  keep[i]=False
  if not same:keep[j]=False
 return ts[keep],ms[keep]
remaining=(T,M);parts=[];meta=[]
for sign,name in [(-1,'Arm_R')]+([] if MODE=='one-arm' else [(1,'Arm_L')]):
 remaining,arm,count=clip_pair(*remaining,lambda v:arm_field(v,sign))
 # Close torso immediately; later cuts can partition the reconstructed side.
 bt,bm,bmeta=cap_arm(*remaining,sign,True);at,am,ameta=cap_arm(*arm,sign,False)
 remaining=(bt,bm);parts.append((name,at,am));meta.append({'part':name,'split_source_triangles':count,'body_caps':bmeta,'arm_caps':ameta})
if MODE=='one-arm':parts.insert(0,('Body_Head_Legs_Shorts',*remaining))
else:parts=decompose_core(remaining)+parts
for name,t,m in parts:
 if name=='Body':
  mask=(m==2)[:,None]&(t[:,:,1]<-.38);t[:,:,8:11][mask]=lin(np.array([1.,.91,.34]))
parts=[(n,*clean_part(t,m)) for n,t,m in parts]
write_glb(OUT/'lulu-assembled.glb',parts)
for name,ts,ms in parts:write_glb(OUT/(name+'.glb'),[(name,ts,ms)])
report={'revision':REV,'mode':MODE,'source':str(source.relative_to(R)),'source_sha256':SHA,'original_surface_weld_max_delta':WELD_DELTA,'original_exterior_removed':False,'local_reconstruction':'Torso x/normal adjustments confined to formerly fused arm-side junction; head, arms and other original exterior positions preserved','parts':[{'name':n,'triangles':len(t),'new_hidden_triangles':int(np.sum(m==2))} for n,t,m in parts],'closures':meta,'bones':0,'status':'Awaiting actual visual inspection; not art accepted'}
(REPORT/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
