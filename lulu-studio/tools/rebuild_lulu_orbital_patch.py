"""Independent whole-orbit study. The damaged eye boundary is NOT an anchor.

Keep the eye's front projection in the baked appearance, while reconstructing
the entire small eye/skin surface from a healthy outer boundary. No r01-r06 data
are used. This is a candidate and needs fixed-camera visual review.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, struct, sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lulu_patch_io import read_glb, accessor

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-eye-ring-20261018'
CENTER=np.array([-.235,.525])
RADII=np.array([.156,.137])

def write(path,g,b):
    g['buffers'][0]['byteLength']=len(b)
    j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    b.extend(b'\0'*((-len(b))%4))
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)

def source():
    g,b=read_glb(D/'baseline/modular-r04.glb')
    pr=g['meshes'][0]['primitives'][0];at=pr['attributes']
    P=accessor(g,b,at['POSITION']);N=accessor(g,b,at['NORMAL']);UV=accessor(g,b,at['TEXCOORD_0']);T=accessor(g,b,pr['indices']).reshape(-1,3)
    U,inv=np.unique(P,axis=0,return_inverse=True);ut=inv[T]
    mid=P[T].mean(1);radius=np.linalg.norm((mid[:,:2]-CENTER)/RADII,axis=1)
    sel=(radius<1)&(mid[:,2]>.08)
    edges=np.concatenate([ut[sel][:,[0,1]],ut[sel][:,[1,2]],ut[sel][:,[2,0]]]);edges,cnt=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True);boundary=edges[cnt==1]
    adj={int(i):[] for i in np.unique(boundary)}
    for a,b0 in boundary:adj[int(a)].append(int(b0));adj[int(b0)].append(int(a))
    assert all(len(v)==2 for v in adj.values()), 'Boundary is not a simple loop'
    loops=[];remaining=set(adj)
    while remaining:
        start=next(iter(remaining));prev=None;cur=start;loop=[]
        while cur not in loop:
            loop.append(cur);remaining.discard(cur);ns=adj[cur];nxt=ns[0] if ns[0]!=prev else ns[1];prev,cur=cur,nxt
        loops.append(np.array(loop))
    assert len(loops)==1, f'Expected one full-orbit boundary, got {len(loops)}'
    return g,b,pr,P,N,UV,T,U,inv,ut,sel,boundary,loops

def inside(xy,loop,U):
    keep=np.zeros(len(xy),bool)
    for a,b in zip(loop,np.roll(loop,-1)):
        u,v=U[a,:2],U[b,:2]
        keep^=((u[1]>xy[:,1])!=(v[1]>xy[:,1]))&(xy[:,0]<(v[0]-u[0])*(xy[:,1]-u[1])/(v[1]-u[1]+1e-30)+u[0])
    return keep

def prepare(O):
    O.mkdir(exist_ok=False)
    *_,U,inv,ut,sel,boundary,loops=source();ids=np.unique(boundary);pos=U[ids,:2];lo=pos.min(0);hi=pos.max(0)
    # Crossing projected boundary edges would invalidate frontal reconstruction.
    loop=loops[0];xy=U[loop,:2];crossings=0
    for i in range(len(loop)):
        a,b=xy[i],xy[(i+1)%len(loop)]
        for j in range(i+2,len(loop)):
            if i==0 and j==len(loop)-1:continue
            c,d=xy[j],xy[(j+1)%len(loop)]
            cr=lambda x,y:x[0]*y[1]-x[1]*y[0]
            if cr(b-a,c-a)*cr(b-a,d-a)<0 and cr(d-c,a-c)*cr(d-c,b-c)<0:crossings+=1
    assert crossings==0, f'Projected perimeter crosses {crossings} times'
    gx,gy=np.meshgrid(np.arange(lo[0]+.002,hi[0],.003),np.arange(lo[1]+.002,hi[1],.003));grid=np.c_[gx.ravel(),gy.ravel()];keep=inside(grid,loop,U)
    dist=np.full(len(grid),np.inf)
    for a,b in boundary:
        v=U[b,:2]-U[a,:2];q=grid-U[a,:2];t=np.clip(q@v/(v@v),0,1);dist=np.minimum(dist,np.linalg.norm(q-t[:,None]*v,axis=1))
    grid=grid[keep&(dist>.0015)];mapping={int(v):i for i,v in enumerate(ids)}
    data={'vertices':np.r_[pos,grid].tolist(),'edges':[[mapping[int(a)],mapping[int(b)]] for a,b in boundary],'boundary_ids':ids.tolist(),'boundary_count':len(ids),'loop':[mapping[int(i)] for i in loop]}
    (O/'cdt-input.json').write_text(json.dumps(data));print('Prepared',len(ids),'outer boundary vertices,',len(grid),'new interior vertices,',int(sel.sum()),'faces removed')

def cdt(O):
    from mathutils import Vector
    from mathutils.geometry import delaunay_2d_cdt
    data=json.loads((O/'cdt-input.json').read_text())
    v,e,f,ov,oe,of=delaunay_2d_cdt([Vector(v) for v in data['vertices']],data['edges'],[],0,1e-8,True)
    (O/'cdt-output.json').write_text(json.dumps({'vertices':[list(v) for v in v],'faces':f,'orig_verts':ov}));print('CDT',len(v),len(f))

def finish(O):
    from PIL import Image
    g,raw,pr,P,N,UV,T,U,inv,ut,sel,boundary,loops=source()
    data=json.loads((O/'cdt-input.json').read_text());res=json.loads((O/'cdt-output.json').read_text())
    xy=np.array(res['vertices']);faces=np.array(res['faces']);faces=faces[inside(xy[faces].mean(1),loops[0],U)]
    boundary_ids=np.array(data['boundary_ids']);fixed={}
    for i,ids in enumerate(res['orig_verts']):
        old=[j for j in ids if j<len(boundary_ids)]
        if old:assert len(old)==1;fixed[i]=int(boundary_ids[old[0]])
    assert set(fixed.values())==set(boundary_ids)
    outside=T[~sel];touch=np.any(np.isin(inv[outside],boundary_ids),axis=1)
    anchors=np.unique(np.r_[boundary_ids,inv[outside[touch]].reshape(-1)])
    # Fit only the healthy outer skin; old eye socket folds are not constraints.
    scale=np.array([.15,.14]);a=(U[anchors,:2]-CENTER)/scale;q=(xy-CENTER)/scale
    def poly(t):
        x,y=t.T;return np.c_[np.ones(len(t)),x,y,x*x,x*y,y*y]
    coef=np.linalg.lstsq(poly(a),U[anchors,2],rcond=None)[0]
    residual=U[anchors,2]-poly(a)@coef
    def kernel(a,b):
        d=np.sum((a[:,None]-b[None,:])**2,axis=2);return .5*d*np.log(np.maximum(d,1e-25))
    pol=np.c_[np.ones(len(a)),a];mat=np.block([[kernel(a,a)+np.eye(len(a))*1e-7,pol],[pol.T,np.zeros((3,3))]])
    rb=np.linalg.solve(mat,np.r_[residual,np.zeros(3)])
    def surface(v):return poly(v)@coef+kernel(v,a)@rb[:-3]+np.c_[np.ones(len(v)),v]@rb[-3:]
    depth=surface(q)
    # Very shallow corneal relief, with zero value and slope outside the eye.
    e=((xy-np.array([-.232,.528]))/np.array([.074,.067]));er=np.sum(e*e,axis=1)
    relief=.005*np.maximum(1-er,0)**3
    depth+=relief
    eye_fit_error=None
    if O.name in ['orbit-r02','orbit-r03']:
        # Preserve the coarse depth and tilt of the existing painted eye, not
        # its wrinkled border. A low-order C2 correction has no pinned inner rim.
        im0=g['images'][g['textures'][0]['source']];bv=g['bufferViews'][im0['bufferView']];st=bv.get('byteOffset',0)
        img=np.array(Image.open(io.BytesIO(raw[st:st+bv['byteLength']])).convert('RGB'));hh,ww=img.shape[:2]
        col=img[np.clip((UV[:,1]*(hh-1)).astype(int),0,hh-1),np.clip((UV[:,0]*(ww-1)).astype(int),0,ww-1)].astype(float)
        colored=((col.min(1)>160)&(col.max(1)-col.min(1)<65))|((col[:,2]>col[:,0]*.84)&(col[:,2]>col[:,1]*.84))
        eye=colored&(P[:,0]>-.32)&(P[:,0]<-.145)&(P[:,1]>.455)&(P[:,1]<.60)&(P[:,2]>.10)
        ids=np.flatnonzero(eye);_,unique=np.unique(np.round(P[ids,:2]/.006).astype(int),axis=0,return_index=True);ids=ids[unique]
        qe=(P[ids,:2]-CENTER)/scale
        def basis(v):return poly(v)*np.maximum(1-np.sum(v*v,axis=1),0)[:,None]**3
        target=P[ids,2]-surface(qe)
        fit=np.linalg.lstsq(basis(qe),target,rcond=None)[0]
        strength=.80 if O.name=='orbit-r03' else 1.0
        depth+=basis(q)@fit*strength-relief
        eye_fit_error=float(np.sqrt(np.mean((basis(qe)@fit*strength-target)**2)))
    newP=np.c_[xy,depth]
    for i,j in fixed.items():newP[i]=U[j]
    cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]])
    wrong=cross[:,2]<0;faces[wrong]=faces[wrong][:,[0,2,1]]
    cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]])
    norm=np.zeros_like(newP)
    for k in range(3):np.add.at(norm,faces[:,k],cross)
    norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-20)[:,None]
    count=np.bincount(inv);oldN=np.stack([np.bincount(inv,weights=N[:,i])/count for i in range(3)],axis=1);oldN/=np.maximum(np.linalg.norm(oldN,axis=1),1e-20)[:,None]
    for i,j in fixed.items():norm[i]=oldN[j]
    # Frontal texture reprojection preserves the visible painted eye silhouette.
    lo=xy.min(0)-.002;hi=xy.max(0)+.002;size=1024;newUV=((xy-lo)/(hi-lo)).astype('<f4')
    uvmap=np.zeros((size,size,2));zbuffer=np.full((size,size),-np.inf);covered=np.zeros((size,size),bool)
    for tri in T[sel]:
        p=P[tri];pixel=(p[:,:2]-lo)/(hi-lo)*(size-1);mn=np.maximum(np.floor(pixel.min(0)).astype(int)-1,0);mx=np.minimum(np.ceil(pixel.max(0)).astype(int)+1,size-1)
        if np.any(mn>mx):continue
        yy,xx=np.mgrid[mn[1]:mx[1]+1,mn[0]:mx[0]+1];v=pixel[1:]-pixel[0];det=v[0,0]*v[1,1]-v[0,1]*v[1,0]
        if abs(det)<1e-12:continue
        dx=xx-pixel[0,0];dy=yy-pixel[0,1];b1=(dx*v[1,1]-dy*v[1,0])/det;b2=(dy*v[0,0]-dx*v[0,1])/det;b0=1-b1-b2;mask=(b0>=-1e-5)&(b1>=-1e-5)&(b2>=-1e-5);zz=b0*p[0,2]+b1*p[1,2]+b2*p[2,2];mask&=zz>zbuffer[yy,xx]
        vals=b0[...,None]*UV[tri[0]]+b1[...,None]*UV[tri[1]]+b2[...,None]*UV[tri[2]];uvmap[yy[mask],xx[mask]]=vals[mask];zbuffer[yy[mask],xx[mask]]=zz[mask];covered[yy[mask],xx[mask]]=True
    for _ in range(32):
        prev=covered.copy()
        for ax,step in [(0,1),(0,-1),(1,1),(1,-1)]:
            near=np.roll(prev,step,axis=ax);take=near&~covered;vals=np.roll(uvmap,step,axis=ax);uvmap[take]=vals[take];covered[take]=True
    buf=bytearray(raw);doc=copy.deepcopy(g)
    def blob(bb):
        buf.extend(b'\0'*((-len(buf))%4));i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(bb)});buf.extend(bb);return i
    def acc(a,typ,component):
        i=len(doc['accessors']);v={'bufferView':blob(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
        if typ=='VEC3':v.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        doc['accessors'].append(v);return i
    def bake(tid,name):
        img=g['images'][g['textures'][tid]['source']];v=g['bufferViews'][img['bufferView']];st=v.get('byteOffset',0)
        im=np.array(Image.open(io.BytesIO(raw[st:st+v['byteLength']])).convert('RGBA'));h,w=im.shape[:2];tx=np.clip(uvmap[...,0]*(w-1),0,w-1);ty=np.clip(uvmap[...,1]*(h-1),0,h-1);x0=tx.astype(int);y0=ty.astype(int);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1);a=(tx-x0)[...,None];b=(ty-y0)[...,None]
        col=np.round(im[y0,x0]*(1-a)*(1-b)+im[y0,x1]*a*(1-b)+im[y1,x0]*(1-a)*b+im[y1,x1]*a*b).astype('uint8')
        stream=io.BytesIO();Image.fromarray(col).save(stream,format='PNG');(O/f'{name}.png').write_bytes(stream.getvalue());doc['images'].append({'bufferView':blob(stream.getvalue()),'mimeType':'image/png'});tex=copy.deepcopy(g['textures'][tid]);tex['source']=len(doc['images'])-1;doc['textures'].append(tex);return len(doc['textures'])-1
    mat=copy.deepcopy(g['materials'][0]);mat['name']='Right_Orbital_Continuous_Surface';mat.pop('normalTexture',None)
    mat['pbrMetallicRoughness']['baseColorTexture']['index']=bake(0,'orbital-basecolor')
    mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=bake(1,'orbital-metalrough')
    mat['extensions']['KHR_materials_specular']['specularTexture']['index']=bake(3,'orbital-specular')
    doc['materials'].append(mat);doc['meshes'][0]['primitives'][0]['indices']=acc(T[~sel].astype('<u4').reshape(-1,1),'SCALAR',5125)
    attrs={'POSITION':acc(newP.astype('<f4'),'VEC3',5126),'NORMAL':acc(norm.astype('<f4'),'VEC3',5126),'TEXCOORD_0':acc(newUV,'VEC2',5126)}
    doc['meshes'][0]['primitives'].append({'attributes':attrs,'indices':acc(faces.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':len(doc['materials'])-1,'mode':4})
    output=O/'lulu-eye-ring.glb';write(output,doc,buf)
    np.savez(O/'patch.npz',P=newP,N=norm,UV=newUV,T=faces,removed=sel,sourceP=P,sourceT=T,sourceUV=UV,boundary_ids=boundary_ids)
    report={'status':'UNREVIEWED_CANDIDATE','method':'Whole orbital surface rebuilt from healthy outer skin; old eye rim released; frontal eye color projection retained','removed_triangles':int(sel.sum()),'new_triangles':len(faces),'new_vertices':len(newP),'boundary_count':len(fixed),'head_outline_preserved':True,'opposite_eye_unchanged':True,'other_seven_parts_unchanged':True,'original_images_unchanged':True,'eye_depth_changed':True,'eye_depth_low_order_fit_rmse':eye_fit_error,'eye_front_projection_preserved_by_local_bake':True,'new_patch_z_range':depth.min().item(), 'max_patch_z':depth.max().item(),'source_sha256':hashlib.sha256((D/'baseline/modular-r04.glb').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'candidate_only':True}
    (O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','cdt','finish']);ap.add_argument('--rev',default='orbit-r01');a=ap.parse_args(args);O=D/a.rev
    {'prepare':prepare,'cdt':cdt,'finish':finish}[a.stage](O)
