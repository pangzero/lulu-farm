"""Code-authored seamless fabric sheets for the shared FabricUV channel."""
from pathlib import Path
import json,numpy as np,shutil
from PIL import Image
R=Path(__file__).resolve().parents[1];out=R/'public/models/wardrobe-rig/materials-v2';out.mkdir(parents=True,exist_ok=True);config=out.parent/'wardrobe.json';old=out.parent/'wardrobe-uv0-failed.json'
if config.exists() and not old.exists():shutil.copy2(config,old)
W,H=2048,1024;U,V=np.meshgrid(np.arange(W)/W,np.arange(H)/H);xx=U.ravel()*14;yy=V.ravel()*4;i=np.floor(xx);j=np.floor(yy);dx=xx-i-.5-.08*np.sin(i*6+j*3);dy=-(yy-j-.5-.08*np.cos(i*2+j*8));angles=np.arange(10)*np.pi/5+np.pi/2;r=np.where(np.arange(10)%2==0,.27,.12);vx=r*np.cos(angles);vy=r*np.sin(angles);star=np.zeros(len(dx),bool)
for k in range(10):
 l=(k+1)%10;hit=(vy[k]>dy)!=(vy[l]>dy);cross=(vx[l]-vx[k])*(dy-vy[k])/(vy[l]-vy[k]+1e-12)+vx[k];star^=hit&(dx<cross)
dot=dx*dx+dy*dy<.10**2;mask=np.where(((i+j)%3)==0,dot,star);blue=np.tile(np.array([161,210,234],np.uint8),(len(dx),1));blue[mask]=[250,226,101];blue[V.ravel()<.055]=[149,199,224]
xx=U.ravel()*13;yy=V.ravel()*3.2;i=np.floor(xx);j=np.floor(yy);dx=xx-i-.5;dy=-(yy-j-.5);ang=np.sin(i*9+j*3)*.35;c=np.cos(ang);s=np.sin(ang);x=c*dx-s*dy;y=s*dx+c*dy;rho=np.sqrt(x*x+(y-.23)**2);theta=np.arctan2(x,.23-y);wedge=(np.abs(theta)<.62)&(rho<.50);pink=wedge&(rho<.435);rind=wedge&(rho>.46);melon=np.tile(np.array([250,249,237],np.uint8),(len(dx),1));melon[wedge]=[225,241,202];melon[pink]=[237,130,143];melon[rind]=[107,167,112]
seed=np.zeros(len(dx),bool)
for sx,sy in [(-.10,-.01),(.10,-.01),(0,-.15)]:seed|=((x-sx)/.018)**2+((y-sy)/.033)**2<1
melon[seed&pink]=[93,73,64];melon[V.ravel()<.065]=[131,180,116]
for name,data in [('blue-stars',blue),('watermelon',melon)]:Image.fromarray(data.reshape(H,W,3)).save(out/(name+'.png'),optimize=True)
data={'version':2,'slot':'Shorts','template':'lulu shared short-pants silhouette','texCoord':1,'uv_name':'FabricUV','same_geometry':True,'same_skin_weights':True,'presets':[{'id':'original','name':'原版橙色','material':'original embedded materials / UV0'},{'id':'blue-stars','name':'蓝色星星','baseColor':'/models/wardrobe-rig/materials-v2/blue-stars.png','roughness':.86},{'id':'watermelon','name':'西瓜图案','baseColor':'/models/wardrobe-rig/materials-v2/watermelon.png','roughness':.86}],'template_notes':'One canonical fabric sheet per new outfit. UV0 retained for original orange. UV1 aligns all original material patches. Only index/UV seam duplication; geometry, normals and skin weights retained.','reference_note':'Original short-pants silhouette retained; high-cut briefs from the second screenshot would be a separate geometry template.'}
config.write_text(json.dumps(data,ensure_ascii=False,indent=2));print('Created shared 2048x1024 fabric sheets and UV1 wardrobe manifest')
