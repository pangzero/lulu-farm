"""Rebuild only the lower/inner skin connection outside the fixed painted eyes.

Cut two small crescent patches from no-tail-2, retain both original rims, and
replace the folded interior with closed continuous interpolating surfaces.
"""
import argparse,hashlib,io,json,struct
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor
from remove_meshy_tail import triangulate_polygon,cross2
BASE=R/'review/meshy-eye-bridge-baseline/lulu-meshy-notail.glb'

def kernel(a,b):
 r2=np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)
 return .5*r2*np.log(np.maximum(r2,1e-22))

def interpolator(xy,values):
 origin=xy.mean(0);scale=.08;q=(xy-origin)/scale
 P=np.c_[np.ones(len(q)),q]
 A=np.block([[kernel(q,q),P],[P.T,np.zeros((3,3))]])
 coef=np.linalg.lstsq(A,np.r_[values,np.zeros((3,values.shape[1]))],rcond=1e-12)[0]
 def evaluate(points):
  pp=(np.atleast_2d(points)-origin)/scale
  return kernel(pp,q)@coef[:-3]+np.c_[np.ones(len(pp)),pp]@coef[-3:]
 return evaluate

def loops_from_edges(edges):
 ids,degree=np.unique(edges,return_counts=True);assert np.all(degree==2),'Cut rim has a branch'
 adj={int(i):[] for i in ids}
 for a,b in edges:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 unseen=set(map(int,ids));loops=[]
 while unseen:
  start=next(iter(unseen));loop=[start];prev=-1;i=start
  while True:
   j=next(v for v in adj[i] if v!=prev)
   if j==start:break
   loop.append(j);prev,i=i,j
  unseen-=set(loop);loops.append(np.array(loop))
 return loops

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--revision',default='bridge-1');args=ap.parse_args()
 data,g,raw=read_glb(BASE);prims=g['meshes'][0]['primitives'];pr=prims[0]
 p0=accessor(g,raw,pr['attributes']['POSITION']).copy();n0=accessor(g,raw,pr['attributes']['NORMAL']).copy();uv0=accessor(g,raw,pr['attributes']['TEXCOORD_0']).copy()
 tris=[accessor(g,raw,q['indices']).reshape(-1,3).copy() for q in prims];t0=tris[0]
 v=g['bufferViews'][g['images'][0]['bufferView']];im=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=im.shape[:2]
 c=im[(uv0[:,1]*(h-1)).astype(int).clip(0,h-1),(uv0[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
 _,first,inv=np.unique(np.round(p0,6),axis=0,return_index=True,return_inverse=True);U=p0[first];C=c[first];ut=inv[t0]
 eye=(abs(p0[:,0])>.10)&(abs(p0[:,0])<.37)&(p0[:,1]>.43)&(p0[:,1]<.62)&(p0[:,2]>.14)&(((c[:,2]>c[:,0]*.85)&(c[:,2]>c[:,1]*.85))|(c.mean(1)<110))
 center=p0[t0].mean(1);x,y,z=center.T;q=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.07)**2)
 remove=(q>1.07)&(q<1.66)&((y-.525)/.07<.4)&(z>.14)&~np.any(eye[t0],axis=1)
 E=np.sort(np.concatenate([ut[remove][:,[0,1]],ut[remove][:,[1,2]],ut[remove][:,[2,0]]]),axis=1);E,num=np.unique(E,axis=0,return_counts=True);loops=loops_from_edges(E[num==1]);assert len(loops)==2
 kept_tris=[t0[~remove],*tris[1:]];keep=np.unique(np.concatenate(kept_tris));mapping=np.full(len(p0),-1,dtype=int);mapping[keep]=np.arange(len(keep))
 positions=[p0[keep]];normals=[n0[keep]];uvs=[uv0[keep]];patch_tri=[];patch_info=[];atlas=np.zeros((256,512,3),dtype=np.uint8);border_orig=[];offset=len(keep)
 for patch_index,loop in enumerate(sorted(loops,key=lambda a:U[a,0].mean())):
  boundary=U[loop].copy();signed=sum(cross2(a[:2],b[:2]) for a,b in zip(boundary,np.roll(boundary,-1,axis=0)))
  # The triangulator expects CW; front-facing triangles are reversed later.
  if signed>0:loop=loop[::-1];boundary=U[loop].copy()
  border_orig.extend(first[loop].tolist())
  border_set=set(map(int,loop));all_edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
  near_edges=all_edges[np.isin(all_edges[:,0],loop)|np.isin(all_edges[:,1],loop)]
  ring=np.setdiff1d(np.unique(near_edges),loop)
  # Samples outside the replaced band provide slope constraints at each rim.
  surviving=np.unique(inv[t0[~remove]]);ring=ring[np.isin(ring,surviving)]
  samples=np.r_[loop,ring];sample_p=U[samples]
  # Interpolate exact rims plus retained one-ring samples. Interior folds are
  # discarded, rather than repeatedly smoothing their old triangulation.
  field=interpolator(sample_p[:,:2],sample_p[:,2:3])
  faces=triangulate_polygon(boundary[:,:2]);patch=list(boundary.copy())
  for _ in range(2):
   edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);edges,counts=np.unique(edges,axis=0,return_counts=True);mid={}
   for a,b in edges[counts==2]:
    xy=(np.array(patch[a][:2])+np.array(patch[b][:2]))/2
    mid[(int(a),int(b))]=len(patch);patch.append(np.r_[xy,field(xy)[0,0]])
   refined=[]
   for t in faces:
    poly=[]
    for a,b in zip(t,np.roll(t,-1)):
     poly.append(int(a));key=tuple(sorted((int(a),int(b))))
     if key in mid:poly.append(mid[key])
    xy=np.mean([patch[i][:2] for i in t],axis=0);ci=len(patch);patch.append(np.r_[xy,field(xy)[0,0]])
    for a,b in zip(poly,poly[1:]+poly[:1]):refined.append([ci,b,a])
   # Keep CW for the next refinement pass.
   faces=np.array(refined,dtype=int)[:,::-1]
  patch=np.asarray(patch,dtype=np.float32);faces=faces[:,::-1]
  e=.00004
  dx=(field(patch[:,:2]+[e,0])[:,0]-field(patch[:,:2]-[e,0])[:,0])/(2*e)
  dy=(field(patch[:,:2]+[0,e])[:,0]-field(patch[:,:2]-[0,e])[:,0])/(2*e)
  nn=np.c_[-dx,-dy,np.ones(len(patch))];nn/=np.linalg.norm(nn,axis=1)[:,None]
  # Boundary values are copied from the source. A local UV chart interpolates
  # source skin colors across the new bridge without baking the old groove.
  color_field=interpolator(sample_p[:,:2],C[samples])
  lo=patch[:,:2].min(0)-.001;hi=patch[:,:2].max(0)+.001
  xx,yy=np.meshgrid(np.linspace(lo[0],hi[0],256),np.linspace(hi[1],lo[1],256));grid=np.c_[xx.reshape(-1),yy.reshape(-1)]
  pixels=np.clip(np.round(color_field(grid)),0,255).astype(np.uint8).reshape(256,256,3)
  atlas[:,patch_index*256:(patch_index+1)*256]=pixels
  uv=np.c_[((patch[:,0]-lo[0])/(hi[0]-lo[0])+patch_index)/2,(hi[1]-patch[:,1])/(hi[1]-lo[1])].astype(np.float32)
  positions.append(patch);normals.append(nn.astype(np.float32));uvs.append(uv);patch_tri.append(faces+offset)
  patch_info.append({'side':int(np.sign(boundary[:,0].mean())),'rim_vertices':len(loop),'constraint_vertices':len(samples),'vertices':len(patch),'triangles':len(faces),'bounds':[patch.min(0).tolist(),patch.max(0).tolist()]})
  # Match the new boundary normal on all duplicates in the retained mesh.
  for j,uid in enumerate(loop):
   retained_indices=np.flatnonzero(inv[keep]==uid);normals[0][retained_indices]=nn[j]
  offset+=len(patch)
 p=np.concatenate(positions);n=np.concatenate(normals);uv=np.concatenate(uvs)
 new_tris=[mapping[t] for t in kept_tris]+[np.concatenate(patch_tri)]
 binary=bytearray(raw)
 def blob(data,target=None):
  binary.extend(b'\0'*((-len(binary))%4));start=len(binary);binary.extend(data);v={'buffer':0,'byteOffset':start,'byteLength':len(data)}
  if target is not None:v['target']=target
  g['bufferViews'].append(v);return len(g['bufferViews'])-1
 def array(a,kind,component,target):
  a=np.asarray(a,dtype='<f4' if component==5126 else '<u4');view=blob(a.tobytes(),target);acc={'bufferView':view,'componentType':component,'count':len(a),'type':kind}
  if kind=='VEC3':acc.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  g['accessors'].append(acc);return len(g['accessors'])-1
 attrs={'POSITION':array(p,'VEC3',5126,34962),'NORMAL':array(n,'VEC3',5126,34962),'TEXCOORD_0':array(uv,'VEC2',5126,34962)}
 stream=io.BytesIO();Image.fromarray(atlas).save(stream,format='PNG');iv=blob(stream.getvalue());g['images'].append({'bufferView':iv,'mimeType':'image/png'});g['textures'].append({'source':len(g['images'])-1,'sampler':g['textures'][0].get('sampler',0)})
 g['materials'].append({'name':'Lulu_EyeSkin_Bridge','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':len(g['textures'])-1},'metallicFactor':0,'roughnessFactor':.86}})
 g['meshes'][0]['primitives']=[{'attributes':attrs,'indices':array(t.reshape(-1),'SCALAR',5125,34963),'material':prims[i]['material'] if i<len(prims) else len(g['materials'])-1,'mode':4} for i,t in enumerate(new_tris)]
 g['buffers'][0]['byteLength']=len(binary);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
 result=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
 (R/'public/models/lulu-meshy-bridge.glb').write_bytes(result)
 border_mask=np.isin(inv[keep],inv[np.array(border_orig)])
 np.savez(R/'review/meshy-eye-bridge-map.npz',retained=keep,border=border_mask,removed=remove,eye=eye,new_patch_vertices=p[len(keep):])
 report={'revision':args.revision,'source_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'removed_triangles':int(remove.sum()),'patches':patch_info,'retained_vertices':len(keep),'output_vertices':len(p),'output_triangles':sum(map(len,new_tris)),'method':'two local crescent skin patches replaced; fixed eye faces and source rims; continuous interpolating bridge with source color transfer'}
 (R/'review/meshy-eye-bridge-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
