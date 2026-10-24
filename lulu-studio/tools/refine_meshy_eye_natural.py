"""Eye-corner/lower-lid skin refinement from the immutable current Meshy polish.

Only a continuous depth field changes the inner/lower eye transition. All X/Y,
the central eye core, textures, topology, head width, temples and body stay fixed.
"""
from pathlib import Path
import argparse, hashlib, io, json, struct
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[1]
BASE=R/'review/meshy-eye-natural-baseline/lulu-meshy-polish.glb'

def read_glb(path):
    data=path.read_bytes(); size=struct.unpack_from('<I',data,12)[0]
    return data,json.loads(data[20:20+size]),data[28+size:]

def accessor(g,raw,index):
    a=g['accessors'][index]; view=g['bufferViews'][a['bufferView']]
    size={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    return np.ndarray((a['count'],size),dtype=dtype,buffer=raw,
        offset=view.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(view.get('byteStride',size*dtype.itemsize),dtype.itemsize))

def smoothstep(t):
    t=np.clip(t,0,1); return t*t*t*(10+t*(-15+6*t))

def scope_and_core(p):
    x,y,z=p.T
    lower=np.sqrt(((abs(x)-.252)/.162)**2+((y-.468)/.069)**2)
    corner=np.sqrt(((abs(x)-.168)/.075)**2+((y-.503)/.080)**2)
    eye=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.070)**2)
    scope=((lower<1.16)|(corner<1.10))&(z>.14)
    core=(eye<.62)&(z>.14)
    return scope,core,lower,corner,eye

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=float,default=.035);parser.add_argument('--revision',default='natural-6')
    args=parser.parse_args()
    source,g,raw=read_glb(BASE);prim=g['meshes'][0]['primitives'][0]
    p0=accessor(g,raw,prim['attributes']['POSITION']).copy()
    n0=accessor(g,raw,prim['attributes']['NORMAL']).copy()
    uv=accessor(g,raw,prim['attributes']['TEXCOORD_0']).copy()
    triangles=accessor(g,raw,prim['indices']).reshape(-1,3).copy()
    view=g['bufferViews'][g['images'][0]['bufferView']]
    colors=np.array(Image.open(io.BytesIO(raw[view['byteOffset']:view['byteOffset']+view['byteLength']])).convert('RGB'))
    h,w=colors.shape[:2]
    c=colors[(uv[:,1]*(h-1)).astype(int).clip(0,h-1),(uv[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
    _,inverse=np.unique(np.round(p0,6),axis=0,return_inverse=True)
    counts=np.bincount(inverse);N=len(counts)
    average=lambda v:np.stack([np.bincount(inverse,weights=v[:,k])/counts for k in range(v.shape[1])],axis=1)
    U=average(p0);C=average(c);scope,core,lower,corner,eye=scope_and_core(U)
    X=(abs(U[:,0])-.232)/.09;Y=(U[:,1]-.525)/.08
    Q=np.sqrt(X*X+Y*Y)
    design=np.c_[np.ones(N),X,Y,X*X,X*Y,Y*Y]
    skin=(C[:,0]>150)&(C[:,1]>140)&(C[:,2]<180)
    healthy=(Q>1.48)&(Q<2.25)&(U[:,2]>.10)&skin
    coef=np.linalg.lstsq(design[healthy],U[healthy,2],rcond=None)[0]
    for _ in range(4):
        residual=design[healthy]@coef-U[healthy,2]
        robust=1/np.maximum(1,abs(residual)/.018)
        coef=np.linalg.lstsq(design[healthy]*robust[:,None],U[healthy,2]*robust,rcond=None)[0]
    def field(points):
        x,y,z=points.T
        lo=np.sqrt(((abs(x)-.252)/.162)**2+((y-.468)/.069)**2)
        co=np.sqrt(((abs(x)-.168)/.075)**2+((y-.503)/.080)**2)
        eq=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.070)**2)
        patch=np.maximum(smoothstep((1.16-lo)/.50),smoothstep((1.10-co)/.50))
        periphery=smoothstep((eq-.62)/.35)
        front=smoothstep((z-.14)/.07)
        weight=patch*periphery*front*smoothstep((.555-y)/.045)
        xx=(abs(x)-.232)/.09;yy=(y-.525)/.08
        target=coef[0]+coef[1]*xx+coef[2]*yy+coef[3]*xx*xx+coef[4]*xx*yy+coef[5]*yy*yy
        return args.limit*np.tanh((target-z)/args.limit)*weight*.50,weight
    shift,weight=field(U)
    delta=np.zeros_like(p0);delta[:,2]=shift[inverse]
    eps=1e-5;plus=U.copy();minus=U.copy();plus[:,2]+=eps;minus[:,2]-=eps
    jacobian=1+(field(plus)[0]-field(minus)[0])/(2*eps)
    assert jacobian.min()>.10, f'Depth transformation folds over: {jacobian.min()}'
    binary=bytearray(raw);p=accessor(g,binary,prim['attributes']['POSITION']);normal=accessor(g,binary,prim['attributes']['NORMAL'])
    p[:]=p0+delta;changed=np.any(p!=p0,axis=1)
    face=np.cross(p[triangles[:,1]]-p[triangles[:,0]],p[triangles[:,2]]-p[triangles[:,0]])
    sums=np.zeros((N,3))
    for k in range(3):np.add.at(sums,inverse[triangles[:,k]],face)
    sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-12)[:,None]
    normal[changed]=sums[inverse][changed]
    bounds=[p.min(0).tolist(),p.max(0).tolist()]
    pa=g['accessors'][prim['attributes']['POSITION']];pa['min'],pa['max']=bounds
    del p,normal
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    binary+=b'\0'*((-len(binary))%4)
    result=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    output=R/'public/models/lulu-meshy-natural.glb';output.write_bytes(result)
    np.savez(R/'review/meshy-eye-natural-delta.npz',delta=delta,weight=weight[inverse])
    report={'revision':args.revision,'baseline_sha256':hashlib.sha256(source).hexdigest(),
        'output_sha256':hashlib.sha256(result).hexdigest(),'surface_fit':coef.tolist(),'min_depth_jacobian':float(jacobian.min()),
        'limit':args.limit,'changed_vertices':int(changed.sum()),'max_axis_delta':np.abs(delta).max(0).tolist(),
        'temple_edit':False,'scope':'Continuous depth field on inner corner/lower eye skin and peripheral transition; eye core, all X/Y and head bounds pinned.'}
    (R/'review/meshy-eye-natural-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
