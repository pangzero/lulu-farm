"""Independent, reversible fold / eye-surface / tail edits based on eye-local-5."""
from pathlib import Path
import json,struct,hashlib,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
SRC=R/'review/meshy-fold-tail-baseline/lulu-meshy-eyes.glb'
d=SRC.read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);raw=d[28+n:];pr=g['meshes'][0]['primitives'][0]
def arr(b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 return np.ndarray((a['count'],sz),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*np.dtype(dt).itemsize),np.dtype(dt).itemsize))
p0=arr(raw,pr['attributes']['POSITION']).copy();n0=arr(raw,pr['attributes']['NORMAL']).copy();uv=arr(raw,pr['attributes']['TEXCOORD_0']).copy();tri=arr(raw,pr['indices']).copy().reshape(-1,3)
v=g['bufferViews'][g['images'][0]['bufferView']];im=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'))
c=im[(uv[:,1]*2047).astype(int).clip(0,2047),(uv[:,0]*2047).astype(int).clip(0,2047)].astype(float)
_,inv=np.unique(np.round(p0,6),axis=0,return_inverse=True);count=np.bincount(inv);N=len(count)
def average(a):return np.stack([np.bincount(inv,weights=a[:,k])/count for k in range(a.shape[1])],axis=1)
U=average(p0);C=average(c);ut=inv[tri];edges=np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]);edges.sort(axis=1);edges=np.unique(edges,axis=0);edges=edges[edges[:,0]!=edges[:,1]];a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]];degree=np.bincount(a,minlength=N)
def smoothstep(t):t=np.clip(t,0,1);return t*t*t*(10+t*(-15+6*t))
# Fold: local skin relaxation, with blue/black/white eye core protected.
X=(abs(U[:,0])-.265)/.135;Y=(U[:,1]-.456)/.042;q=np.sqrt(X*X+Y*Y)
skin=np.clip((C[:,1]-C[:,2]-20)/65,0,1)
fweight=smoothstep((1.2-q)/.6)*skin*smoothstep((U[:,2]-.18)/.06)
P=U.copy()
for _ in range(22):
 mean=np.stack([np.bincount(a,weights=P[b,k],minlength=N)/np.maximum(degree,1) for k in range(3)],axis=1)
 proposed=P+.6*fweight[:,None]*(mean-P)
 delta=proposed-U;delta[:,:2]=np.clip(delta[:,:2],-.004,.004);delta[:,2]=np.clip(delta[:,2],-.020,.020)
 P=U+delta
fold=(P-U)[inv]
# Eye surface: fit the existing convex eye face, without changing its frontal outline.
surface=np.zeros_like(p0);fits=[]
for side in [-1,1]:
 x,y,z=p0.T;X=(x*side-.232)/.09;Y=(y-.525)/.08;Q=np.sqrt(((x*side-.232)/.079)**2+((y-.525)/.070)**2)
 eye=(x*side>0)&(z>.15)&(Q<.98)&(c[:,2]>c[:,0]*.90)&(c[:,2]>c[:,1]*.85)
 A=np.c_[np.ones(len(p0)),X,Y,X*X,X*Y,Y*Y];coef=np.linalg.lstsq(A[eye],z[eye],rcond=None)[0]
 for _ in range(3):
  residual=A[eye]@coef-z[eye];w=1/np.maximum(1,abs(residual)/.006);coef=np.linalg.lstsq(A[eye]*w[:,None],z[eye]*w,rcond=None)[0]
 target=A@coef;weight=smoothstep((1.22-Q)/.35)*(x*side>0)*smoothstep((z-.13)/.05)
 surface[:,2]+=.012*np.tanh((target-z)/.012)*weight*.92
 fits.append(coef.tolist())
# Tail: +10% distal length, width and thickness, feathered into a fixed root.
x,y,z=U.T
lower=smoothstep((-.475-y)/.055);lateral=smoothstep((.067-abs(x-.0015))/.018);rear=smoothstep((-.446-z)/.011)
tweight=lower*lateral*rear*(y>-.62)
tailU=np.zeros_like(U);tailU[:,0]=(x-.0015)*.10*tweight;tailU[:,1]=(y+.473)*.10*tweight;tailU[:,2]=(z+.444)*.10*tweight
tail=tailU[inv]
# Repeated UV-seam positions receive the same displacement.
surface=average(surface)[inv]
parts={'fold':fold,'surface':surface,'tail':tail,'polish':fold+surface+tail}
reports={}
for name,delta in parts.items():
 binary=bytearray(raw);p=arr(binary,pr['attributes']['POSITION']);normal=arr(binary,pr['attributes']['NORMAL']);p[:]=p0+delta;changed=np.any(p!=p0,axis=1)
 face=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 sums=np.zeros((N,3),dtype=float)
 for k in range(3):np.add.at(sums,inv[tri[:,k]],face)
 length=np.linalg.norm(sums,axis=1);sums/=np.maximum(length,1e-12)[:,None];normal[changed]=sums[inv][changed]
 bounds=[p.min(0).tolist(),p.max(0).tolist()];del p,normal
 gg=json.loads(json.dumps(g));pa=gg['accessors'][pr['attributes']['POSITION']];pa['min'],pa['max']=bounds
 js=json.dumps(gg,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
 out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
 (R/f'public/models/lulu-meshy-{name}.glb').write_bytes(out)
 reports[name]={'changed_vertices':int(changed.sum()),'max_axis_displacement':np.abs(delta).max(0).tolist(),'sha256':hashlib.sha256(out).hexdigest()}
np.savez(R/'review/meshy-fold-tail-deltas.npz',fold=fold,surface=surface,tail=tail)
(R/'review/meshy-fold-tail-edit.json').write_text(json.dumps({'source_sha256':hashlib.sha256(d).hexdigest(),'eye_surface_fits':fits,'parts':reports},indent=2));print(json.dumps(reports,indent=2))
