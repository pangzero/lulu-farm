"""Delete the folded eye connection annuli and build new manifold patch meshes.

Preserves source eye centers, body and head silhouette. Rebuilds in each eye's
own tangent coordinates, transferring its source color design to the new mesh.
Old interior triangles/vertices are discarded, never smoothed.
"""
import argparse,copy,hashlib,io,json,struct,subprocess
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor,smoothstep
from rebuild_meshy_eye_bridge import loops_from_edges,interpolator,cross2
BASE=R/'review/meshy-eye-retopo-baseline/lulu-meshy-notail.glb'

def image(g,raw,index,mode):
 v=g['bufferViews'][g['images'][index]['bufferView']]
 return np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert(mode))

def bake_projection(p,t,uv,images,lo,hi,resolution):
 """Transfer the exact visible front color/material design by a depth raster."""
 depth=np.full((resolution,resolution),-np.inf);charts=[np.zeros((resolution,resolution,im.shape[2]),dtype=np.uint8) for im in images]
 pp=p[t];selected=(pp[:,:,0].max(1)>=lo[0])&(pp[:,:,0].min(1)<=hi[0])&(pp[:,:,1].max(1)>=lo[1])&(pp[:,:,1].min(1)<=hi[1])&(pp[:,:,2].max(1)>.08)
 xy=np.c_[(p[:,0]-lo[0])/(hi[0]-lo[0])*resolution-.5,(hi[1]-p[:,1])/(hi[1]-lo[1])*resolution-.5]
 for tr in t[selected]:
  a,b,c=xy[tr];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:continue
  q=xy[tr];mn=np.maximum(np.ceil(q.min(0)).astype(int),0);mx=np.minimum(np.floor(q.max(0)).astype(int),resolution-1)
  if np.any(mx<mn):continue
  xx,yy=np.meshgrid(np.arange(mn[0],mx[0]+1),np.arange(mn[1],mx[1]+1))
  u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
  v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
  z=u*p[tr[0],2]+v*p[tr[1],2]+w*p[tr[2],2];mask=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(z>depth[yy,xx])
  if not mask.any():continue
  yy=yy[mask];xx=xx[mask];u=u[mask];v=v[mask];w=w[mask];depth[yy,xx]=z[mask]
  tex=u[:,None]*uv[tr[0]]+v[:,None]*uv[tr[1]]+w[:,None]*uv[tr[2]]
  for im,out in zip(images,charts):
   h,wi=im.shape[:2];tx=np.clip(tex[:,0]*(wi-1),0,wi-1);ty=np.clip(tex[:,1]*(h-1),0,h-1);ix=np.floor(tx).astype(int);iy=np.floor(ty).astype(int);fx=(tx-ix)[:,None];fy=(ty-iy)[:,None];jx=np.minimum(ix+1,wi-1);jy=np.minimum(iy+1,h-1)
   value=(im[iy,ix]*(1-fx)+im[iy,jx]*fx)*(1-fy)+(im[jy,ix]*(1-fx)+im[jy,jx]*fx)*fy;out[yy,xx]=np.clip(np.round(value),0,255)
 return charts,depth


def clean_old_skin_groove(chart,depth,lo,hi,side,world_xy=None):
 """Remove baked groove shading on skin; preserve all eye-color pixels."""
 res=chart.shape[0];xx,yy=np.meshgrid(np.linspace(lo[0],hi[0],res),np.linspace(hi[1],lo[1],res))
 if world_xy is not None:xx,yy=world_xy[:,:,0],world_xy[:,:,1]
 ax=abs(xx);Q=np.sqrt(((ax-.232)/.079)**2+((yy-.525)/.07)**2);rgb=chart.astype(float);r,g,b=rgb.transpose(2,0,1)
 white=(rgb.min(2)>165)&((rgb.max(2)-rgb.min(2))<100)
 blue=(b>r*.86)&(b>g*.82);dark=(rgb.mean(2)<115)&(Q<1.1)
 eye=(Q<1.18)&(white|blue|dark)
 for _ in range(2):
  padded=np.pad(eye,1);eye=np.logical_or.reduce([padded[j:j+res,i:i+res] for j in range(3) for i in range(3)])
 X=(ax-.232)/.14;Y=(yy-.50)/.10;A=np.stack([np.ones_like(X),X,Y,X*X,X*Y,Y*Y],axis=-1)
 healthy=np.isfinite(depth)&~eye&(Q>1.15)&(Q<1.8)&(yy>.435)&(r>220)&(g>190)&(b<170)
 aa=A[healthy];cc=rgb[healthy];coef=np.linalg.lstsq(aa,cc,rcond=None)[0]
 for _ in range(4):
  err=np.linalg.norm(aa@coef-cc,axis=1);w=1/np.maximum(1,err/8)
  coef=np.linalg.lstsq(aa*w[:,None],cc*w[:,None],rcond=None)[0]
 target=A@coef
 lower=np.sqrt(((ax-.24)/.12)**2+((yy-.466)/.055)**2)
 inner=np.sqrt(((ax-.163)/.052)**2+((yy-.503)/.047)**2)
 weight=np.maximum(smoothstep((1.15-lower)/.45),smoothstep((1.10-inner)/.45))
 weight*=smoothstep((yy-.435)/.015)*smoothstep((.545-yy)/.025)*.95
 weight[eye|~np.isfinite(depth)]=0
 out=np.clip(np.round(rgb+(target-rgb)*weight[:,:,None]),0,255).astype(np.uint8)
 return out,{'skin_pixels_changed':int(np.any(out!=chart,axis=2).sum()),'protected_eye_pixels_exact':bool(np.array_equal(out[eye],chart[eye]))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--revision',default='retopo-5');ap.add_argument('--resolution',type=int,default=768);ap.add_argument('--eye-shape',type=float,default=0);ap.add_argument('--tangent',action='store_true',default=True);ap.add_argument('--front-projection',dest='tangent',action='store_false');args=ap.parse_args()
 data,g,raw=read_glb(BASE);old_pr=g['meshes'][0]['primitives'];pr=old_pr[0];p0=accessor(g,raw,pr['attributes']['POSITION']).copy();n0=accessor(g,raw,pr['attributes']['NORMAL']).copy();uv0=accessor(g,raw,pr['attributes']['TEXCOORD_0']).copy();tris=[accessor(g,raw,q['indices']).reshape(-1,3).copy() for q in old_pr];t0=tris[0]
 _,first,inv=np.unique(np.round(p0,6),axis=0,return_index=True,return_inverse=True);U=p0[first];ut=inv[t0];cent=p0[t0].mean(1);x,y,z=cent.T;q=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.07)**2)
 removed=(q>.6)&(q<1.65)&(z>.08)
 e=np.sort(np.concatenate([ut[removed][:,[0,1]],ut[removed][:,[1,2]],ut[removed][:,[2,0]]]),axis=1);e,count=np.unique(e,axis=0,return_counts=True);loops=loops_from_edges(e[count==1]);assert len(loops)==4
 all_edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
 surviving=np.unique(inv[t0[~removed]]);kept_tris=[t0[~removed],*tris[1:]];keep=np.unique(np.concatenate(kept_tris));mapping=np.full(len(p0),-1,dtype=int);mapping[keep]=np.arange(len(keep))
 P=[p0[keep]];N=[n0[keep]];UV=[uv0[keep]];patches=[];info=[];offset=len(keep);res=args.resolution
 images=[image(g,raw,0,'RGB'),image(g,raw,1,'RGB'),image(g,raw,3,'RGBA')];atlases=[np.zeros((res,2*res,im.shape[2]),dtype=np.uint8) for im in images];patch_meshes=[]
 for index,side in enumerate([-1,1]):
  ll=[l for l in loops if np.sign(U[l,0].mean())==side]
  ll.sort(key=lambda l:np.ptp(U[l,:2],axis=0).prod(),reverse=True);outer,inner=ll
  basis=np.eye(3)
  if args.tangent:
   en=np.array([side*.525,.65,1.]);en/=np.linalg.norm(en)
   eu=np.array([1.,0.,-side*.525]);eu/=np.linalg.norm(eu)
   ev=np.cross(en,eu);basis=np.stack([eu,ev,en],axis=1)
  local_U=U@basis;local_p=p0@basis
  # Earcut preserves source rim vertices and the inner eye opening.
  inputs=R/f'review/retopo-{side}-loops.json';outputs=R/f'review/retopo-{side}-triangles.json';inputs.write_text(json.dumps({'outer':local_U[outer,:2].tolist(),'inner':local_U[inner,:2].tolist()}));subprocess.run(['node',str(R/'tools/triangulate_lulu_annulus.mjs'),str(inputs),str(outputs)],check=True)
  faces=np.array(json.loads(outputs.read_text()),dtype=int);rim=np.r_[outer,inner];boundary=local_U[rim].copy();border_len=len(rim)
  # Ensure every source boundary edge is present; do not silently drop rim points.
  be=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);be,cc=np.unique(be,axis=0,return_counts=True);assert (cc==1).sum()==len(rim)
  rr=all_edges[np.isin(all_edges[:,0],rim)|np.isin(all_edges[:,1],rim)];ring=np.setdiff1d(np.unique(rr),rim);ring=ring[np.isin(ring,surviving)];samples=np.r_[rim,ring]
  # Preserve the accepted convex eye-face shape within the new annulus.
  # Fit its visible blue/white surface, then constrain new interior eye rings.
  source_color=images[0];hh,ww=source_color.shape[:2]
  cc=source_color[(uv0[:,1]*(hh-1)).astype(int).clip(0,hh-1),(uv0[:,0]*(ww-1)).astype(int).clip(0,ww-1)].astype(float)
  X=(p0[:,0]*side-.232)/.09;Y=(p0[:,1]-.525)/.08;Q=np.sqrt(((p0[:,0]*side-.232)/.079)**2+((p0[:,1]-.525)/.07)**2)
  eye=(p0[:,0]*side>0)&(p0[:,2]>.15)&(Q<1.02)&(cc[:,2]>cc[:,0]*.9)&(cc[:,2]>cc[:,1]*.85)
  A=np.c_[np.ones(len(p0)),X,Y,X*X,X*Y,Y*Y];coef=np.linalg.lstsq(A[eye],p0[eye,2],rcond=None)[0]
  for _ in range(4):
   err=A[eye]@coef-p0[eye,2];weight=1/np.maximum(1,abs(err)/.004)
   coef=np.linalg.lstsq(A[eye]*weight[:,None],p0[eye,2]*weight,rcond=None)[0]
  theta=np.linspace(0,2*np.pi,36,endpoint=False);anchors=[]
  for radius in [.72,.86,.98]:
   ax=side*(.232+.079*radius*np.cos(theta));ay=.525+.07*radius*np.sin(theta)
   xx=(abs(ax)-.232)/.09;yy=(ay-.525)/.08
   az=np.c_[np.ones(len(ax)),xx,yy,xx*xx,xx*yy,yy*yy]@coef
   anchors.extend(np.c_[ax,ay,az])
  anchors=np.array(anchors)
  anchors=anchors@basis
  base_field=interpolator(local_U[samples,:2],local_U[samples,2:3])
  base_z=base_field(anchors[:,:2])[:,0]
  anchors[:,2]=base_z+(anchors[:,2]-base_z)*args.eye_shape
  fit_samples=np.concatenate([local_U[samples],anchors])
  field=interpolator(fit_samples[:,:2],fit_samples[:,2:3]) if args.eye_shape else base_field
  # Normalize initial face winding to +Z.
  signed=np.cross(boundary[faces[:,1]]-boundary[faces[:,0]],boundary[faces[:,2]]-boundary[faces[:,0]])[:,2];faces[signed<0]=faces[signed<0,::-1]
  patch=list(boundary.copy())
  for _ in range(3):
   ee=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);ee,cc=np.unique(ee,axis=0,return_counts=True);mid={}
   for a,b in ee[cc==2]:
    xy=(np.array(patch[a][:2])+np.array(patch[b][:2]))*.5;mid[(int(a),int(b))]=len(patch);patch.append(np.r_[xy,field(xy)[0,0]])
   new=[]
   for tr in faces:
    poly=[]
    for a,b in zip(tr,np.roll(tr,-1)):
     poly.append(int(a));key=tuple(sorted((int(a),int(b))))
     if key in mid:poly.append(mid[key])
    xy=np.mean([patch[v][:2] for v in tr],axis=0);ci=len(patch);patch.append(np.r_[xy,field(xy)[0,0]])
    for a,b in zip(poly,poly[1:]+poly[:1]):new.append([ci,a,b])
   faces=np.array(new,dtype=int)
  patch=np.asarray(patch,dtype=np.float32);ep=.00003
  dx=(field(patch[:,:2]+[ep,0])[:,0]-field(patch[:,:2]-[ep,0])[:,0])/(2*ep);dy=(field(patch[:,:2]+[0,ep])[:,0]-field(patch[:,:2]-[0,ep])[:,0])/(2*ep)
  normal=np.c_[-dx,-dy,np.ones(len(patch))];normal/=np.linalg.norm(normal,axis=1)[:,None];normal=normal@basis.T;normal[:border_len]=n0[first[rim]]
  lo=patch[:,:2].min(0)-.002;hi=patch[:,:2].max(0)+.002;charts,depth=bake_projection(local_p,t0,uv0,images,lo,hi,res)
  cx,cy=np.meshgrid(np.linspace(lo[0],hi[0],res),np.linspace(hi[1],lo[1],res));coords=np.c_[cx.ravel(),cy.ravel()];cz=np.concatenate([field(coords[j:j+2048])[:,0] for j in range(0,len(coords),2048)])
  world_xy=(np.c_[coords,cz]@basis.T)[:,:2].reshape(res,res,2)
  charts[0],paint_info=clean_old_skin_groove(charts[0],depth,lo,hi,side,world_xy)
  for chart,atlas in zip(charts,atlases):atlas[:,index*res:(index+1)*res]=chart
  tex=np.c_[((patch[:,0]-lo[0])/(hi[0]-lo[0])+index)/2,(hi[1]-patch[:,1])/(hi[1]-lo[1])].astype(np.float32)
  patch=(patch@basis.T).astype(np.float32);patch[:border_len]=U[rim]
  P.append(patch);N.append(normal.astype(np.float32));UV.append(tex);patches.append(faces+offset);patch_meshes.append((patch,faces));offset+=len(patch)
  info.append({'side':side,'graph_axis':basis[:,2].tolist(),'outer_rim':len(outer),'inner_rim':len(inner),'new_vertices':len(patch),'new_triangles':len(faces),'bounds':[patch.min(0).tolist(),patch.max(0).tolist()],'raster_coverage':float(np.isfinite(depth).mean()),'skin_paint_cleanup':paint_info})
 p=np.concatenate(P);n=np.concatenate(N);uv=np.concatenate(UV);new_tri=[mapping[t] for t in kept_tris]+[np.concatenate(patches)];binary=bytearray(raw)
 def blob(value,target=None):
  binary.extend(b'\0'*((-len(binary))%4));start=len(binary);binary.extend(value);view={'buffer':0,'byteOffset':start,'byteLength':len(value)}
  if target is not None:view['target']=target
  g['bufferViews'].append(view);return len(g['bufferViews'])-1
 def array(a,kind,component,target):
  a=np.asarray(a,dtype='<f4' if component==5126 else '<u4');view=blob(a.tobytes(),target);ac={'bufferView':view,'componentType':component,'count':len(a),'type':kind}
  if kind=='VEC3':ac.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  g['accessors'].append(ac);return len(g['accessors'])-1
 attrs={'POSITION':array(p,'VEC3',5126,34962),'NORMAL':array(n,'VEC3',5126,34962),'TEXCOORD_0':array(uv,'VEC2',5126,34962)};texture_ids=[]
 for atlas in atlases:
  s=io.BytesIO();Image.fromarray(atlas).save(s,format='PNG');view=blob(s.getvalue());g['images'].append({'bufferView':view,'mimeType':'image/png'});g['textures'].append({'source':len(g['images'])-1,'sampler':0});texture_ids.append(len(g['textures'])-1)
 mat=copy.deepcopy(g['materials'][0]);mat['name']='Lulu_Retopo_EyeConnection';mat.pop('normalTexture',None);mat['pbrMetallicRoughness']['baseColorTexture']['index']=texture_ids[0];mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=texture_ids[1];mat['extensions']['KHR_materials_specular']['specularTexture']['index']=texture_ids[2];g['materials'].append(mat)
 g['meshes'][0]['primitives']=[{'attributes':attrs,'indices':array(tr.reshape(-1),'SCALAR',5125,34963),'material':old_pr[i]['material'] if i<len(old_pr) else len(g['materials'])-1,'mode':4} for i,tr in enumerate(new_tri)]
 g['buffers'][0]['byteLength']=len(binary);js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4);out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
 (R/'public/models/lulu-meshy-retopo.glb').write_bytes(out);np.savez(R/'review/meshy-eye-retopo-map.npz',retained=keep,removed=removed,new_patch_vertices=p[len(keep):],new_patch_triangles=new_tri[-1]-len(keep))
 report={'revision':args.revision,'source_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'removed_triangles':int(removed.sum()),'retained_vertices':len(keep),'output_vertices':len(p),'output_triangles':sum(map(len,new_tri)),'new_patch_triangles':len(new_tri[-1]),'patches':info,'method':'old folded annuli deleted; inner eye core and outer head rim fixed; new triangulated annuli in eye-tangent coordinates; source color/material projection transfer; only old skin groove color locally repainted'}
 (R/'review/meshy-eye-retopo-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
