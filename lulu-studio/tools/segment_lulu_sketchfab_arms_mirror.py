from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-sketchfab-arm-down-20261019'
v=np.load(R/'review/lulu-sketchfab-color-20261019/baseline/geometry.npz');p=v['p'];u,inv=np.unique(p,axis=0,return_inverse=True);f=inv[v['f']];n=np.stack([np.bincount(inv,weights=v['n'][:,a])/np.bincount(inv) for a in range(3)],1);n/=np.linalg.norm(n,axis=1)[:,None]
x,y,z=u.T;t=np.radians(8.7);c,s=np.cos(t),np.sin(t);hx=c*x+s*(y-.72);hy=-s*x+c*(y-.72)+.72
# Reference half has no arm at this depth. Two frames: torso and tilted head.
def envelope(coord,side,roi):
 xx,yy,zz=coord.T;src=(xx*side<-.03)&roi;ids=np.where(src)[0];U=coord[ids];step=.002
 low=np.array([-.03,-.29]);shape=(560,295);yi=np.clip(((U[:,1]-low[0])/step).astype(int),0,shape[0]-1);zi=np.clip(((U[:,2]-low[1])/step).astype(int),0,shape[1]-1)
 val=np.full(shape,np.nan);indices=np.full(shape,-1,int)
 # Maximum projected cross section, with provenance for mirror shells.
 for a,b,pt,i in zip(yi,zi,U,ids):
  d=-side*pt[0]
  if np.isnan(val[a,b]) or d>val[a,b]:val[a,b]=d;indices[a,b]=i
 qy=np.clip(((yy-low[0])/step).astype(int),0,shape[0]-1);qz=np.clip(((zz-low[1])/step).astype(int),0,shape[1]-1)
 best=np.full(len(coord),np.nan)
 # Adjacent raster cells avoid spurious holes from source triangulation.
 for dy in [-2,-1,0,1,2]:
  for dz in [-2,-1,0,1,2]:
   vv=val[np.clip(qy+dy,0,shape[0]-1),np.clip(qz+dz,0,shape[1]-1)]
   best=np.fmax(best,vv)
 return best
raw=u.copy();head=np.c_[hx,hy,z]
left_raw=envelope(raw,1,(z>-.10)&(y>.28)&(y<.68));left_head=envelope(head,1,(z>.04)&(hy>.4)&(hy<.80))
# Convert expected head surface to raw X; y uses the queried point's head frame.
head_x=c*left_head-s*(hy-.72)
a=np.clip((y-.48)/.10,0,1);expected=left_raw*(1-a)+head_x*a
expected=np.where(np.isnan(expected),np.where(a>.5,head_x,left_raw),expected)
leftroi=(x>.075)&(y>.35)&(y<.605)&(z>-.045)
left=leftroi & (np.isnan(expected)|(x>expected+.0025))
right_exp=envelope(raw,-1,(z<.045)&(y>.13)&(y<.53));rightroi=(x<-.15)&(y>.155)&(y<.49)&(z<.045)
right=rightroi&(np.isnan(right_exp)|(-x>right_exp+.0025))
labels=np.zeros(len(u),np.uint8);labels[left]=1;labels[right]=2
fl=labels[f];face=np.zeros(len(f),np.uint8)
for part in [1,2]:face[(fl==part).sum(1)>=2]=part
# Keep only largest connected surface component for each arm; eliminate tiny
# residual normal/asymmetry islands. This is classification, not a mesh edit.
for part in [1,2]:
 ids=np.where(face==part)[0];ff=f[ids];parent=np.arange(len(u))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for aa,bb,cc in ff:
  aa=root(aa);parent[root(bb)]=aa;parent[root(cc)]=aa
 groups=np.array([root(i) for i in ff[:,0]]);big=np.bincount(groups).argmax();face[ids[groups!=big]]=0
out=D/'baseline/arm-labels-mirror-r01.npz';assert not out.exists();np.savez_compressed(out,u=u,inv=inv,n=n,labels=labels,face_labels=face,left_envelope=expected,right_envelope=right_exp)
print(np.bincount(face));print(out)
