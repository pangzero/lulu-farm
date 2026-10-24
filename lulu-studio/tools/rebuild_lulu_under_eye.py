"""One-eye surface study from an immutable modular r04 backup.

Preserve all painted-eye vertices, the opposite eye, all UVs/materials and
nonlocal geometry. Reconstruct the lower skin transition with Hermite sections
between the fixed eye rim and healthy cheek, not repeated mesh smoothing.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, struct
import numpy as np
from PIL import Image
from lulu_patch_io import read_glb, accessor

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-under-eye-20261018'

def smooth(t):
    t=np.clip(t,0,1);return t*t*t*(10+t*(-15+6*t))

def hull(points):
    ids=sorted(range(len(points)),key=lambda i:tuple(points[i,:2]))
    def cross(a,b,c):
        u=points[b,:2]-points[a,:2];v=points[c,:2]-points[a,:2]
        return u[0]*v[1]-u[1]*v[0]
    lo=[];hi=[]
    for i in ids:
        while len(lo)>1 and cross(lo[-2],lo[-1],i)<=0:lo.pop()
        lo.append(i)
    for i in ids[::-1]:
        while len(hi)>1 and cross(hi[-2],hi[-1],i)<=0:hi.pop()
        hi.append(i)
    return np.array(lo[:-1]+hi[:-1])

def store_accessor(g,buf,index,value):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
    array=np.ndarray(value.shape,dtype='<f4',buffer=buf,
      offset=v.get('byteOffset',0)+a.get('byteOffset',0),
      strides=(v.get('byteStride',value.shape[1]*4),4))
    array[:]=value

def write(path,g,b):
    g['buffers'][0]['byteLength']=len(b)
    j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    b.extend(b'\0'*((-len(b))%4))
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rev',default='r01');ap.add_argument('--strength',type=float,default=.8);ap.add_argument('--unfold',action='store_true');args=ap.parse_args()
    out=D/args.rev;out.mkdir(exist_ok=False)
    source=D/'baseline/modular-r04.glb';g,raw=read_glb(source)
    pr=g['meshes'][0]['primitives'][0];at=pr['attributes']
    P=accessor(g,raw,at['POSITION']);N=accessor(g,raw,at['NORMAL']);UV=accessor(g,raw,at['TEXCOORD_0']);T=accessor(g,raw,pr['indices']).reshape(-1,3)
    v=g['bufferViews'][g['images'][0]['bufferView']]
    image=np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'));h,w=image.shape[:2]
    C=image[(UV[:,1]*(h-1)).astype(int),(UV[:,0]*(w-1)).astype(int)].astype(float)
    U,inv=np.unique(P,axis=0,return_inverse=True);count=np.bincount(inv);num=len(U)
    x,y,z=U.T;local=(x>-.43)&(x<-.085)&(y>.375)&(y<.625)&(z>.10)
    lc=local[inv]
    col=((C.min(1)>160)&(C.max(1)-C.min(1)<65))|((C[:,2]>C[:,0]*.84)&(C[:,2]>C[:,1]*.84))
    pin=np.bincount(inv,weights=(col&lc).astype(int),minlength=num)>0
    eyeids=np.flatnonzero(pin);H=eyeids[hull(U[eyeids])]
    center=U[H,:2].mean(0);vec=U[:,:2]-center;radius=np.linalg.norm(vec,axis=1);direction=vec/np.maximum(radius[:,None],1e-12)
    rimR=np.zeros(num);rimZ=np.zeros(num)
    # Intersect each radial ray with the exact convex painted-eye boundary.
    for ia,ib in zip(H,np.roll(H,-1)):
        a=U[ia,:2]-center;edge=U[ib,:2]-U[ia,:2]
        den=direction[:,0]*edge[1]-direction[:,1]*edge[0]
        rr=(a[0]*edge[1]-a[1]*edge[0])/np.where(abs(den)>1e-12,den,1e-12)
        ss=(a[0]*direction[:,1]-a[1]*direction[:,0])/np.where(abs(den)>1e-12,den,1e-12)
        ok=(rr>0)&(ss>=-1e-6)&(ss<=1.000001)
        rimR[ok]=rr[ok];rimZ[ok]=U[ia,2]*(1-ss[ok])+U[ib,2]*ss[ok]
    dist=radius-rimR;pin|=(dist<=.0005)&local
    # Lower transition and inner-lower corner only, with a broad cheek exit.
    extent=.065
    angular=smooth((.18-direction[:,1])/.65)
    mask=local&~pin&(dist>0)&(dist<extent)&(angular>0)
    originalU=U.copy()
    if args.unfold:
        # Solve the local positive-weight harmonic parameterization in XY.
        # The old lower skin doubles back in screen projection. Merely altering
        # its depth leaves a folded strip. Fixed eye/boundary data stay exact.
        ut=inv[T];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
        chosen=np.flatnonzero(mask);mapping=np.full(num,-1);mapping[chosen]=np.arange(len(chosen));degree=np.bincount(edges.ravel(),minlength=num)[chosen].astype(float)
        both=mask[edges].all(1);aa=mapping[edges[both,0]];bb=mapping[edges[both,1]]
        cross=mask[edges].sum(1)==1;ce=edges[cross];ii=np.where(mask[ce[:,0]],ce[:,0],ce[:,1]);jj=np.where(mask[ce[:,0]],ce[:,1],ce[:,0]);ii=mapping[ii]
        def mul(v):
            r=degree*v
            np.add.at(r,aa,-v[bb]);np.add.at(r,bb,-v[aa]);return r
        for axis in [0,1]:
            rhs=np.bincount(ii,weights=U[jj,axis],minlength=len(chosen));solution=U[chosen,axis].copy();res=rhs-mul(solution);pre=res/degree;directionCG=pre.copy();rz=float(res@pre)
            for it in range(1200):
                q=mul(directionCG);alpha=rz/max(float(directionCG@q),1e-30);solution+=alpha*directionCG;res-=alpha*q
                if np.linalg.norm(res)<1e-10:break
                pre=res/degree;nrz=float(res@pre);directionCG=pre+(nrz/max(rz,1e-30))*directionCG;rz=nrz
            U[chosen,axis]=solution
        # Recompute the radial coordinates of redistributed skin vertices.
        vec=U[:,:2]-center;radius=np.linalg.norm(vec,axis=1);direction=vec/np.maximum(radius[:,None],1e-12)
        for ia,ib in zip(H,np.roll(H,-1)):
            a=U[ia,:2]-center;edge=U[ib,:2]-U[ia,:2];den=direction[:,0]*edge[1]-direction[:,1]*edge[0]
            rr=(a[0]*edge[1]-a[1]*edge[0])/np.where(abs(den)>1e-12,den,1e-12);ss=(a[0]*direction[:,1]-a[1]*direction[:,0])/np.where(abs(den)>1e-12,den,1e-12)
            ok=(rr>0)&(ss>=-1e-6)&(ss<=1.000001);rimR[ok]=rr[ok];rimZ[ok]=U[ia,2]*(1-ss[ok])+U[ib,2]*ss[ok]
        dist=radius-rimR
    ids=np.flatnonzero(mask)
    target=z.copy();weight=np.zeros(num)
    healthy=local&~pin&(dist>extent*.8)
    pool=U[healthy]
    for i in ids:
        direct=direction[i];outer=center+direct*(rimR[i]+extent)
        delta=pool[:,:2]-outer
        ds=np.sum(delta*delta,axis=1);choose=np.argsort(ds)[:45]
        q=delta[choose]/.025;qx,qy=q.T
        A=np.c_[np.ones(len(q)),qx,qy,qx*qx,qx*qy,qy*qy]
        ww=np.exp(-ds[choose]/(.025**2))+.001
        coef=np.linalg.lstsq(A*ww[:,None],pool[choose,2]*ww,rcond=None)[0]
        z1=coef[0];m1=(coef[1:3]@direct)/.025
        # Match the outgoing eye-surface slope using fixed interior samples.
        rimxy=center+direct*rimR[i];dv=U[eyeids,:2]-rimxy
        dd=np.sum(dv*dv,axis=1);near=np.argsort(dd)[:35]
        a=np.c_[np.ones(len(near)),dv[near]/.015]
        wt=np.exp(-dd[near]/.000225)+.001
        co=np.linalg.lstsq(a*wt[:,None],U[eyeids[near],2]*wt,rcond=None)[0]
        m0=float(np.clip(co[1:]@direct/.015,-1.5,1.5))
        t=dist[i]/extent
        desired=(2*t**3-3*t*t+1)*rimZ[i]+(t**3-2*t*t+t)*extent*m0+(-2*t**3+3*t*t)*z1+(t**3-t*t)*extent*m1
        target[i]=desired
        weight[i]=angular[i]*smooth(dist[i]/.006)*smooth((extent-dist[i])/.022)
    change=(target-z)*weight*args.strength
    # Bound displacement with a smooth limiter; all colored-eye points fixed.
    change=.045*np.tanh(change/.045);change[pin]=0
    newP=P.copy();newP[:,2]+=change[inv].astype('float32')
    if args.unfold:newP[:,:2]=U[inv,:2]
    f0=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]])
    f1=np.cross(newP[T[:,1]]-newP[T[:,0]],newP[T[:,2]]-newP[T[:,0]])
    sums=np.zeros((num,3))
    for k in range(3):np.add.at(sums,inv[T[:,k]],f1)
    sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-20)[:,None]
    nw=np.clip(weight*4,0,1);nw[pin]=0
    if args.unfold:nw[mask]=1
    newN=N*(1-nw[inv,None])+sums[inv]*nw[inv,None];newN/=np.maximum(np.linalg.norm(newN,axis=1),1e-20)[:,None];newN[nw[inv]==0]=N[nw[inv]==0]
    a0=np.linalg.norm(f0,axis=1);a1=np.linalg.norm(f1,axis=1);valid=a0>1e-12
    cos=np.sum(f0*f1,axis=1)/np.maximum(a0*a1,1e-24)
    scope=mask if args.unfold else weight>0
    checks={'eye_positions_exact':bool(np.array_equal(P[pin[inv]],newP[pin[inv]])),'eye_normals_exact':bool(np.array_equal(N[pin[inv]],newN[pin[inv]])),'all_XY_exact':bool(np.array_equal(P[:,:2],newP[:,:2])),'outside_positions_exact':bool(np.array_equal(P[~scope[inv]],newP[~scope[inv]])),'opposite_eye_exact':bool(np.array_equal(P[P[:,0]>0],newP[P[:,0]>0])),'bounds_exact':bool(np.array_equal(P.min(0),newP.min(0)) and np.array_equal(P.max(0),newP.max(0))),'new_degenerate':int(((a1<1e-12)&valid).sum()),'faces_rotated_over60':int(((cos<.5)&valid).sum()),'faces_rotated_over90':int(((cos<0)&valid).sum()),'min_area_ratio':float((a1[valid]/a0[valid]).min()),'changed_vertices':int(np.any(P!=newP,axis=1).sum()),'max_axis_delta':abs(newP-P).max(0).tolist(),'delta_z_range':[float((newP-P)[:,2].min()),float((newP-P)[:,2].max())],'new_XY_reversed_faces':int(((f0[:,2]>1e-10)&(f1[:,2]<-1e-10)&np.any(scope[inv[T]],axis=1)).sum())}
    binary=bytearray(raw);store_accessor(g,binary,at['POSITION'],newP);store_accessor(g,binary,at['NORMAL'],newN)
    output=out/'lulu-under-eye.glb';write(output,copy.deepcopy(g),binary)
    np.savez(out/'correction.npz',P=P,newP=newP,delta=newP-P,eye=pin[inv],weight=weight[inv],target=target[inv])
    report={'revision':args.rev,'base':str(source.relative_to(R)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'method':'Hermite depth reconstruction, fixed painted eye and outer cheek, one right eye only','checks':checks,'texture_bytes_unchanged':True,'topology_unchanged':True,'candidate_only':True}
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
