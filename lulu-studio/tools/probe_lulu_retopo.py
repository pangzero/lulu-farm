import numpy as np
from refine_meshy_eye_natural import R,read_glb,accessor
from rebuild_meshy_eye_bridge import loops_from_edges
_,g,b=read_glb(R/'review/meshy-eye-retopo-baseline/lulu-meshy-notail.glb');pr=g['meshes'][0]['primitives'][0];p=accessor(g,b,pr['attributes']['POSITION']);t=accessor(g,b,pr['indices']).reshape(-1,3)
_,first,inv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True);U=p[first];ut=inv[t];c=p[t].mean(1);x,y,z=c.T;q=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.07)**2)
for inner,cap in [(.55,1),(.60,1),(.65,1),(.60,.3),(.60,.5)]:
 remove=(q>inner)&(q<1.65)&(z>.08)
 if cap!=1:remove&=((y-.525)/.07<cap)
 e=np.sort(np.concatenate([ut[remove][:,[0,1]],ut[remove][:,[1,2]],ut[remove][:,[2,0]]]),axis=1);e,n=np.unique(e,axis=0,return_counts=True);be=e[n==1]
 try:loops=loops_from_edges(be);print(inner,cap,'faces',remove.sum(),'loops',[(len(l),np.round(U[l].mean(0),4).tolist()) for l in loops])
 except Exception as e:print(inner,cap,str(e))
