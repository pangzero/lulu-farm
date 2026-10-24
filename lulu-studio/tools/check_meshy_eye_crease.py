import json,hashlib
import numpy as np
from refine_meshy_eye_natural import R,read_glb,accessor
base=R/'review/meshy-eye-crease-baseline/lulu-meshy-notail.glb'
d0,g0,b0=read_glb(base);d,g,b=read_glb(R/'public/models/lulu-meshy-crease.glb');pr=g['meshes'][0]['primitives'][0]
p0=accessor(g0,b0,pr['attributes']['POSITION']);p=accessor(g,b,pr['attributes']['POSITION']);n0=accessor(g0,b0,pr['attributes']['NORMAL']);n=accessor(g,b,pr['attributes']['NORMAL'])
m=np.load(R/'review/meshy-eye-crease-delta.npz');scope=m['weight']>0;pin=m['pin']
t=np.concatenate([accessor(g,b,q['indices']).reshape(-1,3) for q in g['meshes'][0]['primitives']]);f0=np.cross(p0[t[:,1]]-p0[t[:,0]],p0[t[:,2]]-p0[t[:,0]]);f=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]);a0=np.linalg.norm(f0,axis=1);a=np.linalg.norm(f,axis=1);valid=a0>1e-12
cos=np.sum(f*f0,axis=1)/np.maximum(a*a0,1e-24)
def image(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
r={'source_sha256':hashlib.sha256(d0).hexdigest(),'output_sha256':hashlib.sha256(d).hexdigest(),'finite':bool(np.isfinite(p).all() and np.isfinite(n).all()),'all_XY_exact':bool(np.array_equal(p[:,:2],p0[:,:2])),'outside_scope_positions_exact':bool(np.array_equal(p[~scope],p0[~scope])),'outside_scope_normals_exact':bool(np.array_equal(n[~scope],n0[~scope])),'blue_black_eye_and_core_positions_exact':bool(np.array_equal(p[pin],p0[pin])),'blue_black_eye_and_core_normals_exact':bool(np.array_equal(n[pin],n0[pin])),'all_UV_exact':bool(np.array_equal(accessor(g,b,pr['attributes']['TEXCOORD_0']),accessor(g0,b0,pr['attributes']['TEXCOORD_0']))),'all_indices_exact':all(np.array_equal(accessor(g,b,q['indices']),accessor(g0,b0,q['indices'])) for q in g['meshes'][0]['primitives']),'all_images_exact':all(image(g,b,i)==image(g0,b0,i) for i in range(len(g['images']))),'all_materials_exact':g['materials']==g0['materials'],'nodes_exact':g['nodes']==g0['nodes'],'primitives_exact':g['meshes']==g0['meshes'],'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),'new_degenerate_triangles':int(((a<1e-12)&valid).sum()),'reversed_faces_over90deg':int(((cos<0)&valid).sum()),'minimum_face_area_ratio':float((a[valid]/a0[valid]).min()),'max_axis_delta':np.abs(p-p0).max(0).tolist(),'changed_vertices':int(np.any(p!=p0,axis=1).sum())}
r['passed']=all(v for v in r.values() if isinstance(v,bool)) and r['new_degenerate_triangles']==0 and r['reversed_faces_over90deg']==0 and r['minimum_face_area_ratio']>.35
(R/'review/meshy-eye-crease-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
