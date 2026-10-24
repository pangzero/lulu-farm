import numpy as np, geo, json
from collections import Counter
from scipy.spatial import cKDTree
def part_mesh(prims):
    P=np.vstack([p['P'] for p in prims]);off=np.cumsum([0]+[len(p['P']) for p in prims])
    I=np.vstack([p['I'].astype(np.int64)+o for p,o in zip(prims,off)]);pid=np.concatenate([np.full(len(p['I']),p['prim']) for p in prims])
    return P,I,pid,off
def borders(F):
    E=Counter(tuple(sorted(e)) for f in F for e in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])))
    return np.array(sorted(set(v for e,k in E.items() if k==1 for v in e)),int)
def cluster_weld(W,F,tol,keep):
    key=np.round(W/tol).astype(np.int64);key=np.c_[key,np.zeros(len(W),np.int64)]
    key[keep,3-0]=0;key[keep,:3]=0;key[keep,3]=np.arange(1,len(keep)+1) if np.ndim(keep)==1 and keep.dtype!=bool else 0
    return key
def decimate(P,I,target,tol=1e-3,lock_extra=None,scale=10):
    W,F=geo.weld(P,I,1e-6)
    b=borders(F);fixed=np.zeros(len(W),bool);fixed[b]=True
    if lock_extra is not None: fixed|=lock_extra(W)
    key=np.round(W/tol).astype(np.int64);key=np.c_[key,np.zeros(len(W),np.int64)]
    idx=np.where(fixed)[0];key[idx,:3]=0;key[idx,3]=idx+1
    _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True);inv=inv.ravel()
    W2=W[first];F2=inv[F];ok=(F2[:,0]!=F2[:,1])&(F2[:,1]!=F2[:,2])&(F2[:,0]!=F2[:,2]);F2=F2[ok]
    s=np.sort(F2,1);_,u=np.unique(s,axis=0,return_index=True);F2=F2[np.sort(u)]
    lk=fixed[first].astype(np.int32)
    V,T=geo.simplify(W2*scale,F2,target,7.0,lk);V/=scale
    return V,T,W,F,fixed
