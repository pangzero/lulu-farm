"""One-sided skin correction from the backed-up crease candidate.

Actual eye-color vertices, every X/Y, UV, indices and non-local geometry are pinned.
An interpolating depth field joins fixed eye-border samples to healthy outer skin.
Run revisions separately; never overwrite the source or a previous candidate.
"""
from pathlib import Path
import argparse, hashlib, heapq, io, json, struct
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R, read_glb, accessor, smoothstep

ROOT=R/'review/lulu-left-eye-20261018'
BASE=ROOT/'baseline/lulu-meshy-crease.glb'

def tps(points,values):
    origin=np.array([-.232,.525]);scale=.10
    q=(points-origin)/scale
    def kernel(a,b):
        r2=np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)
        return .5*r2*np.log(np.maximum(r2,1e-20))
    P=np.c_[np.ones(len(q)),q]
    A=np.block([[kernel(q,q)+np.eye(len(q))*1e-7,P],[P.T,np.zeros((3,3))]])
    rhs=np.r_[values,np.zeros(3)]
    coef=np.linalg.solve(A,rhs)
    def field(xy):
        v=(xy-origin)/scale
        return kernel(v,q)@coef[:-3]+np.c_[np.ones(len(v)),v]@coef[-3:]
    return field

def spread_sample(ids,points,cell):
    key=np.round(points[ids,:2]/cell).astype(int)
    _,first=np.unique(key,axis=0,return_index=True)
    return ids[first]

def convex_boundary(ids,points):
    ordered=sorted(ids,key=lambda i:(points[i,0],points[i,1]))
    def cross(a,b,c):
        u=points[b,:2]-points[a,:2];v=points[c,:2]-points[a,:2]
        return u[0]*v[1]-u[1]*v[0]
    lower=[];upper=[]
    for i in ordered:
        while len(lower)>=2 and cross(lower[-2],lower[-1],i)<=0:lower.pop()
        lower.append(i)
    for i in ordered[::-1]:
        while len(upper)>=2 and cross(upper[-2],upper[-1],i)<=0:upper.pop()
        upper.append(i)
    return np.array(lower[:-1]+upper[:-1],dtype=int)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='r1');ap.add_argument('--limit',type=float,default=.022)
    ap.add_argument('--strength',type=float,default=.85);ap.add_argument('--texture',action='store_true');ap.add_argument('--hull',action='store_true')
    ap.add_argument('--negative-limit',type=float,default=0);ap.add_argument('--feather',type=float,default=.020)
    args=ap.parse_args();outdir=ROOT/args.revision;outdir.mkdir(exist_ok=False)
    data,g,raw=read_glb(BASE);pr=g['meshes'][0]['primitives'][0];attrs=pr['attributes']
    p0=accessor(g,raw,attrs['POSITION']).copy();n0=accessor(g,raw,attrs['NORMAL']).copy();uv=accessor(g,raw,attrs['TEXCOORD_0']).copy()
    tri=np.concatenate([accessor(g,raw,p['indices']).reshape(-1,3) for p in g['meshes'][0]['primitives']])
    view=g['bufferViews'][g['images'][0]['bufferView']]
    pixels=np.array(Image.open(io.BytesIO(raw[view['byteOffset']:view['byteOffset']+view['byteLength']])).convert('RGB'))
    h,w=pixels.shape[:2];C0=pixels[(uv[:,1]*(h-1)).astype(int).clip(0,h-1),(uv[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float)
    _,inv=np.unique(np.round(p0,6),axis=0,return_inverse=True);count=np.bincount(inv);N=len(count)
    avg=lambda a:np.stack([np.bincount(inv,weights=a[:,k])/count for k in range(a.shape[1])],axis=1)
    U=avg(p0);C=avg(C0);ut=inv[tri];x,y,z=U.T
    Q=np.sqrt(((x+.232)/.079)**2+((y-.525)/.07)**2)
    local=(x>-.445)&(x<-.075)&(y>.375)&(y<.66)&(z>.10)
    eye_color=((C0.min(1)>160)&((C0.max(1)-C0.min(1))<65))|((C0[:,2]>C0[:,0]*.84)&(C0[:,2]>C0[:,1]*.84))
    pin=np.bincount(inv,weights=eye_color.astype(int),minlength=N)>0
    pin&=local&(Q<1.18)
    color_pin=pin.copy()
    hull=convex_boundary(np.flatnonzero(pin),U)
    outside=np.zeros(N);inside=np.ones(N,dtype=bool);hull_dist=np.full(N,np.inf)
    for ia,ib in zip(hull,np.roll(hull,-1)):
        a=U[ia,:2];v=U[ib,:2]-a;d=U[:,:2]-a
        cross=v[0]*d[:,1]-v[1]*d[:,0]
        inside&=cross>=-1e-9
        t=np.clip((d@v)/(v@v),0,1)
        hull_dist=np.minimum(hull_dist,np.linalg.norm(d-t[:,None]*v,axis=1))
    if args.hull:pin|=inside&local
    skin=(C[:,0]>230)&(C[:,1]>185)&(C[:,2]<170)
    edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
    el=edges[local[edges[:,0]]&local[edges[:,1]]]
    boundary_edges=el[pin[el[:,0]]!=pin[el[:,1]]]
    border=np.unique(boundary_edges[pin[boundary_edges]])
    border=spread_sample(border,U,.006)
    if args.hull:border=hull
    # Exclude the folded lower skin from the target constraints. Its long tail
    # reaches leftwards farther than the central eye ellipse.
    tail=np.sqrt(((x+.351)/.086)**2+((y-.468)/.034)**2)
    outer=local&skin&(Q>1.70)&(Q<2.45)&(tail>1.25)
    outer_ids=spread_sample(np.flatnonzero(outer),U,.015)
    # Close healthy forehead samples retain the small upper-eye rise.
    upper_ids=spread_sample(np.flatnonzero(local&skin&(Q>1.25)&(Q<1.75)&(y>.59)),U,.012)
    constraints=np.unique(np.r_[border,outer_ids,upper_ids])
    field=tps(U[constraints,:2],U[constraints,2])
    ids=np.flatnonzero(local);target=U[:,2].copy();target[ids]=field(U[ids,:2])
    adj={int(i):[] for i in ids}
    for a,b in el:
        d=float(np.linalg.norm(U[a]-U[b]));adj[int(a)].append((int(b),d));adj[int(b)].append((int(a),d))
    dist=np.full(N,np.inf);queue=[]
    for i in np.flatnonzero(pin):dist[i]=0;heapq.heappush(queue,(0,int(i)))
    while queue:
        d,i=heapq.heappop(queue)
        if d!=dist[i] or d>.22:continue
        for j,dd in adj[i]:
            nd=d+dd
            if nd<dist[j]:dist[j]=nd;heapq.heappush(queue,(nd,j))
    # Full effect at the visible lower/inner defect; gently feather externally.
    patch=np.maximum(smoothstep((2.05-Q)/.65),smoothstep((1.22-tail)/.45))
    patch*=smoothstep((.62-y)/.045)*smoothstep((y-.39)/.045)
    patch*=smoothstep((x+.445)/.035)*smoothstep((-.08-x)/.035)
    patch*=smoothstep((hull_dist if args.hull else dist)/(args.feather if args.hull else .007))
    patch[pin|~local]=0
    desired=target-z
    limit=np.where(desired<0,args.negative_limit or args.limit,args.limit)
    shift=limit*np.tanh(desired/limit)*patch*args.strength
    P=p0.copy();P[:,2]+=shift[inv].astype(np.float32)
    changed=np.any(P!=p0,axis=1)
    # Blend geometric normals over the complete affected one-ring, not only
    # exactly moved vertices. The painted eye normals remain unchanged.
    face=np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]])
    sums=np.zeros((N,3))
    for k in range(3):np.add.at(sums,inv[tri[:,k]],face)
    sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-12)[:,None]
    nw=np.minimum(1,patch*4);nw[pin|~local]=0
    normals=n0*(1-nw[inv,None])+sums[inv]*nw[inv,None]
    normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-12)[:,None]
    normals[nw[inv]==0]=n0[nw[inv]==0]
    binary=bytearray(raw)
    accessor(g,binary,attrs['POSITION'])[:]=P
    accessor(g,binary,attrs['NORMAL'])[:]=normals
    texture_count=0
    if args.texture:
        # Rasterize only local source triangles to the original UV chart. Build
        # a smooth skin-color field from healthy skin, never touch eye pixels.
        fit=outer&skin&(y>.44)
        X=(x+.232)/.12;Y=(y-.525)/.10
        A=np.c_[np.ones(N),X,Y,X*Y,X*X,Y*Y]
        coef=np.linalg.lstsq(A[fit],C[fit],rcond=None)[0]
        output=pixels.astype(float).copy();alpha=np.zeros((h,w),dtype=np.float32)
        candidates=tri[np.all(local[ut],axis=1)&~np.any(pin[ut],axis=1)]
        for t in candidates:
            tuv=uv[t]*[w-1,h-1];lo=np.maximum(np.floor(tuv.min(0)).astype(int)-1,0);hi=np.minimum(np.ceil(tuv.max(0)).astype(int)+1,[w-1,h-1])
            if np.any(hi<lo):continue
            yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            d=tuv[1:]-tuv[0];det=d[0,0]*d[1,1]-d[0,1]*d[1,0]
            if abs(det)<1e-8:continue
            dx=xx-tuv[0,0];dy=yy-tuv[0,1]
            b1=(dx*d[1,1]-dy*d[1,0])/det;b2=(dy*d[0,0]-dx*d[0,1])/det;b0=1-b1-b2
            inside=(b0>=-1e-6)&(b1>=-1e-6)&(b2>=-1e-6)
            pp=b0[...,None]*p0[t[0]]+b1[...,None]*p0[t[1]]+b2[...,None]*p0[t[2]]
            xxp,yyp,zzp=pp.transpose(2,0,1)
            q=np.sqrt(((xxp+.232)/.079)**2+((yyp-.525)/.07)**2)
            ta=np.sqrt(((xxp+.35)/.09)**2+((yyp-.468)/.038)**2)
            a=np.maximum(smoothstep((1.6-q)/.4),smoothstep((1.2-ta)/.5))
            a*=smoothstep((q-1.06)/.16)*smoothstep((.555-yyp)/.05)*smoothstep((yyp-.435)/.025)*inside
            old=pixels[yy,xx].astype(float)
            # Yellow skin only; spare white/blue/black and orange muzzle.
            a*=smoothstep((old[...,0]-205)/30)*smoothstep((old[...,1]-200)/20)*smoothstep((200-old[...,2])/45)
            xp=(xxp+.232)/.12;yp=(yyp-.525)/.10
            aa=np.stack([np.ones_like(xp),xp,yp,xp*yp,xp*xp,yp*yp],axis=-1)
            col=np.clip(aa@coef,[245,218,105],[255,236,137])
            old_alpha=alpha[yy,xx];choose=a>old_alpha
            new=old*(1-a[...,None])+col*a[...,None]
            output[yy[choose],xx[choose]]=new[choose];alpha[yy[choose],xx[choose]]=a[choose]
        result_pixels=np.round(output).astype(np.uint8)
        texture_count=int(np.any(result_pixels!=pixels,axis=2).sum())
        stream=io.BytesIO();Image.fromarray(result_pixels).save(stream,format='PNG')
        binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(stream.getvalue())
        g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(stream.getvalue())})
        g['images'][0]={'mimeType':'image/png','bufferView':len(g['bufferViews'])-1}
        Image.fromarray((alpha*255).astype(np.uint8)).save(outdir/'texture-mask.png')
    f0=np.cross(p0[tri[:,1]]-p0[tri[:,0]],p0[tri[:,2]]-p0[tri[:,0]])
    a0=np.linalg.norm(f0,axis=1);an=np.linalg.norm(face,axis=1);valid=a0>1e-12
    cos=np.sum(face*f0,axis=1)/np.maximum(a0*an,1e-24)
    g['buffers'][0]['byteLength']=len(binary)
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary.extend(b'\0'*((-len(binary))%4))
    out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    output=outdir/'lulu-meshy-leftfix.glb';output.write_bytes(out)
    np.savez(outdir/'correction.npz',delta=P-p0,eye=pin[inv],scope=patch[inv],normal_weight=nw[inv],constraints=U[constraints],target=target)
    report={'revision':args.revision,'base_sha256':hashlib.sha256(data).hexdigest(),'sha256':hashlib.sha256(out).hexdigest(),'changed_vertices':int(changed.sum()),'max_axis_delta':np.abs(P-p0).max(0).tolist(),'eye_positions_exact':bool(np.array_equal(P[pin[inv]],p0[pin[inv]])),'eye_normals_exact':bool(np.array_equal(normals[pin[inv]],n0[pin[inv]])),'all_XY_exact':bool(np.array_equal(P[:,:2],p0[:,:2])),'other_side_positions_exact':bool(np.array_equal(P[p0[:,0]>=0],p0[p0[:,0]>=0])),'outside_scope_positions_exact':bool(np.array_equal(P[patch[inv]==0],p0[patch[inv]==0])),'new_degenerate':int(((an<1e-12)&valid).sum()),'reversed_faces_over90deg':int(((cos<0)&valid).sum()),'min_area_ratio':float((an[valid]/a0[valid]).min()),'texture_changed_pixels':texture_count,'constraints':len(constraints),'candidate_only':True}
    (outdir/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
