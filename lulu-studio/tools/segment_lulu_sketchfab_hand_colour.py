"""Surface-distance colour labels only; does not separate or alter geometry."""
from pathlib import Path
import numpy as np,heapq,json
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-sketchfab-color-20261019'
v=np.load(D/'baseline/geometry.npz');p,n,f=v['p'],v['n'],v['f']
u,inv=np.unique(p,axis=0,return_inverse=True);count=np.bincount(inv)
nn=np.stack([np.bincount(inv,weights=n[:,a])/count for a in range(3)],axis=1)
nn/=np.maximum(np.linalg.norm(nn,axis=1),1e-20)[:,None];x,y,z=u.T
roi=(x<-.155)&(x>-.315)&(y>.145)&(y<.345)&(z<.045)&(z>-.27)
ids=np.where(roi)[0];lookup=np.full(len(u),-1,int);lookup[ids]=np.arange(len(ids))
f=inv[f];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);e=e[roi[e].all(1)];e=np.unique(np.sort(e,axis=1),axis=0)
delta=u[e[:,1]]-u[e[:,0]];length=np.linalg.norm(delta,axis=1)
projection=np.einsum('ij,ij->i',nn[e[:,1]]-nn[e[:,0]],delta)/np.maximum(length,1e-10)
w=length*(1+1500*np.maximum(-projection,0)**2);adj=[[] for _ in ids]
for (a,b),ww in zip(lookup[e],w):adj[a].append((int(b),float(ww)));adj[b].append((int(a),float(ww)))
q=u[ids]
armseeds=np.array([[-.264,.25,-.033],[-.251,.228,-.053],[-.262,.188,-.161],[-.202,.252,-.235],[-.214,.200,-.242],[-.23,.225,-.245],[-.27,.29,-.08],[-.268358,.225058,-.194131],[-.251780,.185685,-.205970],[-.2794,.217,-.1066]])
clothseeds=np.array([[-.239174,.241636,-.015627],[-.22,.158,-.23],[-.154383,.202263,-.201256]])
A=np.unique([np.linalg.norm(q-s,axis=1).argmin() for s in armseeds])
B=np.unique(np.r_[[np.linalg.norm(q-s,axis=1).argmin() for s in clothseeds],np.where((q[:,1]<.154)|((q[:,0]>-.160)&(q[:,1]<.27)))[0]])
def distances(seeds):
    d=np.full(len(q),np.inf);d[seeds]=0;heap=[(0,int(i)) for i in seeds];heapq.heapify(heap)
    while heap:
        dd,a=heapq.heappop(heap)
        if dd!=d[a]:continue
        for b,w0 in adj[a]:
            v=dd+w0
            if v<d[b]:d[b]=v;heapq.heappush(heap,(v,b))
    return d
ad,bd=distances(A),distances(B);arm=ad<bd
selected=np.zeros(len(u),bool);selected[ids[arm]]=True
out=D/'baseline/hand-colour-segmentation-r02.npz'
if out.exists():raise RuntimeError('Keep colour-label history')
np.savez_compressed(out,u=u,inv=inv,arm_source_vertex=selected[inv],arm_u=selected)
(out.with_suffix('.json')).write_text(json.dumps({'scope':'colour labels only; geometry untouched','roi_vertices':len(ids),'hand_vertices':int(arm.sum()),'arm_seeds':armseeds.tolist(),'clothing_seeds':clothseeds.tolist()},indent=2))
print(out,'hand vertices',arm.sum())
