"""Repair the user's red-box cheek mark, independent from the painted eye rim.

Source: backed-up leftfix r3. All X/Y, painted eyes, head outline and body stay
unchanged. Geometry and local color repairs are saved as separate candidates.
"""
import argparse,hashlib,io,json,struct
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor,smoothstep

ROOT=R/'review/lulu-cheek-mark-20261018'
BASE=ROOT/'baseline/lulu-meshy-leftfix.glb'

def scope(p):
    x,y,z=np.asarray(p).T
    q=np.sqrt(((x+.361)/.077)**2+((y-.446)/.038)**2)
    weight=smoothstep((1.12-q)/.48)*smoothstep((-.303-x)/.016)*smoothstep((z-.12)/.04)
    return q,weight

def design(p):
    x=(p[:,0]+.361)/.077;y=(p[:,1]-.446)/.038
    return np.c_[np.ones(len(p)),x,y,x*x,x*y,y*y]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='r1');ap.add_argument('--limit',type=float,default=.009)
    ap.add_argument('--method',choices=['boundary','local'],default='local')
    ap.add_argument('--patch-radius',type=float,default=1)
    args=ap.parse_args();dest=ROOT/args.revision;dest.mkdir(exist_ok=False)
    data,g,raw=read_glb(BASE);attrs=g['meshes'][0]['primitives'][0]['attributes']
    P=accessor(g,raw,attrs['POSITION']).copy();N=accessor(g,raw,attrs['NORMAL']).copy();UV=accessor(g,raw,attrs['TEXCOORD_0']).copy()
    tris=[accessor(g,raw,p['indices']).reshape(-1,3) for p in g['meshes'][0]['primitives']];tri=np.concatenate(tris)
    _,inv=np.unique(np.round(P,6),axis=0,return_inverse=True);count=np.bincount(inv);num=len(count)
    average=lambda a:np.stack([np.bincount(inv,weights=a[:,k])/count for k in range(a.shape[1])],axis=1)
    U=average(P);ut=inv[tri];q,weight=scope(U)
    iv=g['bufferViews'][g['images'][0]['bufferView']]
    image=np.array(Image.open(io.BytesIO(raw[iv['byteOffset']:iv['byteOffset']+iv['byteLength']])).convert('RGB'))
    h,w=image.shape[:2];C0=image[(UV[:,1]*(h-1)).astype(int).clip(0,h-1),(UV[:,0]*(w-1)).astype(int).clip(0,w-1)].astype(float);C=average(C0)
    skin=(C[:,0]>240)&(C[:,1]>210)&(C[:,2]>95)&(C[:,2]<165)
    # Healthy surrounding skin alone determines the smooth local continuation.
    eyeq=np.sqrt(((U[:,0]+.232)/.079)**2+((U[:,1]-.525)/.07)**2)
    healthy=(q>1.15)&(q<1.9)&(eyeq>1.45)&(U[:,2]>.12)&skin
    area=np.linalg.norm(np.cross(U[ut[:,1]]-U[ut[:,0]],U[ut[:,2]]-U[ut[:,0]]),axis=1)
    mass=np.zeros(num)
    for k in range(3):np.add.at(mass,ut[:,k],area/3)
    A=design(U);a=A[healthy];target=U[healthy,2];fitting=np.sqrt(mass[healthy]);fitting/=fitting.max()
    coef=np.linalg.lstsq(a*fitting[:,None],target*fitting,rcond=None)[0]
    for _ in range(3):
        robust=1/np.maximum(1,np.abs(a@coef-target)/.008)
        wi=fitting*robust;coef=np.linalg.lstsq(a*wi[:,None],target*wi,rcond=None)[0]
    targetZ=A@coef
    if args.method=='local':
        # Reconstruct only the short high-frequency ridge. The broad boundary
        # fit overestimates cheek depth and merely translates the entire patch.
        # Area-weighted local quadratic patches retain the underlying cheek arc.
        pool=(q<2.2)&(U[:,2]>.12)&(eyeq>1.15)&skin
        for i in np.flatnonzero(weight>0):
            xy=(U[:,:2]-U[i,:2])/(np.array([.035,.021])*args.patch_radius)
            radius=np.sum(xy*xy,axis=1)
            near=pool&(radius<1.8**2)
            axy=xy[near];xx,yy=axy.T
            local=np.c_[np.ones(len(xx)),xx,yy,xx*xx,xx*yy,yy*yy]
            wt=np.sqrt(mass[near]*np.exp(-2*radius[near]))
            localcoef=np.linalg.lstsq(local*wt[:,None],U[near,2]*wt,rcond=None)[0]
            targetZ[i]=localcoef[0]
    shift=args.limit*np.tanh((targetZ-U[:,2])/args.limit)*weight
    newP=P.copy();newP[:,2]+=shift[inv].astype(np.float32)
    f0=np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]])
    f=np.cross(newP[tri[:,1]]-newP[tri[:,0]],newP[tri[:,2]]-newP[tri[:,0]])
    sums=np.zeros((num,3))
    for k in range(3):np.add.at(sums,ut[:,k],f)
    sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-20)[:,None]
    nw=np.minimum(weight*3,1)[inv];newN=N*(1-nw[:,None])+sums[inv]*nw[:,None]
    newN/=np.maximum(np.linalg.norm(newN,axis=1),1e-20)[:,None];newN[nw==0]=N[nw==0]
    a0=np.linalg.norm(f0,axis=1);a1=np.linalg.norm(f,axis=1);valid=a0>1e-12
    cosine=np.sum(f*f0,axis=1)/np.maximum(a0*a1,1e-24)
    # A separate color-only candidate allows the geometric result to be judged
    # independently. Rasterization is limited to source material 0 and the box.
    colorcoef=np.linalg.lstsq(a*fitting[:,None],C[healthy]*fitting[:,None],rcond=None)[0]
    alpha=np.zeros((h,w),dtype=np.float32);outimage=image.astype(float).copy()
    candidates=tris[0][np.any(weight[inv[tris[0]]]>0,axis=1)]
    for t in candidates:
        uv=UV[t]*[w-1,h-1];lo=np.maximum(np.floor(uv.min(0)).astype(int)-1,0);hi=np.minimum(np.ceil(uv.max(0)).astype(int)+1,[w-1,h-1])
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];d=uv[1:]-uv[0];det=d[0,0]*d[1,1]-d[0,1]*d[1,0]
        if abs(det)<1e-8:continue
        dx=xx-uv[0,0];dy=yy-uv[0,1];b1=(dx*d[1,1]-dy*d[1,0])/det;b2=(dy*d[0,0]-dx*d[0,1])/det;b0=1-b1-b2
        inside=(b0>=-1e-6)&(b1>=-1e-6)&(b2>=-1e-6)
        points=b0[...,None]*P[t[0]]+b1[...,None]*P[t[1]]+b2[...,None]*P[t[2]]
        _,strength=scope(points.reshape(-1,3));strength=strength.reshape(xx.shape)*inside
        old=image[yy,xx].astype(float)
        strength*=smoothstep((old[...,0]-235)/15)*smoothstep((old[...,1]-210)/15)*smoothstep((old[...,2]-95)/15)*smoothstep((170-old[...,2])/25)
        targetcolor=np.clip(design(points.reshape(-1,3))@colorcoef,[245,219,105],[255,237,145]).reshape((*xx.shape,3))
        replace=strength>alpha[yy,xx];color=old*(1-strength[...,None])+targetcolor*strength[...,None]
        outimage[yy[replace],xx[replace]]=color[replace];alpha[yy[replace],xx[replace]]=strength[replace]
    outimage=np.round(outimage).astype(np.uint8);image_changed=int(np.any(outimage!=image,axis=2).sum())
    Image.fromarray((alpha*255).astype('uint8')).save(dest/'texture-mask.png')
    np.savez(dest/'correction.npz',delta=newP-P,scope=weight[inv],normal_weight=nw,fit=coef)
    checks={'all_XY_exact':bool(np.array_equal(P[:,:2],newP[:,:2])),'outside_scope_positions_exact':bool(np.array_equal(P[weight[inv]==0],newP[weight[inv]==0])),'outside_scope_normals_exact':bool(np.array_equal(N[nw==0],newN[nw==0])),'eye_region_positions_exact':bool(np.array_equal(P[P[:,0]>-.303],newP[P[:,0]>-.303])),'eye_region_normals_exact':bool(np.array_equal(N[P[:,0]>-.303],newN[P[:,0]>-.303])),'head_bounds_exact':bool(np.array_equal(P.min(0),newP.min(0)) and np.array_equal(P.max(0),newP.max(0))),'changed_vertices':int(np.any(P!=newP,axis=1).sum()),'max_axis_delta':np.abs(P-newP).max(0).tolist(),'new_degenerate':int(((a1<1e-12)&valid).sum()),'faces_rotated_over60deg':int(((cosine<.5)&valid).sum()),'min_area_ratio':float((a1[valid]/a0[valid]).min()),'color_changed_pixels':image_changed}
    assert all(v for v in checks.values() if isinstance(v,bool))
    assert checks['new_degenerate']==0 and checks['faces_rotated_over60deg']==0 and checks['min_area_ratio']>.4,checks
    reports={}
    for kind in ['geometry','texture','combined']:
        import copy
        doc=copy.deepcopy(g);buf=bytearray(raw)
        if kind!='texture':accessor(doc,buf,attrs['POSITION'])[:]=newP;accessor(doc,buf,attrs['NORMAL'])[:]=newN
        if kind!='geometry':
            stream=io.BytesIO();Image.fromarray(outimage).save(stream,format='PNG');buf.extend(b'\0'*((-len(buf))%4));offset=len(buf);buf.extend(stream.getvalue())
            doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(stream.getvalue())});doc['images'][0]={'bufferView':len(doc['bufferViews'])-1,'mimeType':'image/png'}
        doc['buffers'][0]['byteLength']=len(buf);j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);buf.extend(b'\0'*((-len(buf))%4))
        out=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf
        (dest/f'{kind}.glb').write_bytes(out);reports[kind]={'sha256':hashlib.sha256(out).hexdigest(),'bytes':len(out)}
    report={'revision':args.revision,'method':args.method,'patch_radius':args.patch_radius,'source_sha256':hashlib.sha256(data).hexdigest(),'scope':'red-box outer-lower cheek only; x<-.303','checks':checks,'outputs':reports}
    (dest/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
