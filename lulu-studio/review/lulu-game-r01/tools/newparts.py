import numpy as np, clh
from pathlib import Path
def load_new(path='new.glb'):
    g,b=clh.load(Path(path));W=clh.worlds(g)
    ai=next(i for i,n in enumerate(g['nodes']) if n.get('name')=='R04_BodyAssembly_UniformFit');Ainv=np.linalg.inv(W[ai])
    parts={}
    for ni,n in enumerate(g['nodes']):
        if 'mesh' not in n: continue
        M=Ainv@W[ni];R=M[:3,:3];t=M[:3,3];Rn=np.linalg.inv(R).T
        prims=[]
        for pi,p in enumerate(g['meshes'][n['mesh']]['primitives']):
            mat=g['materials'][p['material']].get('name') if 'material' in p else None
            P=clh.accessor(g,b,p['attributes']['POSITION'])@R.T+t
            N=clh.accessor(g,b,p['attributes']['NORMAL'])@Rn.T;N/=np.linalg.norm(N,axis=1,keepdims=True)
            I=clh.accessor(g,b,p['indices']).reshape(-1,3)
            A={k:clh.accessor(g,b,v) for k,v in p['attributes'].items() if k in('COLOR_0','TEXCOORD_0','TEXCOORD_1')}
            prims.append(dict(P=P,N=N,I=I,mat=mat,A=A,prim=pi))
        parts[n['name']]=prims
    return g,b,parts,W[ai]
if __name__=='__main__':
    g,b,parts,A=load_new()
    print('assembly',A.round(4).tolist())
    for k,v in parts.items():
        for p in v: print(k,p['prim'],p['mat'],len(p['P']),len(p['I']),list(p['A']),p['P'].min(0).round(3),p['P'].max(0).round(3))
