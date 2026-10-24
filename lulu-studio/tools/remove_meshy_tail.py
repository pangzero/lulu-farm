"""Remove the attached Meshy tail and reconstruct a closed, textured shorts back.

The accepted natural-6 asset is immutable. Only a small rear patch is replaced;
all retained original vertex positions/UVs and the original images are copied.
"""
from pathlib import Path
import io,json,struct,hashlib
import numpy as np
from PIL import Image
from refine_meshy_eye_natural import R,read_glb,accessor,smoothstep

SOURCE=R/'review/meshy-no-tail-baseline/lulu-meshy-natural.glb'

def cross2(a,b):return a[0]*b[1]-a[1]*b[0]

def triangulate_polygon(xy):
    """Ear clip a single simple clockwise boundary, retaining every edge."""
    active=list(range(len(xy)));out=[]
    while len(active)>3:
        found=False
        for k,b in enumerate(active):
            a=active[k-1];c=active[(k+1)%len(active)]
            if cross2(xy[b]-xy[a],xy[c]-xy[b])>=-1e-12:continue
            blocked=False
            for j in active:
                if j in (a,b,c):continue
                p=xy[j]
                if all(cross2(xy[v]-xy[u],p-xy[u])<=1e-12 for u,v in [(a,b),(b,c),(c,a)]):
                    blocked=True;break
            if blocked:continue
            out.append([a,b,c]);active.pop(k);found=True;break
        assert found,'Cannot triangulate rear boundary without losing an edge'
    out.append(active);return np.array(out,dtype=int)

def main():
    data,g,raw=read_glb(SOURCE);prim=g['meshes'][0]['primitives'][0]
    p0=accessor(g,raw,prim['attributes']['POSITION']).copy()
    n0=accessor(g,raw,prim['attributes']['NORMAL']).copy()
    uv0=accessor(g,raw,prim['attributes']['TEXCOORD_0']).copy()
    tri0=accessor(g,raw,prim['indices']).reshape(-1,3).copy()
    def read_image(i):
        v=g['bufferViews'][g['images'][i]['bufferView']]
        return np.array(Image.open(io.BytesIO(raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'))
    color=read_image(0);mr=read_image(1);h,w=color.shape[:2]
    tex_u=(uv0[:,0]*(w-1)).astype(int).clip(0,w-1);tex_v=(uv0[:,1]*(h-1)).astype(int).clip(0,h-1)
    colors=color[tex_v,tex_u].astype(float)
    _,first,inverse=np.unique(np.round(p0,6),axis=0,return_index=True,return_inverse=True)
    U=p0[first];ut=inverse[tri0];cent=U[ut].mean(1)
    remove=((cent[:,0]/.09)**2+((cent[:,1]+.53)/.10)**2<1)&(cent[:,2]<-.40)
    removed=ut[remove]
    e=np.sort(np.concatenate([removed[:,[0,1]],removed[:,[1,2]],removed[:,[2,0]]]),1)
    e,count=np.unique(e,axis=0,return_counts=True);rim_edges=e[count==1]
    rim_ids,degree=np.unique(rim_edges,return_counts=True);assert np.all(degree==2)
    adjacent={int(i):[] for i in rim_ids}
    for a,b in rim_edges:adjacent[int(a)].append(int(b));adjacent[int(b)].append(int(a))
    start=int(rim_ids[0]);loop=[start];prev=-1;cur=start
    while True:
        nxt=next(i for i in adjacent[cur] if i!=prev)
        if nxt==start:break
        loop.append(nxt);prev,cur=cur,nxt
    assert len(loop)==len(rim_ids),'Rear replacement must have exactly one boundary'
    boundary=U[loop].copy()
    signed=sum(cross2(a[:2],b[:2]) for a,b in zip(boundary,np.roll(boundary,-1,axis=0)))
    if signed>0:loop=loop[::-1];boundary=U[loop].copy()
    patch_faces=triangulate_polygon(boundary[:,:2])
    x,y,z=p0.T;Q=(x/.09)**2+((y+.53)/.10)**2
    healthy=(abs(x)<.19)&(y>-.69)&(y<-.38)&(z<-.37)&(Q>1.12)&(Q<5)
    def design(x,y):
        X=x/.15;Y=(y+.53)/.13
        return np.stack([np.ones_like(X),X,Y,X*X,X*Y,Y*Y],axis=-1)
    A=design(x,y)
    fit=np.linalg.lstsq(A[healthy],z[healthy],rcond=None)[0]
    for _ in range(3):
        err=A[healthy]@fit-z[healthy];rw=1/np.maximum(1,abs(err)/.004)
        fit=np.linalg.lstsq(A[healthy]*rw[:,None],z[healthy]*rw,rcond=None)[0]
    rim_error=boundary[:,2]-design(boundary[:,0],boundary[:,1])@fit
    # A thin-plate interpolant spreads border corrections smoothly over the
    # whole cap; inverse-distance weights produced small radial creases.
    rim_xy=boundary[:,:2]/.1
    def kernel(a,b):
        r2=np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)
        return .5*r2*np.log(np.maximum(r2,1e-20))
    polynomial=np.c_[np.ones(len(rim_xy)),rim_xy]
    matrix=np.block([[kernel(rim_xy,rim_xy),polynomial],[polynomial.T,np.zeros((3,3))]])
    coefficients=np.linalg.solve(matrix,np.r_[rim_error,np.zeros(3)])
    def height(xy):
        q=np.asarray(xy)/.1
        return float(design(np.array(xy[0]),np.array(xy[1]))@fit+kernel(q[None,:],rim_xy)[0]@coefficients[:-3]+np.r_[1,q]@coefficients[-3:])
    patch=list(boundary.copy())
    # Refine internal edges only; keep the original irregular border watertight.
    for _ in range(2):
        edges=np.sort(np.concatenate([patch_faces[:,[0,1]],patch_faces[:,[1,2]],patch_faces[:,[2,0]]]),1)
        edges,counts=np.unique(edges,axis=0,return_counts=True);midpoints={}
        for a,b in edges[counts==2]:
            xy=(np.array(patch[a][:2])+np.array(patch[b][:2]))/2
            midpoints[(int(a),int(b))]=len(patch);patch.append(np.array([*xy,height(xy)]))
        refined=[]
        for triangle in patch_faces:
            polygon=[]
            for a,b in zip(triangle,np.roll(triangle,-1)):
                polygon.append(int(a));key=tuple(sorted((int(a),int(b))))
                if key in midpoints:polygon.append(midpoints[key])
            xy=np.mean([patch[i][:2] for i in triangle],axis=0)
            center=len(patch);patch.append(np.array([*xy,height(xy)]))
            for a,b in zip(polygon,polygon[1:]+polygon[:1]):refined.append([center,a,b])
        patch_faces=np.array(refined,dtype=int)
    patch=np.array(patch,dtype=np.float32)
    # Bake a local UV chart from the surrounding original body/shorts colors.
    # The source textures remain byte-for-byte intact; the new chart is only
    # assigned to the newly reconstructed rear surface.
    yellow=(colors[:,0]>220)&(colors[:,1]>155)
    color_fits=[]
    for group in [~yellow,yellow]:
        sel=healthy&group
        coef=np.linalg.lstsq(A[sel],colors[sel],rcond=None)[0]
        for _ in range(3):
            error=np.linalg.norm(A[sel]@coef-colors[sel],axis=1)
            rw=1/np.maximum(1,error/7)
            coef=np.linalg.lstsq(A[sel]*rw[:,None],colors[sel]*rw[:,None],rcond=None)[0]
        color_fits.append(coef)
    # Interpolate the existing waist seam through the removed tail root.
    all_edges=np.sort(np.concatenate([tri0[:,[0,1]],tri0[:,[1,2]],tri0[:,[2,0]]]),1)
    all_edges=np.unique(all_edges,axis=0);a,b=all_edges.T
    seam=(yellow[a]!=yellow[b])&(abs(x[a])>.065)&(abs(x[a])<.17)&(y[a]>-.49)&(y[a]<-.43)&(z[a]<-.40)&(z[b]<-.40)
    a,b=a[seam],b[seam]
    f=np.clip((160-colors[a,1])/(colors[b,1]-colors[a,1]),0,1)
    points=p0[a]+(p0[b]-p0[a])*f[:,None]
    waist=np.linalg.lstsq(np.c_[np.ones(len(points)),points[:,0]],points[:,1],rcond=None)[0]
    def paint(xy):
        a=design(xy[...,0],xy[...,1]);cloth=a@color_fits[0];skin=a@color_fits[1]
        blend=smoothstep((xy[...,1]-(waist[0]+waist[1]*xy[...,0])+.0009)/.0018)
        return cloth*(1-blend[...,None])+skin*blend[...,None]
    minimum=patch[:,:2].min(0)-.002;maximum=patch[:,:2].max(0)+.002
    resolution=256
    gx=np.linspace(minimum[0],maximum[0],resolution);gy=np.linspace(maximum[1],minimum[1],resolution)
    xx,yy=np.meshgrid(gx,gy);xy=np.stack([xx,yy],axis=-1)
    pixels=paint(xy)
    rim_colors=colors[first[np.array(loop)]]
    residual=rim_colors-paint(boundary[:,:2])
    dist=np.sum((xy.reshape(-1,1,2)-boundary[None,:,:2])**2,axis=2)
    weights=1/np.maximum(dist,1e-10)**2
    correction=weights@residual/weights.sum(1)[:,None]
    fade=np.exp(-dist.min(1)/(.009**2))
    pixels+=correction.reshape(resolution,resolution,3)*fade.reshape(resolution,resolution,1)
    pixels=np.clip(np.round(pixels),0,255).astype(np.uint8)
    stream=io.BytesIO();Image.fromarray(pixels).save(stream,format='PNG');patch_image=stream.getvalue()
    patch_uv=np.stack([(patch[:,0]-minimum[0])/(maximum[0]-minimum[0]),(maximum[1]-patch[:,1])/(maximum[1]-minimum[1])],axis=1).astype(np.float32)
    kept_faces=tri0[~remove];retained=np.unique(kept_faces)
    mapping=np.full(len(p0),-1,dtype=int);mapping[retained]=np.arange(len(retained))
    positions=np.concatenate([p0[retained],patch]);uv=np.concatenate([uv0[retained],patch_uv])
    body_faces=mapping[kept_faces];patch_faces=patch_faces+len(retained)
    triangles=np.concatenate([body_faces,patch_faces])
    # Recompute normals at the seam and new patch, leaving other normals exact.
    _,weld=np.unique(np.round(positions,6),axis=0,return_inverse=True)
    face=np.cross(positions[triangles[:,1]]-positions[triangles[:,0]],positions[triangles[:,2]]-positions[triangles[:,0]])
    sums=np.zeros((weld.max()+1,3))
    for k in range(3):np.add.at(sums,weld[triangles[:,k]],face)
    sums/=np.maximum(np.linalg.norm(sums,axis=1),1e-12)[:,None]
    normals=np.concatenate([n0[retained],sums[weld[len(retained):]]]).astype(np.float32)
    border_weld=np.unique(weld[len(retained):len(retained)+len(boundary)])
    border=np.isin(weld[:len(retained)],border_weld)
    normals[:len(retained)][border]=sums[weld[:len(retained)][border]]
    # Smooth graph normals avoid weighting artifacts from irregular cap fans.
    def graph_normal(xy):
        e=.00005
        dx=(height(xy+[e,0])-height(xy-[e,0]))/(2*e)
        dy=(height(xy+[0,e])-height(xy-[0,e]))/(2*e)
        v=np.array([dx,dy,-1.]);return v/np.linalg.norm(v)
    for i in np.r_[np.flatnonzero(border),np.arange(len(retained),len(positions))]:
        normals[i]=graph_normal(positions[i,:2])
    binary=bytearray(raw)
    def append_blob(blob,target=None):
        while len(binary)%4:binary.append(0)
        offset=len(binary);binary.extend(blob)
        view={'buffer':0,'byteOffset':offset,'byteLength':len(blob)}
        if target is not None:view['target']=target
        g['bufferViews'].append(view);return len(g['bufferViews'])-1
    def append_array(array,kind,component,target):
        array=np.asarray(array,dtype='<f4' if component==5126 else '<u4')
        view=append_blob(array.tobytes(),target)
        item={'bufferView':view,'componentType':component,'count':len(array),'type':kind}
        if kind=='VEC3' and array is not normals:item.update(min=array.min(0).tolist(),max=array.max(0).tolist())
        g['accessors'].append(item);return len(g['accessors'])-1
    position_id=append_array(positions,'VEC3',5126,34962)
    normal_id=append_array(normals,'VEC3',5126,34962)
    uv_id=append_array(uv,'VEC2',5126,34962)
    body_id=append_array(body_faces.reshape(-1),'SCALAR',5125,34963)
    patch_id=append_array(patch_faces.reshape(-1),'SCALAR',5125,34963)
    image_view=append_blob(patch_image);g['images'].append({'bufferView':image_view,'mimeType':'image/png'})
    g['textures'].append({'source':len(g['images'])-1,'sampler':g['textures'][0].get('sampler',0)})
    roughness=float(np.median(mr[tex_v[healthy&~yellow],tex_u[healthy&~yellow],1]))/255
    g['materials'].append({'name':'Lulu_Shorts_BackRepair','doubleSided':True,'alphaMode':'OPAQUE','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':len(g['textures'])-1,'texCoord':0},'metallicFactor':0,'roughnessFactor':roughness}})
    attributes={'POSITION':position_id,'NORMAL':normal_id,'TEXCOORD_0':uv_id}
    g['meshes'][0]['primitives']=[{'attributes':attributes,'indices':body_id,'mode':4,'material':0},{'attributes':attributes,'indices':patch_id,'mode':4,'material':len(g['materials'])-1}]
    g['buffers'][0]['byteLength']=len(binary)
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
    result=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    (R/'public/models/lulu-meshy-notail.glb').write_bytes(result)
    np.savez(R/'review/meshy-no-tail-map.npz',retained=retained,border=border,removed_faces=remove,patch_positions=patch,patch_triangles=patch_faces-len(retained))
    report={'baseline_sha256':hashlib.sha256(data).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'removed_triangles':int(remove.sum()),'new_patch_triangles':int(len(patch_faces)),'boundary_vertices':len(boundary),'retained_original_vertices':len(retained),'new_patch_vertices':len(patch),'patch_bounds':[patch.min(0).tolist(),patch.max(0).tolist()],'height_fit':fit.tolist(),'waist_fit':waist.tolist(),'patch_roughness':roughness,'eye_edit':False}
    (R/'review/meshy-no-tail-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
