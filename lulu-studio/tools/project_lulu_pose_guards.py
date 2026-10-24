"""Blender geometry queries: project added shells only onto intact opposite skin."""
import bpy,numpy as np,json,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-sketchfab-arm-down-20261019';d=(D/'pose-r09/lulu-arm-down.glb').read_bytes();ln=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+ln]);b=d[28+ln:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];size={'VEC3':3,'SCALAR':1,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);return np.ndarray((a['count'],size),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*dt.itemsize),dt.itemsize)).copy()
v=np.load(R/'review/lulu-sketchfab-color-20261019/baseline/geometry.npz');p=v['p'];f=v['f'];labels=np.load(D/'pose-r09/face-labels.npz')['face_labels']
trees=[]
for side in [1,-1]:
 if side==1:keep=(p[:,0]<-.055)&(p[:,2]>-.07)&(p[:,1]>.29)&(p[:,1]<.78)
 else:keep=(p[:,0]>.055)&(p[:,2]<.06)&(p[:,1]>.11)&(p[:,1]<.57)
 face=f[keep[f].all(1)&(labels==0)];P=p.copy().astype(float);P[:,0]*=-1
 if side==1:
  th=np.radians(8.7);c,s=np.cos(th),np.sin(th);hx=c*p[:,0]+s*(p[:,1]-.72);hy=-s*p[:,0]+c*(p[:,1]-.72)+.72
  mx=c*(-hx)-s*(hy-.72);my=s*(-hx)+c*(hy-.72)+.72
  blend=np.clip((p[:,1]-.45)/.16,0,1);blend=blend*blend*(3-2*blend);P[:,0]=P[:,0]*(1-blend)+mx*blend;P[:,1]=P[:,1]*(1-blend)+my*blend
 trees.append(BVHTree.FromPolygons(P.tolist(),face.tolist(),all_triangles=True))
out={}
for mi,m in enumerate(g['meshes']):
 if not m['name'].startswith('GuardShell'):continue
 pr=m['primitives'][0];P=acc(pr['attributes']['POSITION']).astype(float);N=acc(pr['attributes']['NORMAL']);F=acc(pr['indices']).reshape(-1,3);part=int(m['name'].split('_')[1]);K=(len(P)-1)//24
 if part==0:
  tree=trees[0 if P[:K,0].mean()>0 else 1]
  for j in range(K,len(P)):
   hit=tree.find_nearest(Vector(P[j]));r=1-min(1,(j//K)/24)
   if hit[0] is not None:
    fac=1-r**10;P[j]=P[j]*(1-fac)+np.array(hit[0])*fac
 else:
  line=np.array([[.242,.445,.012],[.254,.453,.10],[.212,.503,.195],[.17,.55,.237]]) if part==1 else np.array([[-.242,.433,-.065],[-.262,.355,-.09],[-.257,.28,-.132],[-.244,.215,-.176]])
  radius=.053 if part==1 else .040
  best=np.full(len(P),1e9);cent=np.zeros_like(P)
  for A,B in zip(line[:-1],line[1:]):
   V=B-A;t=np.clip((P-A)@V/(V@V),0,1);C=A+t[:,None]*V;ds=np.linalg.norm(P-C,axis=1);sel=ds<best;best[sel]=ds[sel];cent[sel]=C[sel]
  for j in range(K,len(P)):
   r=1-min(1,(j//K)/24);targetX=cent[j,0]+(-1 if part==1 else 1)*radius;P[j,0]=P[j,0]*r**8+targetX*(1-r**8)
 fn=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]);NN=np.zeros_like(P)
 for a in range(3):np.add.at(NN,F[:,a],fn)
 NN/=np.maximum(np.linalg.norm(NN,axis=1),1e-12)[:,None];NN[:K]=N[:K]
 out[str(mi)+'_p']=P.astype('<f4');out[str(mi)+'_n']=NN.astype('<f4')
np.savez_compressed(D/'pose-r09/projected-guards.npz',**out);print('PROJECTED_GUARDS',list(out))
