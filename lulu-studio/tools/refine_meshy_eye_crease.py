"""Conservative area-weighted local surface fairing of lower/inner eye skin.

Starts from immutable no-tail-2; all X/Y, blue/black eye faces and central core, textures, topology,
non-local positions and normals stay fixed. No global head surface projection.
"""
import argparse,hashlib,heapq,io,json,struct
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor,smoothstep
BASE=R/'review/meshy-eye-crease-baseline/lulu-meshy-notail.glb'

def prepare():
 source,g,raw=read_glb(BASE);pr=g['meshes'][0]['primitives'][0]
 p0=accessor(g,raw,pr['attributes']['POSITION']).copy();uv=accessor(g,raw,pr['attributes']['TEXCOORD_0']).copy()
 tri=np.concatenate([accessor(g,raw,q['indices']).reshape(-1,3) for q in g['meshes'][0]['primitives']])
 v=g['bufferViews'][g['images'][0]['bufferView']];im=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=im.shape[:2]
 c=im[(uv[:,1]*(h-1)).astype(int).clip(0,h-1),(uv[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
 _,inverse=np.unique(np.round(p0,6),axis=0,return_inverse=True);count=np.bincount(inverse);N=len(count)
 average=lambda a:np.stack([np.bincount(inverse,weights=a[:,k])/count for k in range(a.shape[1])],axis=1)
 U=average(p0);C=average(c);ut=inverse[tri]
 area=np.linalg.norm(np.cross(U[ut[:,1]]-U[ut[:,0]],U[ut[:,2]]-U[ut[:,0]]),axis=1)
 mass=np.zeros(N)
 for k in range(3):np.add.at(mass,ut[:,k],area/3)
 x,y,z=U.T
 eye=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.070)**2)
 skin=(C[:,0]>155)&(C[:,1]>140)&(C[:,2]<170)
 dark_eye=(C.mean(1)<165)|((C[:,2]-C[:,0])>18)
 eye_pin=(eye<1.18)&(z>.14)&dark_eye
 # Also protect the full central face and a soft surrounding margin.
 eye_pin|=(eye<.80)&(z>.14)
 edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
 local=(abs(x)>.07)&(abs(x)<.46)&(y>.34)&(y<.64)&(z>.10)
 local_edges=edges[local[edges[:,0]]&local[edges[:,1]]]
 adj={int(i):[] for i in np.flatnonzero(local)}
 for a,b in local_edges:
  length=float(np.linalg.norm(U[a]-U[b]));adj[int(a)].append((int(b),length));adj[int(b)].append((int(a),length))
 distance=np.full(N,np.inf);queue=[]
 for i in np.flatnonzero(eye_pin&local):distance[i]=0;heapq.heappush(queue,(0,int(i)))
 while queue:
  d,i=heapq.heappop(queue)
  if d!=distance[i] or d>.12:continue
  for j,length in adj[i]:
   nd=d+length
   if nd<distance[j]:distance[j]=nd;heapq.heappush(queue,(nd,j))
 lo=np.sqrt(((abs(x)-.248)/.13)**2+((y-.461)/.056)**2)
 co=np.sqrt(((abs(x)-.164)/.069)**2+((y-.499)/.066)**2)
 weight=np.maximum(smoothstep((1.18-lo)/.50),smoothstep((1.10-co)/.48))
 weight*=smoothstep(distance/.016)*smoothstep((z-.14)/.055)*smoothstep((.545-y)/.04)
 weight[eye_pin|~local]=0
 return source,g,raw,pr,p0,tri,U,inverse,mass,weight,eye_pin

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--radius',type=float,default=.024);parser.add_argument('--limit',type=float,default=.008);parser.add_argument('--strength',type=float,default=.40);parser.add_argument('--revision',default='crease-3');args=parser.parse_args()
 source,g,raw,pr,p0,tri,U,inv,mass,weight,pin=prepare();ids=np.flatnonzero(weight>1e-7)
 local=np.flatnonzero((abs(U[:,0])>.035)&(abs(U[:,0])<.51)&(U[:,1]>.29)&(U[:,1]<.68)&(U[:,2]>.11))
 target=np.zeros(len(U));h=args.radius
 for i in ids:
  d=U[local]-U[i];keep=(np.sum(d[:,:2]**2,axis=1)<(3*h)**2)&(abs(d[:,2])<.16)
  j=local[keep];d=d[keep];X=d[:,0]/h;Y=d[:,1]/h
  A=np.c_[np.ones(len(j)),X,Y,X*X,X*Y,Y*Y]
  w=mass[j]*np.exp(-.5*(X*X+Y*Y)) * np.exp(-.5*(d[:,2]/.075)**2)
  w/=max(w.max(),1e-20)
  lhs=A.T@(A*w[:,None])+np.eye(6)*1e-7
  rhs=A.T@(d[:,2]*w)
  target[i]=np.linalg.solve(lhs,rhs)[0]
 shift=args.limit*np.tanh(target/args.limit)*weight*args.strength
 delta=np.zeros_like(p0);delta[:,2]=shift[inv]
 binary=bytearray(raw);p=accessor(g,binary,pr['attributes']['POSITION']);norm=accessor(g,binary,pr['attributes']['NORMAL']);p[:]=p0+delta;changed=np.any(p!=p0,axis=1)
 face=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 sums=np.zeros((len(U),3))
 for k in range(3):np.add.at(sums,inv[tri[:,k]],face)
 sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-12)[:,None];norm[changed]=sums[inv][changed]
 g['accessors'][pr['attributes']['POSITION']]['min']=p.min(0).tolist();g['accessors'][pr['attributes']['POSITION']]['max']=p.max(0).tolist()
 js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
 out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
 (R/'public/models/lulu-meshy-crease.glb').write_bytes(out)
 np.savez(R/'review/meshy-eye-crease-delta.npz',delta=delta,weight=weight[inv],pin=pin[inv])
 report={'revision':args.revision,'source_sha256':hashlib.sha256(source).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'radius':args.radius,'limit':args.limit,'strength':args.strength,'changed_vertices':int(changed.sum()),'max_axis_delta':np.abs(delta).max(0).tolist(),'positive_z_vertices':int((delta[:,2]>0).sum()),'negative_z_vertices':int((delta[:,2]<0).sum()),'blue_black_eye_and_core_pinned':bool(np.all(delta[pin[inv]]==0)),'method':'area weighted local quadratic fairing; depth only; geodesic feather from pinned blue/black eye and central core'}
 (R/'review/meshy-eye-crease-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
