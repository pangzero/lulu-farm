"""Reconstruct the full 3D skin strip between fixed eye and face boundaries.

A constrained thin-plate solve replaces the curled interior surface shape.
The central/blue-black eyes and all vertices outside the connection stay fixed;
only the outer lower white margin can change depth with its frontal XY fixed.
existing mesh topology and UVs are preserved to protect the user's eye design.
"""
import argparse,hashlib,io,json,struct
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor
BASE=R/'review/meshy-eye-bridge-baseline/lulu-meshy-notail.glb'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--revision',default='bridge-5');ap.add_argument('--anchor',type=float,default=.003);args=ap.parse_args()
 data,g,raw=read_glb(BASE);pr=g['meshes'][0]['primitives'][0];p0=accessor(g,raw,pr['attributes']['POSITION']).copy();n0=accessor(g,raw,pr['attributes']['NORMAL']).copy();uv=accessor(g,raw,pr['attributes']['TEXCOORD_0']).copy()
 tri=np.concatenate([accessor(g,raw,q['indices']).reshape(-1,3) for q in g['meshes'][0]['primitives']]);body=accessor(g,raw,pr['indices']).reshape(-1,3)
 v=g['bufferViews'][g['images'][0]['bufferView']];im=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=im.shape[:2];c=im[(uv[:,1]*(h-1)).astype(int).clip(0,h-1),(uv[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
 _,first,inv=np.unique(np.round(p0,6),axis=0,return_index=True,return_inverse=True);U=p0[first].astype(float);N=len(U);ut=inv[tri]
 rawq=np.sqrt(((abs(p0[:,0])-.232)/.079)**2+((p0[:,1]-.525)/.07)**2)
 white=(rawq<1.18)&(p0[:,2]>.14)&(c[:,0]>170)&(c[:,1]>170)&(c[:,2]>170)
 eye=(rawq<1.18)&(p0[:,2]>.14)&(((c[:,2]>c[:,0]*.85)&(c[:,2]>c[:,1]*.85)) | ((rawq<.80)&(c.mean(1)<160)) | white)
 eye=np.isin(inv,np.unique(inv[eye]));white=np.isin(inv,np.unique(inv[white]))
 margin=white&(rawq>.82)&(p0[:,1]<.505)
 core=eye&~margin
 cent=p0[body].mean(1);x,y,z=cent.T;q=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.07)**2)
 patch=(q>.60)&(q<1.66)&(y<.505)&(z>.14)
 pt=inv[body[patch]];edge=np.sort(np.concatenate([pt[:,[0,1]],pt[:,[1,2]],pt[:,[2,0]]]),axis=1);edge,count=np.unique(edge,axis=0,return_counts=True);rim=np.unique(edge[count==1]);free=np.setdiff1d(np.unique(pt),np.r_[rim,np.unique(inv[core]),np.flatnonzero(U[:,1]>=.505)]);axis_free=np.ones((len(free),3));axis_free[np.isin(free,np.unique(inv[eye])),:2]=0
 # Constant rows are outside this very small physical skin patch.
 edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]]
 degree=np.bincount(a,minlength=N).astype(float);degree=np.maximum(degree,1)
 def L(v):return v-np.stack([np.bincount(a,weights=v[b,k],minlength=N)/degree for k in range(3)],axis=1)
 def LT(v):return v-np.stack([np.bincount(a,weights=(v/degree[:,None])[b,k],minlength=N) for k in range(3)],axis=1)
 rhs=-LT(L(U))[free]*axis_free
 diag=1+np.bincount(a,weights=1/(degree[b]**2),minlength=N)+args.anchor
 def mat(d):
  v=np.zeros((N,3));v[free]=d*axis_free;return (LT(L(v))+args.anchor*v)[free]*axis_free
 d=np.zeros_like(rhs);r=rhs.copy();z=r/diag[free,None];direction=z.copy();rz=(r*z).sum(0);initial=np.linalg.norm(r,axis=0)
 for iteration in range(1400):
  ad=mat(direction);alpha=rz/np.maximum((direction*ad).sum(0),1e-30);d+=direction*alpha;r-=ad*alpha
  if np.all(np.linalg.norm(r,axis=0)<np.maximum(initial*1e-6,1e-10)):break
  z=r/diag[free,None];nrz=(r*z).sum(0);direction=z+direction*(nrz/np.maximum(rz,1e-30));rz=nrz
 newU=U.copy();newU[free]+=d*axis_free
 delta=(newU-U)[inv].astype(np.float32);binary=bytearray(raw);p=accessor(g,binary,pr['attributes']['POSITION']);n=accessor(g,binary,pr['attributes']['NORMAL']);p[:]=p0+delta;changed=np.any(p!=p0,axis=1)
 face=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);normal=np.zeros((N,3))
 for k in range(3):np.add.at(normal,inv[tri[:,k]],face)
 normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-12)[:,None]
 # The fixed rims keep their source normals. Only the rebuilt strip changes.
 n[changed]=normal[inv][changed]
 pa=g['accessors'][pr['attributes']['POSITION']];pa['min']=p.min(0).tolist();pa['max']=p.max(0).tolist()
 js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
 result=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
 (R/'public/models/lulu-meshy-bridge.glb').write_bytes(result)
 free_raw=np.isin(inv,free);np.savez(R/'review/meshy-eye-connection-map.npz',free=free_raw,eye=eye,core=core,margin=margin,delta=delta,patch_faces=patch)
 report={'revision':args.revision,'method':'full 3D constrained thin plate reconstruction between fixed eye core and outer skin rims; white margin depth only; existing topology/UV retained','source_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'anchor':args.anchor,'iterations':iteration+1,'relative_residual':(np.linalg.norm(r,axis=0)/initial).tolist(),'fixed_eye_core_vertices':int(core.sum()),'white_margin_depth_only':True,'free_vertices':int(free_raw.sum()),'changed_vertices':int(changed.sum()),'max_axis_delta':np.abs(delta).max(0).tolist(),'max_displacement':float(np.linalg.norm(delta,axis=1).max()),'curvature_energy_before':float((L(U)**2).sum()),'curvature_energy_after':float((L(newU)**2).sum())}
 (R/'review/meshy-eye-connection-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
