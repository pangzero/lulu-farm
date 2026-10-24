"""Bake code-authored fabric patterns into the fixed shorts UV atlas.
Reference screenshots are preserved separately, not edited or copied into UVs.
"""
from pathlib import Path
import sys,json,numpy as np,hashlib
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent));from lulu_patch_io import read_glb,triangles
R=Path(__file__).resolve().parents[1];out=R/'public/models/wardrobe-rig/materials';out.mkdir(parents=True,exist_ok=True);g,b=read_glb(R/'public/models/modular/right-junction-r04/lulu-assembled.glb');t,m=triangles(g,b,next(q for q in g['meshes'] if q['name']=='Shorts'));p=t[:,:,:3].reshape(-1,3);u=np.arctan2(p[:,0],p[:,2]+.08)/(2*np.pi)+.5;bins=128;heights=np.array([p[(u>=i/bins)&(u<(i+1)/bins),1].max() if np.any((u>=i/bins)&(u<(i+1)/bins)) else -.46 for i in range(bins)]);heights=(np.roll(heights,1)+heights+np.roll(heights,-1))/3
S=2048;blue=np.array([161,210,234],float);white=np.array([250,249,237],float);imgs=[np.tile(blue.astype(np.uint8),(S,S,1)),np.tile(white.astype(np.uint8),(S,S,1))]
def polygon(dx,dy):
 angles=np.arange(10)*np.pi/5+np.pi/2;r=np.where(np.arange(10)%2==0,.27,.12);vx=r*np.cos(angles);vy=r*np.sin(angles);inside=np.zeros(dx.shape,bool)
 for j in range(10):
  k=(j+1)%10;hit=(vy[j]>dy)!=(vy[k]>dy);xx=(vx[k]-vx[j])*(dy-vy[j])/(vy[k]-vy[j]+1e-12)+vx[j];inside^=hit&(dx<xx)
 return inside

def patterns(p):
 x,y,z=p.T;u=np.arctan2(x,z+.08)/(2*np.pi)+.5;U=u*14;V=(y+.85)*10;i=np.floor(U);j=np.floor(V);dx=U-i-.5-.10*np.sin(i*6+j*3);dy=V-j-.5-.10*np.cos(i*2+j*8);star=polygon(dx,dy);dot=dx*dx+dy*dy<.10**2;mask=np.where(((i+j)%3)==0,dot,star);a=np.tile(blue,(len(p),1));a[mask]=[250,226,101];top=np.interp(u,(np.arange(bins)+.5)/bins,heights,period=1);a[y>top-.020]=[150,199,224]
 U=u*13;V=(y+.85)*8;i=np.floor(U);j=np.floor(V);dx=U-i-.5;dy=V-j-.5;ang=np.sin(i*9+j*3)*.45;c=np.cos(ang);s=np.sin(ang);xx=c*dx-s*dy;yy=s*dx+c*dy;rho=np.sqrt(xx*xx+(yy-.23)**2);theta=np.arctan2(xx,.23-yy);wedge=(np.abs(theta)<.62)&(rho<.51);pink=wedge&(rho<.445);rind=wedge&(rho>.465);a2=np.tile(white,(len(p),1));a2[wedge]=[225,241,202];a2[pink]=[237,130,143];a2[rind]=[107,167,112]
 seed=np.zeros(len(p),bool)
 for sx,sy in [(-.10,-.01),(.10,-.01),(0,-.15)]:seed|=((xx-sx)/.018)**2+((yy-sy)/.033)**2<1
 a2[seed&pink]=[93,73,64];a2[y>top-.028]=[131,180,116]
 return a.astype(np.uint8),a2.astype(np.uint8)
count=0
for tri,mat in zip(t,m):
 if mat==2:continue
 uv=tri[:,6:8]*[S-1,S-1];lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),S-1)
 if np.any(hi<lo):continue
 a,bv,c=uv;den=(bv[1]-c[1])*(a[0]-c[0])+(c[0]-bv[0])*(a[1]-c[1])
 if abs(den)<1e-5:continue
 X,Y=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));xx=X.ravel();yy=Y.ravel();w0=((bv[1]-c[1])*(xx-c[0])+(c[0]-bv[0])*(yy-c[1]))/den;w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1;mask=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
 if not mask.any():continue
 pos=w0[mask,None]*tri[0,:3]+w1[mask,None]*tri[1,:3]+w2[mask,None]*tri[2,:3];colors=patterns(pos)
 for image,color in zip(imgs,colors):image[yy[mask],xx[mask]]=color
 count+=int(mask.sum())
for name,image in zip(['blue-stars','watermelon'],imgs):Image.fromarray(image).save(out/(name+'.png'),optimize=True)
config={'version':1,'slot':'Shorts','template':'right-junction-r04/Shorts','same_geometry':True,'same_uv':True,'same_skin_weights':True,'fit':'same waist and leg-opening silhouette as original short pants','presets':[{'id':'original','name':'原版橙色','material':'original embedded materials'},{'id':'blue-stars','name':'蓝色星星','baseColor':'/models/wardrobe-rig/materials/blue-stars.png','roughness':.86},{'id':'watermelon','name':'西瓜图案','baseColor':'/models/wardrobe-rig/materials/watermelon.png','roughness':.86}],'reference_note':'Color and motif direction from supplied screenshots; both are original-short-pants material studies. The higher-cut second screenshot silhouette is not reproduced by texture.'}
(out.parent/'wardrobe.json').write_text(json.dumps(config,ensure_ascii=False,indent=2));print(json.dumps({'rasterized_pixels':count,'size':S,'textures':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.glob('*.png')]}))
