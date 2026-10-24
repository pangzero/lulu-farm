from refine_meshy_eye_natural import R,read_glb,accessor
from PIL import Image
import io,numpy as np,json
_,g,b=read_glb(R/'review/meshy-eye-bridge-baseline/lulu-meshy-notail.glb');pr=g['meshes'][0]['primitives'][0]
p=accessor(g,b,pr['attributes']['POSITION']);uv=accessor(g,b,pr['attributes']['TEXCOORD_0']);t=accessor(g,b,pr['indices']).reshape(-1,3)
v=g['bufferViews'][g['images'][0]['bufferView']];im=np.array(Image.open(io.BytesIO(b[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=im.shape[:2];c=im[(uv[:,1]*(h-1)).astype(int).clip(0,h-1),(uv[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
_,first,inv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True);U=p[first];C=c[first];ut=inv[t]
x,y,z=U.T;X=(abs(x)-.232)/.079;Y=(y-.525)/.07;q=np.sqrt(X*X+Y*Y)
sel=(x>.08)&(x<.4)&(y>.38)&(y<.65)&(z>.14)
for name,mask in [('white',(C.min(1)>160)&(C.max(1)-C.min(1)<65)),('blueblack',(C[:,2]>C[:,0]*.9)&(C[:,2]>C[:,1]*.85)),('skin',(C[:,0]>160)&(C[:,1]>140)&(C[:,2]<160))]:
 ii=sel&mask;print(name,ii.sum(),'q quantile',np.quantile(q[ii],[0,.1,.5,.9,1]),'bounds',U[ii].min(0),U[ii].max(0))
cent=U[ut].mean(1);cx,cy,cz=cent.T;cx=abs(cx);Q=np.sqrt(((cx-.232)/.079)**2+((cy-.525)/.07)**2);Y=(cy-.525)/.07
for ri,ro in [(.94,1.55),(1.03,1.58),(1.14,1.64)]:
 rm=(Q>ri)&(Q<ro)&(Y<.35)&(cz>.14)
 E=np.sort(np.concatenate([ut[rm][:,[0,1]],ut[rm][:,[1,2]],ut[rm][:,[2,0]]]),1);E,n=np.unique(E,axis=0,return_counts=True);be=E[n==1];ids,deg=np.unique(be,return_counts=True)
 print('cut',ri,ro,'faces',rm.sum(),'boundary',len(ids),'degree counts',np.unique(deg,return_counts=True))
np.savez(R/'review/meshy-eye-bridge-analysis.npz',p=p,c=c,uv=uv,t=t,first=first,inv=inv)
