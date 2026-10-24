"""Deterministic nearest-surface atlas transfer; prevents empty ray-bake texels.
Geometry is sampled only from the corresponding source object. Tangent normals transfer true high-surface normals.
"""
import bpy,numpy as np,math,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def bake(high,low,res,folder,semantic=None,supersample=1):
 output_res=res;res*=supersample
 high.data.calc_loop_triangles();low.data.calc_loop_triangles();hs=list(high.data.loop_triangles);ls=list(low.data.loop_triangles)
 verts=np.array([tuple(v.co) for v in high.data.vertices],np.float64);norms=np.array([tuple(v.normal) for v in high.data.vertices],np.float64);uv=high.data.uv_layers.active.data
 tree=BVHTree.FromPolygons([Vector(v) for v in verts],[tuple(t.vertices) for t in hs],all_triangles=True)
 hidx=np.array([t.vertices for t in hs]);hpos=verts[hidx];hnorm=norms[hidx];huv=np.array([[tuple(uv[j].uv) for j in t.loops] for t in hs]);hm=np.array([t.material_index for t in hs]);textures={};factors={}
 for mi,mat in enumerate(high.data.materials):
  bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');factors[mi]=np.array(bs.inputs['Base Color'].default_value)
  factors[mi][:3]=np.where(factors[mi][:3]<=.0031308,12.92*factors[mi][:3],1.055*np.power(factors[mi][:3],1/2.4)-.055)
  if bs.inputs['Base Color'].links:
   tex=bs.inputs['Base Color'].links[0].from_node
   if tex.type=='TEX_IMAGE' and tex.image:
    im=tex.image;p=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(p);textures[mi]=p.reshape(im.size[1],im.size[0],4)
 color=np.zeros((res,res,4),np.float32);normal=np.zeros_like(color);normal[:,:,:3]=(.5,.5,1);filled=np.zeros((res,res),bool);luv=low.data.uv_layers.active.data;clock=time.time();count=0
 for ti,tri in enumerate(ls):
  st=np.array([tuple(luv[j].uv) for j in tri.loops])*res-.5;p=np.array([tuple(low.data.vertices[v].co) for v in tri.vertices]);vn=np.array([tuple(low.data.vertices[v].normal) for v in tri.vertices]);mn=np.maximum(0,np.floor(st.min(0)).astype(int));mx=np.minimum(res-1,np.ceil(st.max(0)).astype(int));
  if np.any(mn>mx):continue
  den=(st[1,1]-st[2,1])*(st[0,0]-st[2,0])+(st[2,0]-st[1,0])*(st[0,1]-st[2,1])
  if abs(den)<1e-10:continue
  xs,ys=np.meshgrid(np.arange(mn[0],mx[0]+1),np.arange(mn[1],mx[1]+1));aa=((st[1,1]-st[2,1])*(xs-st[2,0])+(st[2,0]-st[1,0])*(ys-st[2,1]))/den;bb=((st[2,1]-st[0,1])*(xs-st[2,0])+(st[0,0]-st[2,0])*(ys-st[2,1]))/den;cc=1-aa-bb;mask=(aa>=-.001)&(bb>=-.001)&(cc>=-.001)
  if not mask.any():
   xs=np.array([[int(np.clip(round(st[:,0].mean()),0,res-1))]]);ys=np.array([[int(np.clip(round(st[:,1].mean()),0,res-1))]]);aa=bb=cc=np.array([[1/3]]);mask=np.array([[True]])
  x=xs[mask];y=ys[mask];bary=np.stack((aa[mask],bb[mask],cc[mask]),1);pos=bary@p;ln=bary@vn;ln/=np.maximum(np.linalg.norm(ln,axis=1)[:,None],1e-10)
  results=[tree.find_nearest(Vector(q)) for q in pos];face=np.array([z[2] for z in results]);closest=np.array([z[0] for z in results]);hp=hpos[face];e0=hp[:,1]-hp[:,0];e1=hp[:,2]-hp[:,0];q=closest-hp[:,0];d00=np.sum(e0*e0,1);d01=np.sum(e0*e1,1);d11=np.sum(e1*e1,1);d20=np.sum(q*e0,1);d21=np.sum(q*e1,1);dd=d00*d11-d01*d01;dd=np.where(abs(dd)<1e-18,1e-18,dd);v=(d11*d20-d01*d21)/dd;w=(d00*d21-d01*d20)/dd;hb=np.stack((1-v-w,v,w),1);tuv=np.sum(huv[face]*hb[:,:,None],1);n=np.sum(hnorm[face]*hb[:,:,None],1);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
  # Maintain front/back normal agreement. Nearby opposed surfaces use the low normal instead of flipping.
  bad=np.sum(n*ln,axis=1)<.15;n[bad]=ln[bad]
  mids=hm[face]
  for mi in np.unique(mids):
   k=mids==mi
   if mi in textures:
    pix=textures[mi];ux=np.clip(tuv[k,0]*(pix.shape[1]-1),0,pix.shape[1]-1);uy=np.clip(tuv[k,1]*(pix.shape[0]-1),0,pix.shape[0]-1);tx=np.floor(ux).astype(int);ty=np.floor(uy).astype(int);xx=np.minimum(tx+1,pix.shape[1]-1);yy=np.minimum(ty+1,pix.shape[0]-1);fx=(ux-tx)[:,None];fy=(uy-ty)[:,None];color[y[k],x[k]]=(pix[ty,tx]*(1-fx)+pix[ty,xx]*fx)*(1-fy)+(pix[yy,tx]*(1-fx)+pix[yy,xx]*fx)*fy
   else:color[y[k],x[k]]=factors[mi]
  if semantic=='rose':
   # Explicit 3D organ selection, independent of source pixel hue.
   # Existing Meshy flowers remain geometric sources, including all petals.
   flower=np.zeros(len(pos),bool)
   for center,radius,zmin in [((-.069,-.081,.777),(.23,.22,.18),.62),((-.236,-.132,.505),(.16,.17,.14),.382),((.223,.036,.684),(.1,.11,.14),.574)]:
    q=(closest-np.array(center))/np.array(radius);flower|=(np.sum(q*q,axis=1)<1)&(closest[:,2]>zmin)
   # A narrow luminance modulation retains shallow sculpted petal information
   # without inheriting pink contaminants in semantic foliage.
   lum=color[y,x,:3]@np.array([.2126,.7152,.0722]);variation=np.clip(.90+lum*.13,.90,1.03)
   base=np.tile(np.array([.25,.53,.105]),(len(pos),1))*variation[:,None]
   # Original flower-organ colors preserve the exact petal/green-sepal boundary;
   # only explicitly selected foliage outside those volumes is repainted.
   base[flower]=color[y[flower],x[flower],:3]
   color[y,x,:3]=base
  duv1=st[1]-st[0];duv2=st[2]-st[0];det=duv1[0]*duv2[1]-duv1[1]*duv2[0];tangent=(p[1]-p[0])*duv2[1]-(p[2]-p[0])*duv1[1];tangent/=det if abs(det)>1e-15 else 1;tt=tangent[None,:]-ln*np.sum(ln*tangent,axis=1)[:,None];tt/=np.maximum(np.linalg.norm(tt,axis=1)[:,None],1e-10);bt=np.cross(ln,tt);hand=1 if det>0 else -1;bt*=hand
  tn=np.stack((np.sum(n*tt,1),np.sum(n*bt,1),np.sum(n*ln,1)),1);normal[y,x,:3]=tn*.5+.5;color[y,x,3]=1;normal[y,x,3]=1;filled[y,x]=True;count+=len(x)
 # Pad islands to avoid edge filtering from empty atlas background.
 for _ in range(12):
  nextmask=filled.copy()
  for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
   f=np.roll(filled,(dy,dx),(0,1));sel=f&~nextmask;color[sel]=np.roll(color,(dy,dx),(0,1))[sel];normal[sel]=np.roll(normal,(dy,dx),(0,1))[sel];nextmask|=sel
  filled=nextmask
 # Extend padding through every unused atlas texel, including subpixel islands. This changes only atlas gutters.
 for step in [1,2,4,8,16,32,64,128,256,512,1024]:
  if filled.all():break
  for dy,dx in [(0,step),(0,-step),(step,0),(-step,0)]:
   sel=np.roll(filled,(dy,dx),(0,1))&~filled;color[sel]=np.roll(color,(dy,dx),(0,1))[sel];normal[sel]=np.roll(normal,(dy,dx),(0,1))[sel];filled|=sel
 def save(name,data,space):
  if supersample>1:data=data.reshape(output_res,supersample,output_res,supersample,4).mean(axis=(1,3))
  im=bpy.data.images.new(low.name+' '+name,output_res,output_res,alpha=True);im.colorspace_settings.name=space;im.pixels.foreach_set(data.ravel());im.update();im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
 print('BVH_BAKE',low.name,count,round(time.time()-clock,2),'seconds',flush=True)
 return save('basecolor',color,'sRGB'),save('normal',normal,'Non-Color'),{'sampled_texels':count,'method':'corresponding-object BVH nearest face + barycentric source UV, no empty ray hits','normal_disagreement':'low normal fallback for source dot < .15','seconds':time.time()-clock}
