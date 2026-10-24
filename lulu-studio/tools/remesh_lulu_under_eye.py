"""Replace only the folded lower-eye skin patch, preserving both boundaries.
Preparation uses the immutable source. CDT runs in Blender. Finish reconstructs
surface depth and bakes source skin appearance to an independent local UV chart.
"""
import argparse,copy,hashlib,io,json,struct
import numpy as np
from PIL import Image
from lulu_patch_io import read_glb,accessor
from rebuild_lulu_under_eye import R,D,write

O=D/'r04'
def setup():
 g,raw=read_glb(D/'baseline/modular-r04.glb');pr=g['meshes'][0]['primitives'][0];at=pr['attributes']
 P=accessor(g,raw,at['POSITION']);N=accessor(g,raw,at['NORMAL']);UV=accessor(g,raw,at['TEXCOORD_0']);T=accessor(g,raw,pr['indices']).reshape(-1,3)
 U,inv=np.unique(P,axis=0,return_inverse=True);ut=inv[T]
 probe=np.load(D/'r03/correction.npz');w=probe['weight'];pin=probe['eye']
 sel=(np.mean(w[T],axis=1)>.10)&~np.any(pin[T],axis=1)
 ed=np.concatenate([ut[sel][:,[0,1]],ut[sel][:,[1,2]],ut[sel][:,[2,0]]]);edge,c=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);boundary=edge[c==1]
 adj={int(i):[] for i in np.unique(boundary)}
 for a,b in boundary:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 assert all(len(a)==2 for a in adj.values())
 loops=[];remaining=set(adj)
 while remaining:
  start=next(iter(remaining));prev=None;cur=start;loop=[]
  while cur not in loop:
   loop.append(cur);remaining.discard(cur);ns=adj[cur];nxt=ns[0] if ns[0]!=prev else ns[1];prev,cur=cur,nxt
  loops.append(np.array(loop))
 normal=np.array([-.05820866,.13193963,.98954721]);normal/=np.linalg.norm(normal);e1=np.array([1.,0,0]);e1-=normal*(normal@e1);e1/=np.linalg.norm(e1);B=np.array([e1,np.cross(normal,e1),normal]).T;origin=np.array([-.23,.50,.33]);Q=(U-origin)@B
 return g,raw,pr,P,N,UV,T,U,inv,ut,sel,boundary,loops,B,origin,Q

def inside_polygon(xy,loops,Q):
 inside=np.zeros(len(xy),dtype=bool)
 for loop in loops:
  for a,b in zip(loop,np.roll(loop,-1)):
   u,v=Q[a,:2],Q[b,:2];cross=((u[1]>xy[:,1])!=(v[1]>xy[:,1]))&(xy[:,0]<(v[0]-u[0])*(xy[:,1]-u[1])/(v[1]-u[1]+1e-30)+u[0]);inside^=cross
 return inside

def prepare():
 O.mkdir(exist_ok=False);*_,boundary,loops,B,origin,Q=setup();ids=np.unique(boundary);pos=Q[ids,:2];lo=pos.min(0);hi=pos.max(0);mapping={int(k):i for i,k in enumerate(ids)}
 gx,gy=np.meshgrid(np.arange(lo[0]+.003,hi[0],.0035),np.arange(lo[1]+.003,hi[1],.0035));grid=np.c_[gx.ravel(),gy.ravel()];keep=inside_polygon(grid,loops,Q)
 # Keep new samples away from fixed edges, to avoid thin boundary triangles.
 dist=np.full(len(grid),np.inf)
 for a,b in boundary:
  v=Q[b,:2]-Q[a,:2];d=grid-Q[a,:2];t=np.clip(d@v/(v@v),0,1);dist=np.minimum(dist,np.linalg.norm(d-t[:,None]*v,axis=1))
 grid=grid[keep&(dist>.0016)]
 data={'vertices':np.r_[pos,grid].tolist(),'edges':[[mapping[int(a)],mapping[int(b)]] for a,b in boundary],'boundary_ids':ids.tolist(),'boundary_count':len(ids),'loops':[[mapping[int(k)] for k in loop] for loop in loops]}
 (O/'cdt-input.json').write_text(json.dumps(data));print('prepared',len(pos),'boundary points;',len(grid),'interior samples')

def finish():
 g,raw,pr,P,N,UV,T,U,inv,ut,sel,boundary,loops,B,origin,Q=setup();data=json.loads((O/'cdt-input.json').read_text());cdt=json.loads((O/'cdt-output.json').read_text());xy=np.array(cdt['vertices']);faces=np.array(cdt['faces']);faces=faces[inside_polygon(xy[faces].mean(1),loops,Q)]
 # All boundary points must be preserved without intersections or merging.
 boundary_ids=np.array(data['boundary_ids']);boundary_count=len(boundary_ids);fixed={}
 for i,ids in enumerate(cdt['orig_verts']):
  old=[j for j in ids if j<boundary_count]
  if old:assert len(old)==1;fixed[i]=int(boundary_ids[old[0]])
 assert set(fixed.values())==set(boundary_ids)
 unused=set(range(len(xy)))-set(faces.ravel());assert not unused.intersection(fixed)
 # Anchors: exact boundary and immediate healthy surrounding surface. Adding
 # a one-ring just outside the cut retains the surrounding tangent direction.
 outside=T[~sel];touch=np.any(np.isin(inv[outside],boundary_ids),axis=1);anchor=np.unique(inv[outside[touch]])
 anchor=np.unique(np.r_[boundary_ids,anchor]);qq=Q[anchor,:2]/.1
 def kernel(a,b):
  r2=np.sum((a[:,None]-b[None,:])**2,axis=2);return .5*r2*np.log(np.maximum(r2,1e-20))
 poly=np.c_[np.ones(len(qq)),qq];mat=np.block([[kernel(qq,qq)+np.eye(len(qq))*1e-8,poly],[poly.T,np.zeros((3,3))]])
 coef=np.linalg.solve(mat,np.r_[Q[anchor,2],np.zeros(3)])
 def field(a):return kernel(a/.1,qq)@coef[:-3]+np.c_[np.ones(len(a)),a/.1]@coef[-3:]
 depth=field(xy);newP=np.c_[xy,depth]@B.T+origin
 for i,j in fixed.items():newP[i]=U[j]
 # Winding faces outward along the patch frame.
 cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]]);wrong=cross@B[:,2]<0;faces[wrong]=faces[wrong][:,[0,2,1]]
 cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]]);norm=np.zeros_like(newP)
 for k in range(3):np.add.at(norm,faces[:,k],cross)
 norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-20)[:,None]
 counts=np.bincount(inv);oldnorm=np.stack([np.bincount(inv,weights=N[:,i])/counts for i in range(3)],axis=1);oldnorm/=np.maximum(np.linalg.norm(oldnorm,axis=1),1e-20)[:,None]
 for i,j in fixed.items():norm[i]=oldnorm[j]
 # Bake source material layers into a local planar chart. Source triangles,
 # original atlas pixels and painted eyes are not edited.
 lo=xy.min(0)-.002;hi=xy.max(0)+.002;size=768;newUV=(xy-lo)/(hi-lo);newUV=newUV.astype('<f4')
 uvmap=np.zeros((size,size,2));zbuffer=np.full((size,size),-np.inf);covered=np.zeros((size,size),bool)
 source_faces=T[sel];sourceQ=(P-origin)@B
 for tri in source_faces:
  q=sourceQ[tri];pixel=(q[:,:2]-lo)/(hi-lo)*(size-1);a=np.maximum(np.floor(pixel.min(0)).astype(int)-1,0);b=np.minimum(np.ceil(pixel.max(0)).astype(int)+1,size-1)
  if np.any(a>b):continue
  yy,xx=np.mgrid[a[1]:b[1]+1,a[0]:b[0]+1];v=pixel[1:]-pixel[0];det=v[0,0]*v[1,1]-v[0,1]*v[1,0]
  if abs(det)<1e-12:continue
  dx=xx-pixel[0,0];dy=yy-pixel[0,1];b1=(dx*v[1,1]-dy*v[1,0])/det;b2=(dy*v[0,0]-dx*v[0,1])/det;b0=1-b1-b2;mask=(b0>=-1e-5)&(b1>=-1e-5)&(b2>=-1e-5);zz=b0*q[0,2]+b1*q[1,2]+b2*q[2,2];mask&=zz>zbuffer[yy,xx]
  vals=b0[...,None]*UV[tri[0]]+b1[...,None]*UV[tri[1]]+b2[...,None]*UV[tri[2]];uvmap[yy[mask],xx[mask]]=vals[mask];zbuffer[yy[mask],xx[mask]]=zz[mask];covered[yy[mask],xx[mask]]=True
 # Grow chart gutter and fill small raster gaps, never modifying source images.
 for _ in range(16):
  prev=covered.copy()
  for ax,step in [(0,1),(0,-1),(1,1),(1,-1)]:
   near=np.roll(prev,step,axis=ax);take=near&~covered;vals=np.roll(uvmap,step,axis=ax);uvmap[take]=vals[take];covered[take]=True
 buf=bytearray(raw);doc=copy.deepcopy(g)
 def blob(bb):
  buf.extend(b'\0'*((-len(buf))%4));idx=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(bb)});buf.extend(bb);return idx
 def acc(a,typ,component):
  idx=len(doc['accessors']);d={'bufferView':blob(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
  if typ=='VEC3':d.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  doc['accessors'].append(d);return idx
 def bake(texture_index,name):
  imgid=g['textures'][texture_index]['source'];v=g['bufferViews'][g['images'][imgid]['bufferView']];im=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGBA'));hh,ww=im.shape[:2];tx=np.clip(uvmap[...,0]*(ww-1),0,ww-1);ty=np.clip(uvmap[...,1]*(hh-1),0,hh-1);x0=tx.astype(int);y0=ty.astype(int);x1=np.minimum(x0+1,ww-1);y1=np.minimum(y0+1,hh-1);a=(tx-x0)[...,None];b=(ty-y0)[...,None];col=im[y0,x0]*(1-a)*(1-b)+im[y0,x1]*a*(1-b)+im[y1,x0]*(1-a)*b+im[y1,x1]*a*b;col=np.round(col).astype('uint8')
  stream=io.BytesIO();Image.fromarray(col).save(stream,format='PNG');(O/f'{name}.png').write_bytes(stream.getvalue());doc['images'].append({'bufferView':blob(stream.getvalue()),'mimeType':'image/png'});tex=copy.deepcopy(g['textures'][texture_index]);tex['source']=len(doc['images'])-1;doc['textures'].append(tex);return len(doc['textures'])-1
 mat=copy.deepcopy(g['materials'][0]);mat['name']='Right_UnderEye_Skin_Reconstructed';mat.pop('normalTexture',None)
 mat['pbrMetallicRoughness']['baseColorTexture']['index']=bake(0,'skin-basecolor');mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=bake(1,'skin-metal-rough');mat['extensions']['KHR_materials_specular']['specularTexture']['index']=bake(3,'skin-specular');doc['materials'].append(mat)
 doc['meshes'][0]['primitives'][0]['indices']=acc(T[~sel].astype('<u4').reshape(-1,1),'SCALAR',5125)
 attrs={'POSITION':acc(newP.astype('<f4'),'VEC3',5126),'NORMAL':acc(norm.astype('<f4'),'VEC3',5126),'TEXCOORD_0':acc(newUV,'VEC2',5126)}
 doc['meshes'][0]['primitives'].append({'attributes':attrs,'indices':acc(faces.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':len(doc['materials'])-1,'mode':4})
 output=O/'lulu-under-eye.glb';write(output,doc,buf)
 # Boundary triangle incidence must remain two after merging exact positions.
 alltri=np.r_[P[T[~sel]],newP[faces]];allpos,idx=np.unique(np.round(alltri.reshape(-1,3),6),axis=0,return_inverse=True);tt=idx.reshape(-1,3);ee=np.sort(np.r_[tt[:,[0,1]],tt[:,[1,2]],tt[:,[2,0]]],axis=1);_,cnt=np.unique(ee,axis=0,return_counts=True)
 report={'revision':'r04','method':'Local skin patch replaced by constrained triangulation, fixed eye and outer boundary; source material baked into local UV chart','source_sha256':hashlib.sha256((D/'baseline/modular-r04.glb').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'removed_skin_triangles':int(sel.sum()),'new_skin_triangles':len(faces),'new_vertices':len(newP),'boundary_vertices_preserved':len(fixed),'painted_eye_faces_removed':0,'other_parts_accessors_unchanged':True,'original_images_unchanged':True,'triangle_area_min':float(np.linalg.norm(cross,axis=1).min()/2),'head_primitive_open_edges':int((cnt==1).sum()),'head_primitive_nonmanifold_edges':int((cnt>2).sum()),'needs_visual_review':True}
 np.savez(O/'patch.npz',P=newP,N=norm,UV=newUV,T=faces,removed=sel,frame=B);(O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','finish']);args=ap.parse_args();prepare() if args.stage=='prepare' else finish()
