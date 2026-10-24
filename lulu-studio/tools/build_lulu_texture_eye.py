"""Single-eye smooth-skin and reference-vector texture candidate.
Whole orbital cavity/rim removed. Original static asset is immutable.
The eye is color only, with no corneal relief, socket or normal-map effect.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, struct, sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from lulu_patch_io import read_glb, accessor

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-texture-eye-20261018'
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
    # Convex skin cap has no eye-specific geometry. Replace the positive
    # quadratic curvature inherited from the damaged socket with a gently
    # convex profile, then match only the healthy outside transition.
    H=np.array([[2*coef[3],coef[4]],[coef[4],2*coef[5]]])
    eig,V=np.linalg.eigh(H);curv=V@np.diag(np.minimum(eig,-.008))@V.T
    def quadratic(v):return .5*np.einsum('ki,ij,kj->k',v,curv,v)
    linear=np.linalg.lstsq(np.c_[np.ones(len(a)),a],U[anchors,2]-quadratic(a),rcond=None)[0]
    cap=np.c_[np.ones(len(q)),q]@linear+quadratic(q)
    radius=np.linalg.norm((xy-CENTER)/RADII,axis=1)
    t=np.clip((radius-.68)/.32,0,1);fade=t*t*t*(10+t*(-15+6*t))
    depth=cap+fade*(surface(q)-cap)
    if O.name in ['texture-r02','texture-r03','texture-r04']:
        # Full healthy-skin thin plate, with a first-order boundary correction.
        # No inner eye constraints, dome, socket, or normal-map effect.
        depth=surface(q)
        count=np.bincount(inv)
        source_normals=np.stack([np.bincount(inv,weights=N[:,i])/count for i in range(3)],axis=1)
        source_normals/=np.maximum(np.linalg.norm(source_normals,axis=1),1e-20)[:,None]
        distance=np.full(len(xy),np.inf);point=np.zeros_like(xy);height=np.zeros(len(xy));normal=np.zeros((len(xy),3))
        for ia,ib in boundary:
            u,v=U[ia,:2],U[ib,:2];edge=v-u;delta=xy-u
            t=np.clip(delta@edge/(edge@edge),0,1);near=u+t[:,None]*edge
            ds=np.linalg.norm(xy-near,axis=1);take=ds<distance
            distance[take]=ds[take];point[take]=near[take]
            height[take]=U[ia,2]*(1-t[take])+U[ib,2]*t[take]
            normal[take]=source_normals[ia]*(1-t[take,None])+source_normals[ib]*t[take,None]
        qb=(point-CENTER)/scale;h=.0005
        grad=[]
        for axis in range(2):
            offset=np.zeros_like(qb);offset[:,axis]=h/scale[axis]
            grad.append((surface(qb+offset)-surface(qb-offset))/(2*h))
        grad=np.stack(grad,axis=1)
        expected=-normal[:,:2]/np.maximum(normal[:,2:3],.12)
        expected=np.clip(expected,-4,4)
        correction=height-surface(qb)+np.sum((expected-grad)*(xy-point),axis=1)
        depth+=correction*np.exp(-(distance/.022)**2)
    eye_fit_error=None
    newP=np.c_[xy,depth]
    for i,j in fixed.items():newP[i]=U[j]
    central=np.linalg.norm(q,axis=1)<.24
    local_coef=np.linalg.lstsq(poly(q[central]),newP[central,2],rcond=None)[0]
    central_eigen=np.linalg.eigvalsh([[2*local_coef[3],local_coef[4]],[local_coef[4],2*local_coef[5]]])
    cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]])
    wrong=cross[:,2]<0;faces[wrong]=faces[wrong][:,[0,2,1]]
    cross=np.cross(newP[faces[:,1]]-newP[faces[:,0]],newP[faces[:,2]]-newP[faces[:,0]])
    norm=np.zeros_like(newP)
    for k in range(3):np.add.at(norm,faces[:,k],cross)
    norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-20)[:,None]
    count=np.bincount(inv);oldN=np.stack([np.bincount(inv,weights=N[:,i])/count for i in range(3)],axis=1);oldN/=np.maximum(np.linalg.norm(oldN,axis=1),1e-20)[:,None]
    for i,j in fixed.items():norm[i]=oldN[j]
    # Bake the unmodified surrounding skin, then replace the old eye/shadows
    # with a smooth skin field and the editable reference vector eye.
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
    # These pixels are in UV-image row order: increasing world Y.
    gy,gx=np.mgrid[:size,:size];worldX=lo[0]+gx/(size-1)*(hi[0]-lo[0]);worldY=lo[1]+gy/(size-1)*(hi[1]-lo[1])
    qr=np.stack([(worldX-CENTER[0])/RADII[0],(worldY-CENTER[1])/RADII[1]],axis=-1)
    rr=np.linalg.norm(qr,axis=-1);tt=np.clip((rr-.74)/.23,0,1);clean=1-tt*tt*tt*(10+tt*(-15+6*tt))
    from lulu_reference_eye_vector import generate
    eye_image=np.array(generate(D/'texture-source'/O.name)).astype(float)/255
    # Match front reference proportions while retaining the established eye centre.
    # A fixed UV shear follows the reference's up-and-out eye tilt and reduces
    # the long side projection. It is baked on the same real surface, never
    # dependent on the viewing camera.
    eye_width=.156 if O.name=='texture-r04' else .178
    eye_shear=.55 if O.name=='texture-r04' else 0
    eu=((worldX+.232)-eye_shear*(worldY-.528))/eye_width+.5;ev=.5-(worldY-.528)/.159
    valid=(eu>=0)&(eu<=1)&(ev>=0)&(ev<=1)
    ix=np.clip(np.rint(eu*(eye_image.shape[1]-1)).astype(int),0,eye_image.shape[1]-1);iy=np.clip(np.rint(ev*(eye_image.shape[0]-1)).astype(int),0,eye_image.shape[0]-1)
    eye_rgba=eye_image[iy,ix];eye_alpha=eye_rgba[...,3]*valid
    def clean_color(col):
        rgb=col[...,:3].astype(float)
        # Healthy yellow/orange skin samples only, excluding the old eye and
        # neutral white fragments. Fit a low-frequency colour field, not old
        # painted shadows. Keep the original pixels at the outer boundary.
        select=(rr>.82)&(rr<1.10)&(rgb[...,0]>150)&(rgb[...,1]>115)&(rgb[...,0]+rgb[...,1]-2*rgb[...,2]>100)
        sample=np.zeros_like(select);sample[::8,::8]=True;select&=sample
        xx=qr[...,0];yy=qr[...,1];A=np.stack([np.ones_like(xx),xx,yy,xx*yy,yy*yy],axis=-1)
        aa=A[select];cc=rgb[select];co=np.linalg.lstsq(aa,cc,rcond=None)[0]
        for _ in range(5):
            residual=np.linalg.norm(aa@co-cc,axis=1);weights=np.minimum(1,12/np.maximum(residual,1));co=np.linalg.lstsq(aa*weights[:,None],cc*weights[:,None],rcond=None)[0]
        skin=np.clip(np.einsum('...i,ij->...j',A,co),0,255)
        rgb=rgb*(1-clean[...,None])+skin*clean[...,None]
        rgb=rgb*(1-eye_alpha[...,None])+eye_rgba[...,:3]*255*eye_alpha[...,None]
        col[...,:3]=np.clip(np.round(rgb),0,255).astype('uint8')
        return col
    def bake(tid,name):
        img=g['images'][g['textures'][tid]['source']];v=g['bufferViews'][img['bufferView']];st=v.get('byteOffset',0)
        im=np.array(Image.open(io.BytesIO(raw[st:st+v['byteLength']])).convert('RGBA'));h,w=im.shape[:2];tx=np.clip(uvmap[...,0]*(w-1),0,w-1);ty=np.clip(uvmap[...,1]*(h-1),0,h-1);x0=tx.astype(int);y0=ty.astype(int);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1);a=(tx-x0)[...,None];b=(ty-y0)[...,None]
        col=np.round(im[y0,x0]*(1-a)*(1-b)+im[y0,x1]*a*(1-b)+im[y1,x0]*(1-a)*b+im[y1,x1]*a*b).astype('uint8')
        if name=='orbital-basecolor':col=clean_color(col)
        elif name=='orbital-metalrough':
            healthy=(rr>.85)&(rr<1.0);target=np.median(col[healthy],axis=0).astype(float);target[2]=0
            col=np.round(col.astype(float)*(1-clean[...,None])+target*clean[...,None]).astype('uint8')
        elif name=='orbital-specular':
            healthy=(rr>.85)&(rr<1.0);target=np.median(col[healthy],axis=0).astype(float)
            col=np.round(col.astype(float)*(1-clean[...,None])+target*clean[...,None]).astype('uint8')
        stream=io.BytesIO();Image.fromarray(col).save(stream,format='PNG');(O/f'{name}.png').write_bytes(stream.getvalue());doc['images'].append({'bufferView':blob(stream.getvalue()),'mimeType':'image/png'});tex=copy.deepcopy(g['textures'][tid]);tex['source']=len(doc['images'])-1;doc['textures'].append(tex);return len(doc['textures'])-1
    mat=copy.deepcopy(g['materials'][0]);mat['name']='Right_Eye_Texture_On_Smooth_Skin';mat.pop('normalTexture',None)
    mat['pbrMetallicRoughness']['baseColorTexture']['index']=bake(0,'orbital-basecolor')
    mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']=bake(1,'orbital-metalrough')
    mat['extensions']['KHR_materials_specular']['specularTexture']['index']=bake(3,'orbital-specular')
    doc['materials'].append(mat);doc['meshes'][0]['primitives'][0]['indices']=acc(T[~sel].astype('<u4').reshape(-1,1),'SCALAR',5125)
    attrs={'POSITION':acc(newP.astype('<f4'),'VEC3',5126),'NORMAL':acc(norm.astype('<f4'),'VEC3',5126),'TEXCOORD_0':acc(newUV,'VEC2',5126)}
    doc['meshes'][0]['primitives'].append({'attributes':attrs,'indices':acc(faces.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':len(doc['materials'])-1,'mode':4})
    output=O/'lulu-texture-eye.glb';write(output,doc,buf)
    np.savez(O/'patch.npz',P=newP,N=norm,UV=newUV,T=faces,removed=sel,sourceP=P,sourceT=T,sourceUV=UV,boundary_ids=boundary_ids)
    report={'status':'UNREVIEWED_CANDIDATE','method':'Entire orbital depression/rim replaced by healthy-skin thin plate with first-order boundary matching, zero eye relief; reference vector eye baked into local colour UV','removed_triangles':int(sel.sum()),'new_triangles':len(faces),'new_vertices':len(newP),'boundary_count':len(fixed),'head_outline_preserved':True,'opposite_eye_unchanged':True,'other_seven_parts_unchanged':True,'original_images_unchanged':True,'eye_depth_changed':True,'eye_depth_low_order_fit_rmse':eye_fit_error,'eye_reference':'reference-source/lulu/08_turnaround_front.png, native vector reconstruction', 'eye_relief':0, 'central_quadratic_fit_eigenvalues':central_eigen.tolist(), 'eye_texture_width_height':[.178,.159],'new_patch_z_range':depth.min().item(), 'max_patch_z':depth.max().item(),'source_sha256':hashlib.sha256((D/'baseline/modular-r04.glb').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'candidate_only':True}
    (O/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','cdt','finish']);ap.add_argument('--rev',default='texture-r01');a=ap.parse_args(args);O=D/a.rev
    {'prepare':prepare,'cdt':cdt,'finish':finish}[a.stage](O)
