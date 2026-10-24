import numpy as np, subprocess, struct, os, tempfile
from scipy.spatial import cKDTree
def closest_pt_tri(p,a,b,c):
    # vectorized Ericson; p,a,b,c: (...,3). returns barycentric (u,v,w) for a,b,c
    ab=b-a;ac=c-a;ap=p-a
    d1=(ab*ap).sum(-1);d2=(ac*ap).sum(-1)
    bp=p-b;d3=(ab*bp).sum(-1);d4=(ac*bp).sum(-1)
    cp=p-c;d5=(ab*cp).sum(-1);d6=(ac*cp).sum(-1)
    va=d3*d6-d5*d4;vb=d5*d2-d1*d6;vc=d1*d4-d3*d2
    u=np.zeros(p.shape[:-1]);v=np.zeros_like(u);w=np.zeros_like(u)
    den=va+vb+vc;den=np.where(np.abs(den)<1e-30,1e-30,den)
    v_=vb/den;w_=vc/den;u_=1-v_-w_
    u,v,w=u_.copy(),v_.copy(),w_.copy()
    def setm(m,uu,vv,ww):
        u[m]=uu[m] if np.ndim(uu) else uu; v[m]=vv[m] if np.ndim(vv) else vv; w[m]=ww[m] if np.ndim(ww) else ww
    # regions (apply in reverse priority so earlier override)
    with np.errstate(divide='ignore',invalid='ignore'):
        m=(va<=0)&((d4-d3)>=0)&((d5-d6)>=0);t=(d4-d3)/((d4-d3)+(d5-d6));setm(m,0,1-t,t)
        m=(vb<=0)&(d2>=0)&(d6<=0);t=d2/(d2-d6);setm(m,1-t,0,t)
        m=(vc<=0)&(d1>=0)&(d3<=0);t=d1/(d1-d3);setm(m,1-t,t,0)
        m=(d6>=0)&(d5<=d6);setm(m,0,0,1)
        m=(d3>=0)&(d4<=d3);setm(m,0,1,0)
        m=(d1<=0)&(d2<=0);setm(m,1,0,0)
    return np.stack([u,v,w],-1)
class Surf:
    def __init__(s,P,I,k=24):
        s.P=np.asarray(P,float);s.I=np.asarray(I);s.C=s.P[s.I].mean(1);s.t=cKDTree(s.C);s.k=min(k,len(s.I))
    def query(s,Q,mask_faces=None,chunk=20000):
        Q=np.asarray(Q,float);F=np.zeros(len(Q),int);B=np.zeros((len(Q),3));D=np.zeros(len(Q))
        for o in range(0,len(Q),chunk):
            q=Q[o:o+chunk];_,cand=s.t.query(q,k=s.k)
            if cand.ndim==1:cand=cand[:,None]
            tri=s.I[cand];a,b,c=s.P[tri[...,0]],s.P[tri[...,1]],s.P[tri[...,2]]
            bc=closest_pt_tri(q[:,None,:],a,b,c);pt=bc[...,0:1]*a+bc[...,1:2]*b+bc[...,2:3]*c
            d=np.linalg.norm(pt-q[:,None,:],axis=-1);d=np.where(np.isfinite(d),d,np.inf);j=d.argmin(1);r=np.arange(len(q))
            F[o:o+chunk]=cand[r,j];B[o:o+chunk]=bc[r,j];D[o:o+chunk]=d[r,j]
        return F,B,D
    def interp(s,F,B,attr):
        tri=s.I[F];B=np.nan_to_num(B,nan=1/3);return (attr[tri]*B[...,None]).sum(1)
def weld(P,I,tol=1e-6):
    key=np.round(P/tol).astype(np.int64);_,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True);inv=inv.ravel()
    W=P[first];F=inv[I];ok=(F[:,0]!=F[:,1])&(F[:,1]!=F[:,2])&(F[:,0]!=F[:,2]);F=F[ok]
    s=np.sort(F,1);_,u=np.unique(s,axis=0,return_index=True);F=F[np.sort(u)]
    return W,F
def simplify(P,I,target,agg=7.0,locked=None):
    if locked is None:locked=np.zeros(len(P),np.int32)
    d=tempfile.mkdtemp();fi=os.path.join(d,'in.bin');fo=os.path.join(d,'out.bin')
    with open(fi,'wb') as f:
        f.write(struct.pack('<iiid',len(P),len(I),int(target),agg));f.write(np.asarray(P,'<f4').tobytes());f.write(np.asarray(I,'<i4').tobytes());f.write(np.asarray(locked,'<i4').tobytes())
    subprocess.run([os.path.join(os.path.dirname(__file__),'qem','qem'),fi,fo],check=True)
    b=open(fo,'rb').read();nv,nt=struct.unpack('<ii',b[:8]);o=8
    V=np.frombuffer(b,'<f4',nv*3,o).reshape(-1,3).astype(float);o+=nv*12;T=np.frombuffer(b,'<i4',nt*3,o).reshape(-1,3)
    used=np.unique(T);remap=-np.ones(nv,int);remap[used]=np.arange(len(used));return V[used],remap[T]
def vnormals(P,I):
    n=np.zeros_like(P);fn=np.cross(P[I[:,1]]-P[I[:,0]],P[I[:,2]]-P[I[:,0]])
    for k in range(3):
        e1=P[I[:,(k+1)%3]]-P[I[:,k]];e2=P[I[:,(k+2)%3]]-P[I[:,k]]
        ang=np.arccos(np.clip((e1*e2).sum(1)/np.maximum(np.linalg.norm(e1,axis=1)*np.linalg.norm(e2,axis=1),1e-20),-1,1))
        np.add.at(n,I[:,k],fn/np.maximum(np.linalg.norm(fn,axis=1,keepdims=True),1e-20)*ang[:,None])
    return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-20)
