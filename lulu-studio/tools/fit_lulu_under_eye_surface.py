"""Reconstruct the small under-eye skin in its own tangent frame.

The fixed eye and healthy surrounding skin constrain one continuous surface.
Source is the immutable modular r04, not either rejected frontal-depth study.
"""
from pathlib import Path
import json,io,hashlib,copy,argparse
import numpy as np
from PIL import Image
from lulu_patch_io import read_glb,accessor
from rebuild_lulu_under_eye import hull,smooth,write,store_accessor,R,D

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rev',default='r03');ap.add_argument('--strength',type=float,default=1);args=ap.parse_args()
 out=D/args.rev;out.mkdir(exist_ok=False);source=D/'baseline/modular-r04.glb';g,raw=read_glb(source)
 pr=g['meshes'][0]['primitives'][0];at=pr['attributes'];P=accessor(g,raw,at['POSITION']);N=accessor(g,raw,at['NORMAL']);UV=accessor(g,raw,at['TEXCOORD_0']);T=accessor(g,raw,pr['indices']).reshape(-1,3)
 v=g['bufferViews'][g['images'][0]['bufferView']];image=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=image.shape[:2];C=image[(UV[:,1]*(h-1)).astype(int),(UV[:,0]*(w-1)).astype(int)].astype(float)
 U,inv=np.unique(P,axis=0,return_inverse=True);num=len(U);x,y,z=U.T;local=(x>-.43)&(x<-.09)&(y>.39)&(y<.63)&(z>.10)
 color=((C.min(1)>160)&(C.max(1)-C.min(1)<65))|((C[:,2]>C[:,0]*.84)&(C[:,2]>C[:,1]*.84))
 pin=(np.bincount(inv,weights=(color&local[inv]).astype(int),minlength=num)>0)
 normal=np.array([-.34,.65,.68]);normal/=np.linalg.norm(normal);e1=np.array([1.,0,0]);e1-=normal*(normal@e1);e1/=np.linalg.norm(e1);e2=np.cross(normal,e1);B=np.array([e1,e2,normal]).T
 origin=np.array([-.23,.51,.31]);Q=(U-origin)@B
 H=np.flatnonzero(pin);H=H[hull(Q[H])]
 inside=np.ones(num,dtype=bool);dist=np.full(num,np.inf)
 for ia,ib in zip(H,np.roll(H,-1)):
  a=Q[ia,:2];v=Q[ib,:2]-a;d=Q[:,:2]-a;cross=v[0]*d[:,1]-v[1]*d[:,0];inside&=cross>=-1e-10
  t=np.clip(d@v/(v@v),0,1);dist=np.minimum(dist,np.linalg.norm(d-t[:,None]*v,axis=1))
 pin|=inside&local
 center=Q[H,:2].mean(0)
 # Use the normal-frame lower half; the eye and forehead are anchored.
 lower=smooth((.028-(Q[:,1]-center[1]))/.04)
 patch=smooth((.066-dist)/.025)*smooth(dist/.008)*lower
 patch[pin|~local]=0
 # Boundary samples lie outside the full-effect patch, plus the actual fixed eye.
 outer=local&~pin&(dist>.060)&(dist<.095)
 upper=local&~pin&(dist>.012)&(dist<.070)&(Q[:,1]>center[1]+.018)
 def sample(ids,cell):
  _,idx=np.unique(np.round(Q[ids,:2]/cell).astype(int),axis=0,return_index=True);return ids[idx]
 constraints=np.unique(np.r_[sample(np.flatnonzero(pin&local),.009),sample(np.flatnonzero(outer|upper),.011),H])
 a=Q[constraints,:2]/.1;b=Q[constraints,2]
 def kernel(a,b):
  r2=np.sum((a[:,None]-b[None,:])**2,axis=2);return .5*r2*np.log(np.maximum(r2,1e-20))
 poly=np.c_[np.ones(len(a)),a];mat=np.block([[kernel(a,a)+np.eye(len(a))*2e-6,poly],[poly.T,np.zeros((3,3))]])
 coef=np.linalg.solve(mat,np.r_[b,np.zeros(3)])
 ids=np.flatnonzero(patch>0);xy=Q[ids,:2]/.1;target=Q[:,2].copy();target[ids]=kernel(xy,a)@coef[:-3]+np.c_[np.ones(len(xy)),xy]@coef[-3:]
 shift=.035*np.tanh((target-Q[:,2])/.035)*patch*args.strength
 newP=P+(shift[inv,None]*normal).astype('float32');newP[pin[inv]]=P[pin[inv]]
 f0=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]);f1=np.cross(newP[T[:,1]]-newP[T[:,0]],newP[T[:,2]]-newP[T[:,0]])
 sums=np.zeros((num,3))
 for k in range(3):np.add.at(sums,inv[T[:,k]],f1)
 sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-20)[:,None]
 nw=np.minimum(patch*3,1);nw[pin]=0
 newN=N*(1-nw[inv,None])+sums[inv]*nw[inv,None];newN/=np.maximum(np.linalg.norm(newN,axis=1),1e-20)[:,None];newN[nw[inv]==0]=N[nw[inv]==0]
 a0=np.linalg.norm(f0,axis=1);a1=np.linalg.norm(f1,axis=1);valid=a0>1e-12;cos=np.sum(f0*f1,axis=1)/np.maximum(a0*a1,1e-24)
 checks={'eye_positions_exact':bool(np.array_equal(P[pin[inv]],newP[pin[inv]])),'eye_normals_exact':bool(np.array_equal(N[pin[inv]],newN[pin[inv]])),'outside_positions_exact':bool(np.array_equal(P[patch[inv]==0],newP[patch[inv]==0])),'other_side_exact':bool(np.array_equal(P[P[:,0]>0],newP[P[:,0]>0])),'bounds_exact':bool(np.array_equal(P.min(0),newP.min(0)) and np.array_equal(P.max(0),newP.max(0))),'new_degenerate':int(((a1<1e-12)&valid).sum()),'faces_rotated_over60':int(((cos<.5)&valid).sum()),'faces_rotated_over90':int(((cos<0)&valid).sum()),'min_area_ratio':float((a1[valid]/a0[valid]).min()),'changed_vertices':int(np.any(P!=newP,axis=1).sum()),'max_axis_delta':abs(newP-P).max(0).tolist(),'normal_shift_range':[float(shift.min()),float(shift.max())],'constraints':len(constraints)}
 binary=bytearray(raw);store_accessor(g,binary,at['POSITION'],newP);store_accessor(g,binary,at['NORMAL'],newN);output=out/'lulu-under-eye.glb';write(output,copy.deepcopy(g),binary)
 np.savez(out/'correction.npz',P=P,newP=newP,delta=newP-P,eye=pin[inv],weight=patch[inv],normal_weight=nw[inv],frame=B,target=target[inv])
 report={'revision':args.rev,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'method':'Constrained thin-plate skin surface in cheek tangent frame; painted eye and outer skin anchors','checks':checks,'texture_bytes_unchanged':True,'topology_unchanged':True,'candidate_only':True};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
